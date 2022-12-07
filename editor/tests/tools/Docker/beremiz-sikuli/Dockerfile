#
# Dockerfile for Beremiz
# This container is used to run tests for Beremiz
#
FROM ubuntu:focal  
                                        
ENV TERM xterm-256color
    
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ARG UNAME=testing
ENV UNAME ${UNAME}
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID $UNAME
RUN useradd -m -u $UID -g $GID -s /bin/bash $UNAME

RUN set -xe \
    && apt-get update \
    && TZ="America/Paris" \
       DEBIAN_FRONTEND="noninteractive" \
       apt-get install -y --no-install-recommends \
               `# run sikuli` \
               wget \
               libopencv4.2-java \
               openjdk-11-jre \
               \
               `# run X based tests` \
               fluxbox \
               wmctrl xdotool xvfb \
               x11vnc xterm xnest \
               \
               `# to build tested apps` \
               build-essential automake flex bison mercurial \
               libgtk-3-dev libgl1-mesa-dev libglu1-mesa-dev \
               libpython2.7-dev libssl-dev \
               python2 virtualenv cmake

# link obtained from https://raiman.github.io/SikuliX1/downloads.html
RUN set -xe && \
    wget -qP /usr/local/bin \
        https://launchpad.net/sikuli/sikulix/2.0.5/+download/sikulixide-2.0.5.jar && \
    echo 0795f1e0866ee5a7a84e4c89793ea78c /usr/local/bin/sikulixide-2.0.5.jar | md5sum -c && \
    ( echo '#!/bin/sh' && \
      echo "exec java -jar /usr/local/bin/sikulixide-*.jar \"\$@\"" \
    ) | install /dev/stdin /usr/local/bin/sikulix


RUN env echo -e '#!/bin/bash\nmake -f /home/testing/src/beremiz/tests/Makefile $*' > /usr/local/bin/do_tests
RUN chmod +x /usr/local/bin/do_tests

USER $UNAME

RUN mkdir /home/$UNAME/build /home/$UNAME/src /home/$UNAME/test

RUN virtualenv --python=$(which python2) ~/beremizenv

RUN ~/beremizenv/bin/pip install \
        pytest pytest-timeout ddt \
        lxml future matplotlib zeroconf2 enum34 pyro sslpsk posix_spawn \
        twisted nevow autobahn click opcua \
        wxPython==4.1.1

# Point to python binary test scripts will use
ENV BEREMIZPYTHONPATH /home/$UNAME/beremizenv/bin/python

# easy to remember 'do_tests' alias to invoke main makefile
ARG OWNDIRBASENAME=beremiz
ENV OWNDIRBASENAME ${OWNDIRBASENAME}


