#!/bin/bash

filetouse="full-stack-compose.yml"

source ./properties.sh .

if [ ! -d "$ENV_PROJ_DIR" ]; then
    echo "Creating Project Dir($ENV_PROJ_DIR)"
    mkdir -p -m 777 $ENV_PROJ_DIR
fi
if [ ! -d "$ENV_DATA_DIR" ]; then
    echo "Creating Data Dir($ENV_DATA_DIR)"
    mkdir -p -m 777 $ENV_DATA_DIR
fi
if [ ! -d "$ENV_DATA_BIN_DIR" ]; then
    echo "Creating Data Bin($ENV_DATA_BIN_DIR)"
    mkdir -p -m 777 $ENV_DATA_BIN_DIR
fi
if [ ! -d "$ENV_DATA_SRC_DIR" ]; then
    echo "Creating Data Source($ENV_DATA_SRC_DIR)"
    mkdir -p -m 777 $ENV_DATA_SRC_DIR
fi
if [ ! -d "$ENV_DATA_DST_DIR" ]; then
    echo "Creating Data Destination($ENV_DATA_DST_DIR)"
    mkdir -p -m 777 $ENV_DATA_DST_DIR
fi

echo "Before starting changing permissions with:"
echo "   chown -R driver:users ${ENV_DATA_DIR}/*" 
# docker-compose is mounting the volumes with root:root access which
# prevents Jupyter from accessing these from inside the container
# as a note why this works: the Jupyter container runs as the driver user set to
# user id 1000 with group id 100
sudo chown -R 1000:100 ${ENV_DATA_DIR}/*

echo "Starting Composition: $filetouse"
docker-compose -f $filetouse up -d
echo "Done"

exit 0
