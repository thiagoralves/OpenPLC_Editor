#!/bin/bash

set -e

echo "Building docker image"
cp -f ../../../requirements.txt requirements.txt
docker build \
    --build-arg UID=$(id -u) \
    --build-arg GID=$(id -g) \
    -t beremiz_sikuli .

