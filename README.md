# vip-reproducibility-conversion-images


This repository contains Dockerfiles and scripts necessary to build images for converting the results of medical imaging application experiments through a plugin for the Girder storage platform.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Docker installed on your machine.

## Building the Image

To build all the images, follow these steps:

1. Clone this repository to your local machine:
```
git clone https://github.com/your-username/medical-imaging-conversion.git
```

2. Navigate to the repository directory:
```
cd vip-reproducibility-conversion-images
```

3. Build the images using the provided script:
```
./build.sh
```

## Usage

Once the images are built, you can use them to convert the results of medical imaging application experiments through the Girder conversion plugin ([vip-reproducibility-girder-plugin](https://github.com/virtual-imaging-platform/vip-reproducibility-girder-plugin))