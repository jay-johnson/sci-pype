registry="docker.io"
maintainer="jayjohnson"
basename="redis-base"
imagename="redis-haproxy-cluster-node"
export ENV_VERSION_TAG="3.2.8"

export ENV_DEPLOYMENT_TYPE="DEV"

export ENV_PROJ_DIR="/opt/work"
export ENV_PROJ_SRC_DIR="/opt/work/src"
export ENV_SRC_DIR="/opt/work/src"
export ENV_DATA_DIR="/opt/work/data"
export ENV_DATA_SRC_DIR="/opt/work/data/src"
export ENV_DATA_DST_DIR="/opt/work/data/dst"

# Allow running starters from outside the container
export ENV_BIN_DIR="/opt/work/bin"
export ENV_PRESTART_SCRIPT="/opt/tools/pre-start.sh"
export ENV_START_SCRIPT="/opt/tools/start-services.sh"
export ENV_POSTSTART_SCRIPT="/opt/tools/post-start.sh"
export ENV_CUSTOM_SCRIPT="/opt/tools/custom-pre-start.sh"
