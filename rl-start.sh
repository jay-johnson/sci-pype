#!/bin/bash

source ./properties.sh .

filetouse="redis-labs-compose.yml"

echo "Starting Composition: $filetouse"
docker-compose -f $filetouse up -d
echo "Done"

exit 0
