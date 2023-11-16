#!/bin/bash

echo "Instant OPC-UA server for test"

# Run server
exec $BEREMIZPYTHONPATH - << EOF

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
            inval = await testvar.get_value()
            print(inval)
            await testvarout.set_value(inval*2)
            sys.stdout.flush()
    finally:
        await server.stop()

asyncio.run(main())

EOF
