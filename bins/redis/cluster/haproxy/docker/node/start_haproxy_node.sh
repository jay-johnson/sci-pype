#!/bin/bash

source /opt/tools/bash-common.sh .

log="/tmp/start-haproxy.log"
echo "" > $log

lg "---------------------------------"
lg "Waiting for Redis to start"
sleep 5
lg "Done waiting"
lg "---------------------------------"

configdir="$ENV_CONFIGURABLES_DIR"
etcdir="$ENV_ETC_DIR"

node_supervisor_name=supv-haproxy
first_time_file="/tmp/firsttimerunning"
supervisor_config="${etcdir}/supervisor.d/containerservices.ini"

lg "" > $log
if [ -e $first_time_file ]; then
    lg " - First Time Running($CUR_NODE_NAME)"
    chmod 777 ${configdir}/assign_env_configuration.sh >> $log
    ${configdir}/assign_env_configuration.sh >> $log
    rm -rf $first_time_file >> $log
    lg " - Done First Time Running($CUR_NODE_NAME)"
fi

cp ${configdir}/logrotateservices /etc/logrotate.d/logrotateservices
chmod 644 /etc/logrotate.d/logrotateservices
cp ${configdir}/haproxy.conf /etc/haproxy.conf
chmod 777 /etc/haproxy.conf

lg "Number of Instances($ENV_NUM_INSTANCES)"
CUR_PORT=$ENV_BASE_REDIS_PORT
for i in `seq 1 $ENV_NUM_INSTANCES`;
do
    lg $i
    curname="${ENV_BASE_HOSTNAME}${i}"
    line=" server ${curname} ${curname}:${CUR_PORT} maxconn 1024 check inter 1s"
    let "CUR_PORT += 1"
    lg $line
    echo $line >> /etc/haproxy.conf
done   

lg "Initializing Supervisor Config"
sed -i "s/REPLACE_NODE_NAME/$ENV_NODE_SUPERVISOR_NAME/g" $supervisor_config
lg "Supervisor Node($ENV_NODE_SUPERVISOR_NAME)"
cat $supervisor_config | grep "program:" >> $log
lg ""
lg "Starting node" 
supervisord -c $supervisor_config >> $log
lg "Waiting for supervisor to start"
sleep 1
lg "Done waiting"

lg "Haproxy Started on Node"
tail -f $log
lg "Haproxy Done"
