#!/bin/bash

if [[ -e ./redis/docker/common-bash.sh ]]; then
    source ./redis/docker/common-bash.sh .
fi

filetouse="./single-host-compose.yml"

echo ""
amnt "Starting new Docker Composition($filetouse)"
docker-compose -f $filetouse up -d
echo ""

exit 0
