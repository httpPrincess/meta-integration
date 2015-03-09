#!/bin/bash

# cleanup
echo 'Killing instances'
for i in `docker ps --all | awk '{print $1}'` ; do docker kill $i; docker rm $i; done

echo 'Removing images'
for i in `docker images | awk '{print $3}' |` ; do docker rmi $i; done

