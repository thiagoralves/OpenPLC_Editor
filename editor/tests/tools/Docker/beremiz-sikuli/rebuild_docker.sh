#!/bin/bash

set -e

./clean_docker_container.sh || true
./clean_docker_image.sh || true
./build_docker_image.sh
./create_docker_container.sh $1

