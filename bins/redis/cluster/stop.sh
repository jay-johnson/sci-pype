#!/bin/bash

if [[ -e ./redis/docker/common-bash.sh ]]; then
    source ./redis/docker/common-bash.sh .
fi

filetouse="./single-host-compose.yml"

echo ""
amnt "Stopping Docker Composition"
docker-compose -f $filetouse down
docker stop $imagename &>> /dev/null
docker rm $imagename &>> /dev/null
echo ""

exit 0
