#!/bin/bash

if [[ -e ./common-bash.sh ]]; then
    source ./common-bash.sh .
else
    if [[ -e /opt/scipype/src/common/common-bash.sh ]]; then
        source /opt/scipype/src/common/common-bash.sh .
    fi
fi

filetouse="./single-secure-redis.yml"

if [[ ! -e $filetouse ]]; then
    echo ""
    err "Unable to find compose file: $filetouse" 
    echo ""
    exit 1
fi

echo ""
amnt "Starting new Docker Composition($filetouse)"
docker-compose -f $filetouse up -d
echo ""

exit 0
