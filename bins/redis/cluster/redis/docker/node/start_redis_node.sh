#!/bin/sh

source /opt/tools/bash-common.sh .

log="/tmp/redis-single-node.log"
firsttimefile="/tmp/firsttimerunning"

curcluster=$ENV_CLUSTERED
configdir="$ENV_CONFIGURABLES_DIR"
etcdir="$ENV_ETC_DIR"
redisport=$ENV_REDIS_PORT
curhost=$ENV_MASTER_REDIS_HOST
curport=$ENV_MASTER_REDIS_PORT

curnodename="$ENV_NODE_TYPE"
allnodes="$ENV_NODE_REPLICAS"

echo "" > $log

if [ -e $firsttimefile ]; then
    lg " - First Time Running($curnodename)"
    chmod 777 ${configdir}/assign_env_configuration.sh >> $log
    ${configdir}/assign_env_configuration.sh >> $log
    rm -rf $firsttimefile >> $log
    lg " - Done First Time Running($curnodename)"
fi

lg "Initializing Redis Node($curnodename)"

if [ "$curnodename" == "master" ]; then
    nohup redis-server ${configdir}/redis.conf &> /tmp/redis-${curnodename}.log &
    nohup redis-server ${configdir}/sentinel.conf --sentinel &> /tmp/sentinel-${curnodename}.log &
elif [ "$curnodename" == "node2" ]; then
    echo "slaveof redisnode1 ${redisport}" >> ${configdir}/redis.conf
    nohup redis-server ${configdir}/redis.conf &> /tmp/redis-${curnodename}.log &
    nohup redis-server ${configdir}/sentinel.conf --sentinel &> /tmp/sentinel-${curnodename}.log &
elif [ "$curnodename" == "node3" ]; then
    echo "slaveof redisnode1 ${redisport}" >> ${configdir}/redis.conf
    nohup redis-server ${configdir}/redis.conf &> /tmp/redis-${curnodename}.log &
    nohup redis-server ${configdir}/sentinel.conf --sentinel &> /tmp/sentinel-${curnodename}.log &
elif [ "$curnodename" == "node3" ]; then
    echo "slaveof redisnode1 ${redisport}" >> ${configdir}/redis.conf
    nohup redis-server ${configdir}/redis.conf &> /tmp/redis-${curnodename}.log &
    nohup redis-server ${configdir}/sentinel.conf --sentinel &> /tmp/sentinel-${curnodename}.log &
else
    echo "slaveof redisnode1 ${redisport}" >> ${configdir}/redis.conf
    nohup redis-server ${configdir}/redis.conf &> /tmp/redis-${curnodename}.log &
    nohup redis-server ${configdir}/sentinel.conf --sentinel &> /tmp/sentinel-${curnodename}.log &
fi

touch /tmp/redis-cluster.log
lg "Starting Single Redis ($curnodename:$redisport)"

lg "Done Starting Redis Node($curnodename)"
tail -f /tmp/redis-cluster.log
lg "Start Script Stopping"

exit 0
