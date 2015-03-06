#!/bin/bash

# setup
DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y docker.io git python-virtualenv libyaml-dev
TEST_DIR=/testdir/
mkdir $TEST_DIR
cd $TEST_DIR
virtualenv env
source env/bin/activate
pip install -U git+https://github.com/httpPrincess/compose.git

# make facade image
git clone https://github.com/httpPrincess/metahosting.git
cd metahosting
docker build --rm=true --no-cache=true -t facade . >> /tmp/log.txt

# get worker
cd $TEST_DIR
git clone https://github.com/BeneDicere/metahosting-worker.git
cd metahosting-worker
# we mix all in one environment
pip install -r requirements.txt

# integration starts
cd $TEST_DIR
git clone https://github.com/httpPrincess/meta-integration.git
cd meta-integration
export COMPOSE_CLIENT_VERSION=1.12
docker-compose pull
docker-compose start messaging db autho messaging updater
docker-compose ps >> /tmp/log.txt
