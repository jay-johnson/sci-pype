registry="docker.io"
version="2.0.0"
maintainer="jayjohnson"
basename="jupyter/scipy-notebook"
imagename="jupyter"

export ENV_PROJ_DIR="/opt/project"
export ENV_DATA_DIR="/opt/work/data"
export ENV_DATA_SRC_DIR="/opt/work/data/src"
export ENV_DATA_DST_DIR="/opt/work/data/dst"

# Allow running starters from outside the container
export ENV_DATA_BIN_DIR="/opt/work/data/bin"
export ENV_PRESTART_SCRIPT="/opt/containerfiles/pre-start-notebook.sh"
export ENV_START_SCRIPT="/opt/containerfiles/start-notebook.sh"
export ENV_POSTSTART_SCRIPT="/opt/containerfiles/post-start-notebook.sh"

export ENV_DEPLOYMENT_TYPE="Local"
export ENV_REDIS_HOST="localhost"
export ENV_REDIS_PORT="6000"
export ENV_REDIS_SRC_KEY="JUPYTER_SRC_KEY"
export ENV_REDIS_DST_KEY="JUPYTER_DST_KEY"

export ENV_SYNTHESIZE_DIR="/opt/work/data/synthesize"
export ENV_SYNTHESIZE_BIN="/opt/containerfiles/synthesize.sh"
export ENV_TIDY_DIR="/opt/work/data/tidy"
export ENV_TIDY_BIN="/opt/containerfiles/tidy.sh"
export ENV_ANALYZE_DIR="/opt/work/data/analyze"
export ENV_ANALYZE_BIN="/opt/containerfiles/analyze.sh"
export ENV_OUTPUT_DIR="/opt/work/data/output"
export ENV_OUTPUT_BIN="/opt/containerfiles/output-model.sh"
export ENV_REDIS_MODEL_OUT_BIN="/opt/containerfiles/redis-model.sh"
export ENV_REDIS_MODEL_DST_KEY="JUPYTER_REDIS_MODEL_DST_KEY"
export ENV_BINS=/opt/work/bins
export ENV_LIBS=/opt/work/libs

# Configuration Dir:
export ENV_CONFIGS_DIR=/opt/work/configs

# Global Python Dirs:
export ENV_PYTHON_SRC_DIR=/opt/work/src
export ENV_PYTHON_COMMON_DIR=/opt/work/src/common
export ENV_PYTHON_REDIS_DIR=/opt/work/src/connectors/redis
export ENV_PYTHON_DB_DIR=/opt/work/src/connectors/database
export ENV_PYTHON_SCHEMA_DIR=/opt/work/src/databases/schema

# Slack Debugging Env:
export ENV_SLACK_ENABLED=1
export ENV_SLACK_BOTNAME=bugbot
export ENV_SLACK_CHANNEL=debugging
export ENV_SLACK_NOTIFY_USER=jay
export ENV_SLACK_TOKEN=xoxb-51351043345-Am35WoBrkDENM31FLv8bOzvC
export ENV_SLACK_ENVNAME=dev-jupyter

export ENV_SYSLOG_ENABLED=1
export PATH_TO_JUPYTER=$(which ipython)
export PYSPARK_DRIVER_PYTHON=${PATH_TO_JUPYTER}
export PYSPARK_DRIVER_PYTHON_OPTS="notebook --NotebookApp.open_browser=False --NotebookApp.ip='*' --NotebookApp.port=8880"
export ENV_THIRD_PARTY_SOURCE_DIR=/opt/work/src/thirdparty
export ENV_AWS_KEY=AWS_KEY
export ENV_AWS_SECRET=AWS_SECRET

export ENV_SCP_VENV_BASE_DIR="/tmp"
export ENV_SCP_VENV_NAME="scipype"
export ENV_SCP_VENV_PATH="${ENV_SCP_VENV_BASE_DIR}/${ENV_SCP_VENV_NAME}"
export ENV_SCP_VENV_BIN="${ENV_SCP_VENV_PATH}/bin"
export ENV_SCP_VENV_ACTIVATE="${ENV_SCP_VENV_BIN}/activate"
export ENV_SCP_VENV_DEACTIVATE="${ENV_SCP_VENV_BIN}/deactivate"

if [[ "${PYTHONPATH}" == "" ]]; then
    export PYTHONPATH=/opt/work
else
    export PYTHONPATH=${PYTHONPATH}:/opt/work
fi

export ENV_SCP_ACTIVATE_BY_DEFAULT=1
if [[ "${ENV_SCP_ACTIVATE_BY_DEFAULT}" == "1" ]]; then
    if [[ -e ${ENV_SCP_VENV_ACTIVATE} ]]; then
        source $ENV_SCP_VENV_ACTIVATE .
    else
        echo "Did not find Scipype VirtualEnv At Path(${ENV_SCP_VENV_ACTIVATE}). Please install it with: scipype$ ./setup-new-dev.sh"
    fi
fi
