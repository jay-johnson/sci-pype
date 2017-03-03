#!/bin/bash

source ./properties.sh .

container="haproxy-redis"

echo "SSH-ing into Docker Container($container)"
docker exec -ti $container env TERM=xterm /bin/bash

exit 0
