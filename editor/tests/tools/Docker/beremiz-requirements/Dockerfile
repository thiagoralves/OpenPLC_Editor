#
# Dockerfile for Beremiz
# This container is used to run tests for Beremiz
#
# To run test localy use following command executed from beremiz directory:
# $ docker run --volume=$PWD:/beremiz --workdir="/beremiz" --volume=$PWD/../CanFestival-3:/CanFestival-3 --memory=1g --entrypoint=/beremiz/tests/tools/check_source.sh skvorl/beremiz-requirements
#

FROM skvorl/python2.7-wxpython
MAINTAINER Andrey Skvortsov <andrej.skvortzov@gmail.com>

RUN set -xe \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
               python-nevow \
               python-lxml \
               python-zeroconf \
               python-m2crypto \
               python-autobahn \
               python-future \
               python-simplejson \
    && apt-get install -y --no-install-recommends ca-certificates \
    && apt-get install -y --no-install-recommends wxglade python-cwiid \
    && apt-get install -y --no-install-recommends build-essential automake flex bison mercurial python-pip \
    && apt-get install -y --no-install-recommends \
               pep8 \
               pylint \
               python-pytest \
               python-pytest-timeout \
               gettext \
               python-ddt \
               libpython2.7-dev \
    \
    && apt-get install -y python3-pip \
    && pip3 install crossbar \
    \
    && /usr/bin/pip install gnosis \
                            pyro \
                            sslpsk \
                            posix_spawn \
    && cd / \
    && hg clone http://dev.automforge.net/CanFestival-3 \
    && cd CanFestival-3 \
    && ./configure \
    \
    && cd / \
    && hg clone -r 24ef30a9bcee1e65b027be2c7f7a8d52c41a7479 https://bitbucket.org/automforge/matiec \
    && cd matiec \
    && autoreconf -i \
    && ./configure \
    && make \
    && make install \
    && mkdir /usr/lib/matiec \
    && cp -vR lib/* /usr/lib/matiec \
    && rm -rf /matiec \
    \
    && cd / \
    && hg clone https://bitbucket.org/mjsousa/modbus Modbus \
    && cd Modbus \
    && make \
    \
    && cd / \
    && svn checkout https://svn.code.sf.net/p/bacnet/code/trunk/bacnet-stack/ BACnet \
    && cd BACnet \
    && make MAKE_DEFINE='-fPIC' all \
    \
    && apt-get remove -y bison flex automake python-pip python3-pip libpython2.7-dev \
    && apt-get autoremove -y \
    && apt-get clean -y \
