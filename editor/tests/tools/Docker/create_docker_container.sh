#!/bin/bash

set -e

# source directory containing beremiz, matiec, etc..
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../../../.. && pwd )"
echo "SOURCE direcory : $SRCDIR"

# absolute path to test directory. ~/test if not given as only argument
TESTDIR=${1:-~/test}
mkdir -p $TESTDIR
echo "TEST direcory : $TESTDIR"

UNAME=testing
UHOME=/home/$UNAME

# define TESTDEBUG in env to enable dev-mode. This enables :
#   - debug pasthrough for Xnest
#   - VNC port passthrough
DEBUGARGS="-v /tmp/.X11-unix/X0:/tmp/.X11-unix/X0 -e DISPLAY=$DISPLAY -p 5900:5900"

echo "Creating docker container"
docker create \
       --name beremiz_sikuli_current \
       -v $SRCDIR:$UHOME/src \
       -v $TESTDIR:$UHOME/test \
       `if [ "$TESTDEBUG" == "YES" ]; then echo $DEBUGARGS; fi` \
       -w $UHOME/test \
       -i -t beremiz_sikuli /bin/bash

