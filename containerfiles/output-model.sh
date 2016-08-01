#!/bin/bash

action="OUTPUT-MODEL"
log="/tmp/output-model.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Starting($action)" > $log
echo "$(date +'%m-%d-%y %H:%M:%S') Done($action)" >> $log

exit 0
