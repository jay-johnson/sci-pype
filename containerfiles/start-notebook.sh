#!/bin/bash

log="/tmp/startnotebook.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Starting Notebook" > $log

# Handle special flags if we're root
if [ $UID == 0 ] ; then
    # Change UID of NB_USER to NB_UID if it does not match
    if [ "$NB_UID" != $(id -u $NB_USER) ] ; then
        usermod -u $NB_UID $NB_USER
        chown -R $NB_UID $CONDA_DIR .
    fi

    # Enable sudo if requested
    if [ ! -z "$GRANT_SUDO" ]; then
        echo "$NB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/notebook
    fi

    echo "$(date +'%m-%d-%y %H:%M:%S') exec su $NB_USER -c \"env PATH=$PATH jupyter notebook $*\"" >> $log

    # Start the notebook server
    exec su $NB_USER -c "env PATH=$PATH jupyter notebook $*" &>> $log
else
    # Otherwise just exec the notebook
    echo "$(date +'%m-%d-%y %H:%M:%S') exec jupyter notebook $*" >> $log
    exec jupyter notebook $* &>> $log
fi

echo "$(date +'%m-%d-%y %H:%M:%S') Done Starting Notebook" >> $log

tail -f $log
