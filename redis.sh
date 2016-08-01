#!/bin/bash

imagename="redis-server"

echo "SSH-ing into Docker image($imagename)"
docker exec -ti $imagename env TERM=xterm /bin/bash

exit 0
