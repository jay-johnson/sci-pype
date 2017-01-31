#!/bin/bash

filetouse="redis-labs-compose.yml"

source ./properties.sh .

echo "Starting Composition: $filetouse"
docker-compose -f $filetouse up -d
echo "Done"

exit 0
