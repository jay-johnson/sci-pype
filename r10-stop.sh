#!/bin/bash

filetouse="red10-docker-compose.yml"

echo "Stopping Composition: $filetouse"
docker-compose -f $filetouse stop
echo "Done"

docker stop jupyter &>> /dev/null
docker rm jupyter &>> /dev/null

exit 0
