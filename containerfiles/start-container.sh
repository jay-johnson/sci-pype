#!/bin/bash

log="/tmp/start.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Starting Container" > $log
date >> $log
echo "$(date +'%m-%d-%y %H:%M:%S') Environment Variables" >> $log
env | sort >> $log
echo "$(date +'%m-%d-%y %H:%M:%S') " >> $log

echo "$(date +'%m-%d-%y %H:%M:%S') Starting Services" >> $log

prestartscript="$ENV_PRESTART_SCRIPT"
startscript="$ENV_START_SCRIPT"
poststartscript="$ENV_POSTSTART_SCRIPT"

if [ "$ENV_DEPLOYMENT_TYPE" != "JustDB" ]; then

    # Start a redis server inside the container, the compose files scale these out
    # this is for testing purposes
    echo "$(date +'%m-%d-%y %H:%M:%S') Starting Redis Data Server" >> $log
    /opt/work/bins/local_redis_server.sh &>> $log

    echo "$(date +'%m-%d-%y %H:%M:%S') Done Starting Local Services" >> $log
fi

if [ -e "$prestartscript" ]; then
    echo "$(date +'%m-%d-%y %H:%M:%S') Running PreStart($prestartscript)" >> $log
    $prestartscript &>> $log
    echo "$(date +'%m-%d-%y %H:%M:%S') Done Running PreStart($prestartscript)" >> $log
else
    echo "$(date +'%m-%d-%y %H:%M:%S') PreStart does not Exist($prestartscript)" >> $log
fi

if [ -e "$startscript" ]; then
    echo "$(date +'%m-%d-%y %H:%M:%S') Running Start($startscript)" >> $log
    $startscript &>> $log
    echo "$(date +'%m-%d-%y %H:%M:%S') Done Running Start($startscript)" >> $log
else
    echo "$(date +'%m-%d-%y %H:%M:%S') Start does not Exist($startscript)" >> $log
fi

if [ -e "$poststartscript" ]; then
    echo "$(date +'%m-%d-%y %H:%M:%S') Running PostStart($poststartscript)" >> $log
    $poststartscript &>> $log
    echo "$(date +'%m-%d-%y %H:%M:%S') Done Running PostStart($poststartscript)" >> $log
else
    echo "$(date +'%m-%d-%y %H:%M:%S') PostStart does not Exist($poststartscript)" >> $log
fi

echo "$(date +'%m-%d-%y %H:%M:%S') Done Starting Services" >> $log

echo "$(date +'%m-%d-%y %H:%M:%S') Preventing the container from exiting" >> $log
tail -f $log
echo "$(date +'%m-%d-%y %H:%M:%S') Done preventing the container from exiting" >> $log

exit 0
