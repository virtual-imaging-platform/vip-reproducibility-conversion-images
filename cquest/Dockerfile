FROM python:3.9

RUN pip install pandas pyarrow

COPY ./script_docker.py /script.py

VOLUME ["vol"]

ENTRYPOINT ["python", "script.py"]