#!/bin/bash

source ./properties.sh .

envfile="./local/jupyter.env"

echo "Starting new Docker image($registry/$maintainer/${imagename}:${version})"
docker run --name=$imagename \
            --env-file $envfile \
            -v $(pwd):/opt/work \
            -p 82:8888 \
            -p 444:443 \
            --net=host \
            -d $maintainer/$imagename:$version

exit 0
