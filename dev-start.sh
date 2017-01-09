#!/bin/bash

filetouse="dev-jupyter-docker-compose.yml"

source ./properties.sh .

echo "Starting Composition: $filetouse"
docker-compose -f $filetouse up -d
echo "Done"

exit 0
