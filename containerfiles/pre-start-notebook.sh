#!/bin/bash

log="/tmp/pre-start.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Running Pre-Start" > $log

# Allow setting the Jupyter Theme with Arguments
# at runtime with Docker Environment Variables
if [[ -e /opt/conda/envs/python2/bin/jt ]]; then
    if [[ "${ENV_JUPYTER_THEME}" != "" ]]; then
        if [[ "${ENV_JUPYTER_THEME_ARGS}" != "" ]]; then
            echo "$(date +'%m-%d-%y %H:%M:%S') Loading Jupyter Theme(${ENV_JUPYTER_THEME}) with Args(${ENV_JUPYTER_THEME_ARGS})" >> $log
            /opt/conda/envs/python2/bin/jt -t $ENV_JUPYTER_THEME $ENV_JUPYTER_THEME_ARGS &>> $log
        else
            echo "$(date +'%m-%d-%y %H:%M:%S') Loading Jupyter Theme(${ENV_JUPYTER_THEME}) no Args" >> $log
            /opt/conda/envs/python2/bin/jt -t $ENV_JUPYTER_THEME &>> $log
        fi
    else
        echo "$(date +'%m-%d-%y %H:%M:%S') No Jupyter Theme(${ENV_JUPYTER_THEME})" >> $log
    fi
else
    echo "$(date +'%m-%d-%y %H:%M:%S') No jt($/opt/conda/envs/python2/bin/jt) Available" >> $log
fi

echo "$(date +'%m-%d-%y %H:%M:%S') Done Pre-Start" >> $log

exit 0
