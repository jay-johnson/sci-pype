#!/bin/bash

log="/tmp/pre-start.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Running Pre-Start" > $log

echo "$(date +'%m-%d-%y %H:%M:%S') Done Pre-Start" >> $log

exit 0
