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

envfile="./local/jupyter.env"

echo "Starting new Docker image($registry/$maintainer/${imagename}:${version})"
docker run --name=$imagename \
            --env-file $envfile \
            -v $ENV_PROJ_DIR:$ENV_PROJ_DIR \
            -v $ENV_DATA_DIR:$ENV_DATA_DIR \
            -v $ENV_DATA_BIN_DIR:$ENV_DATA_BIN_DIR \
            -v $ENV_DATA_SRC_DIR:$ENV_DATA_SRC_DIR \
            -v $ENV_DATA_DST_DIR:$ENV_DATA_DST_DIR \
            -v $ENV_SYNTHESIZE_DIR:$ENV_SYNTHESIZE_DIR \
            -v $ENV_TIDY_DIR:$ENV_TIDY_DIR \
            -v $ENV_ANALYZE_DIR:$ENV_ANALYZE_DIR \
            -v $ENV_OUTPUT_DIR:$ENV_OUTPUT_DIR \
            -p 82:8888 \
            -p 444:443 \
            -d $maintainer/$imagename:$version

exit 0
