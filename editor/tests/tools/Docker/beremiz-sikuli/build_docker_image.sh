#!/bin/bash

set -e

echo "Building docker image"
docker build \
    --build-arg UID=$(id -u) \
    --build-arg GID=$(id -g) \
    -t beremiz_sikuli .

