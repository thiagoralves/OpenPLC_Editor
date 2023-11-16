#!/bin/bash

rm -f ./SRVOK ./PLCOK

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
import os
import time
import asyncio

from asyncua import Server

async def main():
    server = Server()
    host = os.environ.get("OPCUA_DEFAULT_HOST", "127.0.0.1")
    endpoint = "opc.tcp://"+host+":4840/freeopcua/server/"
    await server.init()
    server.set_endpoint(endpoint)

    uri = "http://beremiz.github.io"
    idx = await server.register_namespace(uri)

    objects = server.get_objects_node()

    testobj = await objects.add_object(idx, "TestObject")
    testvarout = await testobj.add_variable(idx, "TestOut", 1.2)
    testvar = await testobj.add_variable(idx, "TestIn", 5.6)
    await testvar.set_writable()

    await server.start()
    try:
        while True:
            await asyncio.sleep(1)
            print(await testvar.get_value())
            sys.stdout.flush()
    finally:
        await server.stop()

asyncio.run(main())

EOF
SERVER_PID=$!

# Start PLC with opcua test
setsid $BEREMIZPYTHONPATH $BEREMIZPATH/Beremiz_cli.py -k \
     --project-home $BEREMIZPATH/tests/projects/opcua_client build transfer run > >(
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
c=30
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
