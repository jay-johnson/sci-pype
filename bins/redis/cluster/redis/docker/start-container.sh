#!/bin/bash

echo "Loading common bash methods"
source /opt/tools/bash-common.sh .

log="/tmp/container.log"
echo "" > $log

lg "Starting Container"
date >> $log
lg ""

lg "Activating Virtual Env"
source /venv/bin/activate .

if [[ ! -e /opt/.keys.sh ]]; then
    err "Failed to find Keys: /opt/.keys.sh"
    echo "Failed to find Keys: /opt/.keys.sh"
    echo "Cloud Actions will not work unless this file is present"
else
    lg "Loading Keys"
    source /opt/.keys.sh .
fi

lg "Starting Services"

prestartscript="$ENV_PRESTART_SCRIPT"
startscript="$ENV_START_SCRIPT"
poststartscript="$ENV_POSTSTART_SCRIPT"
customprestartscript="$ENV_CUSTOM_SCRIPT"

if [ "$ENV_DEPLOYMENT_TYPE" != "Custom" ]; then

    if [ -e "$customprestartscript" ]; then
        lg "Starting Custom Script($customprestartscript)"
        $customprestartscript &>> $log
        lg "Done Custom Script($customprestartscript)"
    else
        lg "Custom Script does not Exist($customprestartscript)"
    fi
fi

if [ -e "$prestartscript" ]; then
    lg "Running PreStart($prestartscript)"
    $prestartscript &>> $log
    lg "Done Running PreStart($prestartscript)"
else
    lg "PreStart does not Exist($prestartscript)"
fi

if [ -e "$startscript" ]; then
    lg "Running Start($startscript)"
    $startscript &>> $log
    lg "Done Running Start($startscript)"
else
    lg "Start does not Exist($startscript)"
fi

if [ -e "$poststartscript" ]; then
    lg "Running PostStart($poststartscript)"
    $poststartscript &>> $log
    lg "Done Running PostStart($poststartscript)"
else
    lg "PostStart does not Exist($poststartscript)"
fi

lg "Done Starting Services"

lg "Preventing the container from exiting"
tail -f $log
lg "Done preventing the container from exiting"

exit 0
