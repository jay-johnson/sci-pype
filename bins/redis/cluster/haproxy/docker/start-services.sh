#!/bin/bash

source /opt/tools/bash-common.sh .

log="/tmp/start-services.log"
echo "" > $log

lg "Starting Sevices"

if [[ -e $ENV_START_SERVICE ]]; then
    $ENV_START_SERVICE
    last_status=$?
    if [[ "${last_status}" != "0" ]]; then
        err "Failed starting services for container: ${ENV_START_SERVICE}" >> $log
        exit 1
    else
        lg "Done starting service: ${ENV_START_SERVICE}" >> $log
    fi

    lg "Keeping Container running..." >> $log
    tail -f $log
else
    lg "Starting single haproxy node" >> $log
    /opt/haproxy/node/start_haproxy_node.sh
    last_status=$?
    if [[ "${last_status}" != "0" ]]; then
        err "Failed starting single haproxy node services for container: /opt/haproxy/node/start_haproxy_node.sh" >> $log
        exit 1
    else
        lg "Done starting service: /opt/haproxy/node/start_haproxy_node.sh" >> $log
    fi

    lg "Keeping Container running..." >> $log
    tail -f $log
fi

lg "Done Starting Services"

exit 0
