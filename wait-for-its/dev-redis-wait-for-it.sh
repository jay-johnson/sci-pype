#!/usr/bin/env bash

echo "$(date +'%m-%d-%y %H:%M:%S') Starting container" >> /tmp/waitforit.log
. /bin/start_single_node_with_supervisor.sh

echo "$(date +'%m-%d-%y %H:%M:%S') Container started" >> /tmp/waitforit.log

exit 0
