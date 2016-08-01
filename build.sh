#!/bin/bash

source ./properties.sh .

echo "Building new Docker image($maintainer/$imagename)"
docker build --rm -t $maintainer/$imagename .

exit 0
