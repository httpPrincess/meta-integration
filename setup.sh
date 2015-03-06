#!/bin/bash

# setup
DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y docker.io git python-virtualenv
TEST_DIR=$TEST_DIR
mkdir $TEST_DIR
cd $TEST_DIR
virtualenv env
source env/bin/activate
pip install -U git+https://github.com/httpPrincess/compose.git

# make facade image
mkdir -p $TEST_DIRfacade
cd $TEST_DIRfacade 
git clone https://github.com/httpPrincess/metahosting.git
docker build --rm=true --no-cache=true -t facade . >> log.txt
cd ..

# get worker
mkdir -p $TEST_DIRworker
cd $TEST_DIRworker/
git clone https://github.com/BeneDicere/metahosting-worker.git
# we mix all in one environment
pip install -r requirements.txt
cd ..

# integration starts
mkdir -p $TEST_DIRintegration
cd $TEST_DIRintegration
git clone https://github.com/httpPrincess/meta-integration.git
docker-compose pull
docker-compose start messaging db autho messaging updater
docker-compose ps >> log.txt
