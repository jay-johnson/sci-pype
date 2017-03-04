#!/bin/bash

if [[ -e ./common-bash.sh ]]; then
    source ./common-bash.sh .
else
    if [[ -e /opt/work/src/common/common-bash.sh ]]; then
        source /opt/work/src/common/common-bash.sh .
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
amnt "Stopping Docker Composition"
docker-compose -f $filetouse down
docker stop $(cat $filetouse | grep container | sed -e 's/"//g' | awk '{print $NF}') &>> /dev/null
docker rm $(cat $filetouse | grep container | sed -e 's/"//g' | awk '{print $NF}') &>> /dev/null
echo ""

exit 0
