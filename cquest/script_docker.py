import json
import os
import sys
import uuid
import tarfile

import pandas as pd



def get_quest2(quest2_path, verbose=False) -> tuple[pd.DataFrame, str]:
    """ A home-made function to import data from CQuest result files : *_quest2.txt"""
    
    class __LineInfo():
        """A finite state machine to control each step while reading the result file"""

        def __init__(self):
            self.state = "Newline"
            self.index = 0

        def refresh(self, input) -> None:
            """input = first element of a new line (sep='\t') in the result file""" 
            self.index += 1
            if not input: # Current line is empty
                # Case : Expected New line --> Nothing to do
                if self.state in ["Newline", "Record", "Warning"] : 
                    self.state = "Newline"
                # Case : End of metabolite block --> Record metabolite data
                elif self.state == "Values" : 
                    self.state = "Record" 
                # Case : Unexpected New Line --> Error State
                else:
                    self.state = "Error"
            # Case : Metabolite name
            elif input == 'Metabolite:' and self.state == "Newline" : 
                self.state = "Metabolite"
            # Case : Parameter names
            elif input.split()[0].isalpha() and self.state == "Metabolite" : 
                self.state = "Parameters" 
            # Case : Parameter values
            elif input.isnumeric() and self.state == "Parameters" : 
                self.state = "Values" 
            # Case : Warning message (seen on several files)
            elif input.split()[0] == 'WARNING!' and self.state == "Newline" : 
                self.state = "Warning"
            # Case : Unexpected 1st word --> Error state
            else:
                self.state = "Error"
    # End of the finite state machine

    # Main program 
    # Create an empty data frame 
    data = pd.DataFrame()
    # Read the result file
    with open(quest2_path, 'r') as f:
        # Initiate the finite state machine to control each line of the result file
        line_info = __LineInfo()
        # Read each line
        for line in f:
            # Split the line and read 1st word
            words = line[:-1].split('\t')
            # Update the line state according to the 1st word
            line_info.refresh(words[0])
            # Case : Metabolite name
            if line_info.state == 'Metabolite': 
                # Create new frame for this metabolite
                frame = {
                    "Metabolite": words[1].split("_")[0] # Short name
                }
                params = []
                values = []
            # Case : Parameter names
            elif line_info.state == "Parameters":
                # List of parameters, excluding "Pixel Position"
                params = [ '_'.join(param_str.split(' ')) for param_str in words[1:] if param_str ]
            # Case : Parameter values
            elif line_info.state == "Values":
                # List of parameter values, excluding Pixel & Position
                values = [ val_str for val_str in words[2:] if val_str ]
            # Case : Record parameter values after metabolite block
            elif line_info.state == "Record":
                # Update the frame
                frame.update( dict(zip(params, values)) )
                # Add line_info frame to the data
                data = pd.concat([ data, pd.DataFrame([frame]) ], ignore_index=True )
            # Case : Error state
            elif line_info.state == 'Error': 
                raise Exception( "Error while importing Quest results !\n\
                    File: {}\n\t In line N°{}: '{}'.\n\
                    Check data format.".format(quest2_path, line_info.index, line[:-1]) )
            else: # Case : New line 
                # Nothing to to
                pass
    # Return
    return data

def extract_tgz(tgz_file, destination_dir):
    with tarfile.open(tgz_file, 'r:gz') as tar:
        tar.extractall(path=destination_dir)

def aggregate_workflow_without_folder_logic(path, output_path, wf_id):
    print('Aggregating workflow')
    # get quest2 while adding a column named 'Iteration' with the iteration number
    i = 0
    data_list = []
    items = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    # put the file contained in each item in a list
    files = []
    for item in items:
        files += [path + '/' + item + '/' + f for f in os.listdir(path + '/' + item) if f.endswith('tgz')]
    print(files)
    for f in files:
        # untgz the file in the folder
        # extract_path is file path
        extract_tgz(f, f[:-4])
        # keep the file ending with _quest2.txt in f[:-4]
        quest2_f = [f for f in os.listdir(f[:-4]) if f.endswith('_quest2.txt')][0]
        df = get_quest2(f[:-4] + '/' + quest2_f)
        df['Signal'] = quest2_f
        data_list.append(df)
        i += 1
        
    # concatenate all the dataframes
    if len(data_list) > 0:
        data = pd.concat(data_list, ignore_index=True)
        id = str(uuid.uuid4())
        path = output_path + id
        data['Workflow'] = wf_id
        # save the buffer into the path in local storage
        data.to_feather(path)
        print('Workflow aggregation done')
        return id


def aggregate_experiment_without_folder_logic(files_list, output_path):
    # files list is a list of paths to feather files
    print('Aggregating experiment')
    # aggregate all the feather files into a single dataframe
    data_list = []
    for f in files_list:
        data_list.append(pd.read_feather(output_path + f))
    # concatenate all the dataframes
    data = pd.concat(data_list, ignore_index=True)
    id = str(uuid.uuid4())
    path = output_path + id
    # save the buffer into the path in local storage
    data.to_feather(path)
    print("File saved at " + path)
    print('Experiment aggregation done')
    return id


def process_hierarchy(path):
    # get the only folder inside the path
    exp_name = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))][0]
    out_json = {}
    out_json[exp_name] = {}
    files_list = []
    
    for workflow in os.listdir(path + '/' + exp_name):
        # Get the workflow id
        print(path + exp_name + '/' + workflow)
        result_path = aggregate_workflow_without_folder_logic(path + exp_name + '/' + workflow, path, workflow)
        if result_path:
            out_json[exp_name][workflow] = {}
            out_json[exp_name][workflow]["data.feather"] = result_path
            files_list.append(result_path)
    
    # aggregate the experiment
    out_path = aggregate_experiment_without_folder_logic(files_list, path)
    out_json[exp_name]["data.feather"] = out_path

    # save the json file
    with open(path + exp_name + '_processed.json', 'w') as f:
        json.dump(out_json, f)
    


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("This program takes one argument as input (path to the data)")
        exit()
    path = "/vol/" + sys.argv[1]
    process_hierarchy(path)