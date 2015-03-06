#!/bin/bash

# setup
DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y docker.io git python-virtualenv
mkdir /testingdir/
cd /testingdir/
virtualenv env
source env/bin/activate
pip install -U git+https://github.com/httpPrincess/compose.git
git checkout 

