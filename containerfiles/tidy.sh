#!/bin/bash

action="TIDY"
log="/tmp/tidy.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Starting($action)" > $log
echo "$(date +'%m-%d-%y %H:%M:%S') Done($action)" >> $log

exit 0
