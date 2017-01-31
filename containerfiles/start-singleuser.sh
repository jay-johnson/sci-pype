#!/bin/bash

log="/tmp/singleuser.log"

set -e

echo "$(date +'%m-%d-%y %H:%M:%S') Starting Single User" > $log

notebook_arg=""
if [ -n "${NOTEBOOK_DIR:+x}" ]; then
    echo "$(date +'%m-%d-%y %H:%M:%S') Notebookdir($NOTEBOOK_DIR)" >> $log
    notebook_arg="--notebook-dir=${NOTEBOOK_DIR}"
fi

echo "$(date +'%m-%d-%y %H:%M:%S') Starting Jupyter" >> $log

echo "$(date +'%m-%d-%y %H:%M:%S') Starting Jupyter" >> $log
port="$ENV_PORT"

echo "exec jupyterhub-singleuser --port=$port --ip=0.0.0.0 --user=$JPY_USER --cookie-name=$JPY_COOKIE_NAME --base-url=$JPY_BASE_URL --hub-prefix=$JPY_HUB_PREFIX --hub-api-url=$JPY_HUB_API_URL ${notebook_arg} $@" >> $log

exec jupyterhub-singleuser \
  --port=$port \
  --ip=0.0.0.0 \
  --user=$JPY_USER \
  --cookie-name=$JPY_COOKIE_NAME \
  --base-url=$JPY_BASE_URL \
  --hub-prefix=$JPY_HUB_PREFIX \
  --hub-api-url=$JPY_HUB_API_URL \
  ${notebook_arg} \
  $@ &>> $log

tail -f $log

