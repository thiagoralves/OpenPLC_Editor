#!/bin/bash

CONTAINER=beremiz_sikuli_current

docker start $CONTAINER
docker exec -i -t -u root $CONTAINER bash
docker stop $CONTAINER
