#
# Dockerfile for wxPython3.0 running on python2.7
#

FROM python:2.7-stretch

RUN set -xe \
    && apt-get update \
    && apt-get install -y --no-install-recommends python-wxgtk3.0 python-matplotlib \
    && apt-get install -y --no-install-recommends python-xvfbwrapper xvfb \
    && apt-get clean
