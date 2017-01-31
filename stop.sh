#!/bin/bash

source ./properties.sh .

echo "Stopping Docker image($registry/$maintainer/$imagename)"
docker stop $imagename &>> /dev/null
docker rm $imagename &>> /dev/null

exit 0
