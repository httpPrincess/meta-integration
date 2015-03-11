FROM ubuntu:14.04
MAINTAINER jj
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install python python-pip python-novaclient -y && \
   apt-get clean autoclean && apt-get autoremove && \
   rm -rf /var/lib/{apt,dpkg,cache,log} && mkdir /app/
ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt
ADD . /app/
EXPOSE 7000
WORKDIR /app/
CMD cd /app/ && ./run.py
