export ENV_SCP_VENV_BASE_DIR="/opt/venv"
export ENV_SCP_VENV_NAME="scipype"
export ENV_SCP_VENV_PATH="${ENV_SCP_VENV_BASE_DIR}/${ENV_SCP_VENV_NAME}"
export ENV_SCP_VENV_BIN="${ENV_SCP_VENV_PATH}/bin"
export ENV_SCP_VENV_ACTIVATE="${ENV_SCP_VENV_BIN}/activate"
export ENV_SCP_VENV_DEACTIVATE="${ENV_SCP_VENV_BIN}/deactivate"

test_exists=$(echo ${PYTHONPATH} | grep "$(pwd)" | wc -l)
if [[ "${test_exists}" == "0" ]]; then
    if [[ "${PYTHONPATH}" == "" ]]; then
        export PYTHONPATH=$(pwd)
    else
        export PYTHONPATH=${PYTHONPATH}:$(pwd)
    fi
fi
