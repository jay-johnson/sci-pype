#!/bin/bash

source src/common/common-bash.sh .
source src/common/common-venv.sh .

if [[ -e ${ENV_SCP_VENV_ACTIVATE} ]]; then
    echo "Activate Env with:"
    echo "source ${ENV_SCP_VENV_ACTIVATE}"
else
    err "Please setup the Scipype VirtualEnv before trying to activate"
    exit 1
fi

exit 0
