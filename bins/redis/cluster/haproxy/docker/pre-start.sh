#!/bin/bash

source /opt/tools/bash-common.sh .

log="/tmp/pre-start.log"
echo "" > $log

lg "Running Pre-Start"

if [ -d "$ENV_SSH_CREDS" ]; then
    lg "Installing ssh for container user from ${ENV_SSH_CREDS}" >> $log
    if [ ! -e /root/.ssh ]; then
        mkdir /root/.ssh
        chmod 700 /root/.ssh
    fi
    cp -r $ENV_SSH_CREDS/* /root/.ssh/
    chmod 600 /root/.ssh/*
    chmod 700 /root/.ssh/*.pem
    chmod 644 /root/.ssh/*.pub
    chmod 700 /root/.ssh/config
fi

if [ -e "$ENV_GIT_CONFIG" ]; then
    lg "Installing git config for container user from ${ENV_GIT_CONFIG}" >> $log
    cp $ENV_GIT_CONFIG /root/.gitconfig
    chmod 664 /root/.gitconfig
fi

# Custom commands:

if [[ "${ENV_REDIS_REQUIRE_PASSWORD}" != "" ]]; then
    lg "Setting redis password" >> $log
    sed -i "s/#SET_ENV_REDIS_REQUIRE_PASSWORD/requirepass ${ENV_REDIS_REQUIRE_PASSWORD}/g" /opt/redis/node/*.conf
    lg "Set redis password" >> $log
else
    lg "No redis password set" >> $log
fi

lg "Done Pre-Start"

exit 0
