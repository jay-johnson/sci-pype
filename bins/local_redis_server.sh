#!/bin/bash

pushd /tmp >> /dev/null
nohup /opt/conda/bin/redis-server --port 6000 & > /tmp/redis-data.log
pushd popd >> /dev/null

exit 0
