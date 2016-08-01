#!/usr/bin/env bash

echo "$(date +'%m-%d-%y %H:%M:%S') Waiting for DB" > /tmp/waitforit.log
/wait-for-its/wait-for-it.sh -t 60 stocksdb:3306 &>> /tmp/waitforit.log
echo "$(date +'%m-%d-%y %H:%M:%S') Done waiting for DB" >> /tmp/waitforit.log

echo "$(date +'%m-%d-%y %H:%M:%S') Starting container" >> /tmp/waitforit.log
/opt/containerfiles/start-container.sh

echo "$(date +'%m-%d-%y %H:%M:%S') Container started" >> /tmp/waitforit.log

exit 0
