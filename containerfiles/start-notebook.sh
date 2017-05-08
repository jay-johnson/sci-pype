#!/bin/bash

log="/tmp/startnotebook.log"

echo "$(date +'%m-%d-%y %H:%M:%S') Starting Notebook" > $log

echo "$(date +'%m-%d-%y %H:%M:%S') Enabling ipywidgets: http://ipywidgets.readthedocs.io/en/latest/user_install.html" >> $log
jupyter nbextension enable --py widgetsnbextension --sys-prefix &>> $log

echo "$(date +'%m-%d-%y %H:%M:%S') Enabling RISE: https://github.com/damianavila/RISE" >> $log
jupyter nbextension install rise --py --sys-prefix
jupyter nbextension enable rise --py --sys-prefix

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

    echo "$(date +'%m-%d-%y %H:%M:%S') exec su $NB_USER -c \"env PATH=$PATH /opt/conda/envs/python2/bin/jupyter notebook $*\"" >> $log

    # Start the notebook server
    exec su $NB_USER -c "env PATH=$PATH /opt/conda/envs/python2/bin/jupyter notebook $*" &>> $log
else
    # Otherwise just exec the notebook
    if [[ "${ENV_JUPYTER_PASSWORD}" == "" ]]; then
        echo "$(date +'%m-%d-%y %H:%M:%S') exec /opt/conda/envs/python2/bin/jupyter notebook --NotebookApp.token='' $*" >> $log
        exec /opt/conda/envs/python2/bin/jupyter notebook --NotebookApp.token='' $* &>> $log
    else
        echo "$(date +'%m-%d-%y %H:%M:%S') exec /opt/conda/envs/python2/bin/jupyter notebook $*" >> $log
        exec /opt/conda/envs/python2/bin/jupyter notebook $* &>> $log
    fi
fi

echo "$(date +'%m-%d-%y %H:%M:%S') Done Starting Notebook" >> $log

tail -f $log
