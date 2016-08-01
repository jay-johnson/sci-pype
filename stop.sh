#!/bin/bash

source ./properties.sh .

echo "Stopping Docker image($registry/$maintainer/$imagename)"
docker stop $imagename
docker rm $imagename

exit 0
