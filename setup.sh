#!/bin/bash

# setup
DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io git python-virtualenv python-dev
TEST_DIR=/testdir/
mkdir $TEST_DIR
cd $TEST_DIR
virtualenv env
source env/bin/activate
pip install -U git+https://github.com/httpPrincess/compose.git

# get test suite
git clone https://github.com/httpPrincess/meta-integration.git
cd meta-integration

# make facade image
cd $TEST_DIR
git clone https://github.com/httpPrincess/metahosting.git
cd metahosting
cp ../meta-integration/client.py ./client.py
docker build --rm=true --no-cache=true -t facade . >> /tmp/log.txt

# get worker
# we skip it for now since a dummy worker is provided as an image
cd $TEST_DIR
git clone https://github.com/BeneDicere/metahosting-worker.git
#cd metahosting-worker
# we mix all in one environment
#pip install -r requirements.txt

# integration starts
cd $TEST_DIR/meta-integration
export COMPOSE_CLIENT_VERSION=1.12
docker-compose pull
docker-compose up
docker-compose ps >> /tmp/log.txt
