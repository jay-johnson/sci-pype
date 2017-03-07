#!/bin/bash

source ./properties.sh .

filetouse="dev-jupyter-docker-compose.yml"

echo "Starting Composition: $filetouse"
docker-compose -f $filetouse up -d
echo "Done"

exit 0
