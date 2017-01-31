#!/bin/bash

log="/tmp/post-start.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Running Post-Start" > $log

echo "$(date +'%m-%d-%y %H:%M:%S') Done Post-Start" >> $log

exit 0
