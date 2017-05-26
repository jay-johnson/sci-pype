#!/bin/bash

source ./properties.sh .

filetouse="red10-docker-compose.yml"

echo "Starting Composition: $filetouse"
docker-compose -f $filetouse up -d
echo "Done"

exit 0
