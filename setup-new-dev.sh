#!/bin/bash

source src/common/common-bash.sh .
source src/common/common-venv.sh .

if [[ ! -e /opt/work ]]; then
    lg "Creating symlink: ln -s $(pwd) /opt/work"
    ln -s $(pwd) /opt/work
    last_status=$?
    if [[ "${last_status}" != "0" ]]; then
        err "Creating Scipype repository Symlink(/opt/work) Failed. Please confirm the symlink can be setup on the host before retrying. (check permissions on /opt)"
        lg ""
        lg "ln -s $(pwd) /opt/work"
        lg ""
        exit 1
    fi
fi

if [[ ! -e ${ENV_SCP_VENV_BASE_DIR} ]]; then

    lg "Creating Virtual Environment Base Dir Path: ${ENV_SCP_VENV_BASE_DIR}"
    mkdir -p -m 777 $ENV_SCP_VENV_BASE_DIR
    last_status=$?
    if [[ "${last_status}" != "0" ]]; then
        err "Creating Virtual Environment Base Dir Path Failed: ${ENV_SCP_VENV_BASE_DIR}"
        lg ""
        lg "mkdir -p -m 777 ${ENV_SCP_VENV_BASE_DIR}"
        lg ""
        exit 1
    fi

    if [[ ! -e ${ENV_SCP_VENV_BASE_DIR} ]]; then
        err "Creating Virtual Environment Failed to Create Dir: ${ENV_SCP_VENV_BASE_DIR}"
        lg ""
        lg "mkdir -p -m 777 ${ENV_SCP_VENV_BASE_DIR}"
        lg ""
        exit 1
    fi
fi

lg "Creating VirtualEnv(${ENV_SCP_VENV_NAME}) Path(${ENV_SCP_VENV_PATH})"

pushd $ENV_SCP_VENV_BASE_DIR >> /dev/null
virtualenv $ENV_SCP_VENV_NAME
last_status=$?
if [[ "${last_status}" != "0" ]]; then
    err "Creating VirtualEnv(${ENV_SCP_VENV_NAME}) Failed. Please confirm virtualenv is setup on this host"
    exit 1
fi
popd >> /dev/null

lg "Activating ${ENV_SCP_VENV_ACTIVATE}"
source ${ENV_SCP_VENV_ACTIVATE}

lg "Done Activating VirtualEnv(${ENV_SCP_VENV_ACTIVATE})"

lg "Install Python 2 Pips into VirtualEnv(${ENV_SCP_VENV_ACTIVATE})"
./python2/venv_install_pips.sh

echo ""
echo "---------------------------------------------------------"
echo "Activate the new Scipype virtualenv with:"
echo ""
echo "source ./dev-properties.sh"
echo "   or:"
echo "source ./properties.sh"
echo ""

exit 0
