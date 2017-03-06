#!/bin/bash

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

filetouse="redis-labs-compose.yml"

echo "Starting Composition: $filetouse"
docker-compose -f $filetouse up -d
echo "Done"

exit 0
