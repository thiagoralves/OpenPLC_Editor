#!/bin/bash

set -e

CONTAINER=beremiz_sikuli_current

docker stop $CONTAINER
docker start $CONTAINER 
docker exec $CONTAINER bash -c "do_tests $1"
docker stop $CONTAINER

