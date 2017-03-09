#!/bin/bash

source /opt/tools/bash-common.sh .

log="/tmp/redis-cluster.log"
echo "" > $log

curcluster=$ENV_CLUSTERED
masterhost=$ENV_MASTER_REDIS_HOST
masterport=$ENV_MASTER_REDIS_PORT
configdir="$ENV_CONFIGURABLES_DIR"
etcdir="$ENV_ETC_DIR"

nodesupervisorname="supv-$ENV_NODE_TYPE"
noderedisname=$ENV_NODE_TYPE
noderedisport=$ENV_REDIS_PORT
noderedisreplicas="$ENV_NODE_REPLICAS"
cur_nodename="$ENV_NODE_TYPE"
allnodes="$ENV_NODE_REPLICAS"
service_config_to_use="$ENV_USE_THIS_REDIS_CONFIG"
target_conf_for_supervisor="${configdir}/current.conf"
cursupervisorconfig="${etcdir}/supervisor.d/containerservices.ini"

if [ "$service_config_to_use" == "" ]; then
    lg "Default Installing Single-Replicated Redis Config ${configdir}/single_replicated_redis.conf" 
    cp ${configdir}/single_replicated_redis.conf $target_conf_for_supervisor
    chmod 777 $target_conf_for_supervisor
else
    if [ -e $service_config_to_use ]; then
        lg "Using Redis Config($service_config_to_use)" 
        cp $service_config_to_use $target_conf_for_supervisor
        chmod 777 $target_conf_for_supervisor
    else
        lg "Missing Redis Config($service_config_to_use) Using Default Single-Replicated Redis Config ${configdir}/single_replicated_redis.conf" 
        cp ${configdir}/single_replicated_redis.conf $target_conf_for_supervisor
        chmod 777 $target_conf_for_supervisor
    fi
fi 

FIRST_TIME_FILE="/opt/redis/firsttimerunning"
if [ -e $FIRST_TIME_FILE ]; then
    lg " - First Time Running($cur_nodename)" 
    chmod 777 ${configdir}/assign_env_configuration.sh >> $log
    ${configdir}/assign_env_configuration.sh >> $log
    rm -rf $FIRST_TIME_FILE >> $log
    lg " - Done First Time Running($cur_nodename)" 
fi

cp ${configdir}/logrotateservices /etc/logrotate.d/logrotateservices
chmod 644 /etc/logrotate.d/logrotateservices

if [ "${curcluster}" == "1" ]; then
    lg "Installing Cluster Redis Config" 
    cp ${configdir}/cluster_redis.conf $target_conf_for_supervisor
    lg "Initializing Supervisor Config" 
    sed -i "s/REPLACE_NODE_NAME/$nodesupervisorname/g" $cursupervisorconfig
    lg "Supervisor Node($nodesupervisorname)" 
    cat $cursupervisorconfig | grep "program:" >> $log
    lg "" 
    lg "Starting node" > $log
    supervisord -c $cursupervisorconfig >> $log
    lg "Waiting for supervisor to start" 

    sleep 10
    lg "Done waiting" 
    lg "Starting Ruby Cluster Join ($noderedisname:$noderedisport) Replicas($noderedisreplicas)" 
    echo "yes" | ruby /usr/bin/redis-trib.rb create --replicas 1 $noderedisreplicas >> /tmp/redis-cluster.log 
    lg "Done joining Cluster" 
else
    # Replicas should have the slaveof command in their config
    if [ "$cur_nodename" == "node1" ]; then
        echo "slaveof $masterhost $masterport" >> $target_conf_for_supervisor
    elif [ "$cur_nodename" == "node2" ]; then
        echo "slaveof $masterhost $masterport" >> $target_conf_for_supervisor
    elif [ "$cur_nodename" == "node3" ]; then
        echo "slaveof $masterhost $masterport" >> $target_conf_for_supervisor
    fi
    lg "Done Installing Single-Replicated Redis Config" 

    lg "Initializing Supervisor Config" 
    sed -i "s/REPLACE_NODE_NAME/$nodesupervisorname/g" $cursupervisorconfig
    lg "Supervisor Node($nodesupervisorname)" 
    cat $cursupervisorconfig | grep "program:" >> $log
    lg "" 
    lg "Starting node" > $log
    supervisord -c $cursupervisorconfig >> $log
    lg "Waiting for supervisor to start" 
    sleep 2
    lg "Done waiting" 
fi

lg "Starting Sentinel" 
nohup redis-server ${configdir}/sentinel.conf --sentinel &> /tmp/sentinel-${cur_nodename}.log &
lg "Done Starting Sentinel" 

lg "Cluster Started on Node" 
tail -f /tmp/sentinel-${cur_nodename}.log
lg "Cluster Done" 

exit 0
