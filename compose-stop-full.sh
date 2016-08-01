#!/bin/bash

filetouse="full-stack-compose.yml"

echo "Stopping Composition: $filetouse"
docker-compose -f $filetouse stop
echo "Done"

exit 0
