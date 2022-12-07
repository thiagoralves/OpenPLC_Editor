#!/bin/bash

rm -f ./SRVOK ./PLCOK


yes "" | openssl req -x509 -newkey rsa:2048 -keyout my_private_key.pem -out my_cert.pem \
        -days 355 -nodes -addext "subjectAltName = URI:urn:example.org:FreeOpcUa:python-opcua"
openssl x509 -outform der -in my_cert.pem -out my_cert.der

# Run server
$BEREMIZPYTHONPATH - > >(
    echo "Start SRV loop"
    while read line; do 
        # Wait for server to print modified value
        echo "SRV>> $line"
        if [[ "$line" == 3.4 ]]; then
            echo "PLC could write value"
            touch ./SRVOK
        fi
    done
    echo "End SRV loop"
) << EOF &

import sys
import time

from opcua import ua, Server

server = Server()
server.set_endpoint("opc.tcp://127.0.0.1:4840/freeopcua/server/")

server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
server.load_certificate("my_cert.der")
server.load_private_key("my_private_key.pem")

uri = "http://beremiz.github.io"
idx = server.register_namespace(uri)

objects = server.get_objects_node()

testobj = objects.add_object(idx, "TestObject")
testvarout = testobj.add_variable(idx, "TestOut", 1.2)
testvar = testobj.add_variable(idx, "TestIn", 5.6)
testvar.set_writable()

server.start()

try:
    while True:
        time.sleep(1)
        print testvar.get_value()
        sys.stdout.flush()
finally:
    server.stop()
EOF
SERVER_PID=$!

PROJECT_FILES_DIR=$BEREMIZPATH/tests/projects/opcua_client_encrypted/project_files
mkdir $PROJECT_FILES_DIR
cp my_cert.der my_private_key.pem $PROJECT_FILES_DIR

# Start PLC with opcua test
setsid $BEREMIZPYTHONPATH $BEREMIZPATH/Beremiz_cli.py -k \
     --project-home $BEREMIZPATH/tests/projects/opcua_client_encrypted build transfer run > >(
echo "Start PLC loop"
while read line; do 
    # Wait for PLC runtime to output expected value on stdout
    echo "PLC>> $line"
    if [[ "$line" == 1.2 ]]; then
        echo "PLC could read value"
        touch ./PLCOK
    fi
done
echo "End PLC loop"
) &
PLC_PID=$!

echo all subprocess started, start polling results
res=110  # default to ETIMEDOUT
c=45
while ((c--)); do
    if [[ -a ./SRVOK && -a ./PLCOK ]]; then
        echo got results.
        res=0  # OK success
        break
    else
        echo waiting.... $c
        sleep 1
    fi
done

# Kill PLC and subprocess
echo will kill PLC:$PLC_PID and SERVER:$SERVER_PID
pkill -s $PLC_PID 
kill $SERVER_PID

exit $res
