#!/bin/bash

set -x -e

echo "Instant encrypted OPC-UA server for test"

rm -f my_cert.pem my_cert.der my_private_key.pem

yes "" | openssl req -x509 -newkey rsa:2048 -keyout my_private_key.pem -out my_cert.pem \
        -days 355 -nodes -addext "subjectAltName = URI:urn:example.org:FreeOpcUa:python-opcua"
openssl x509 -outform der -in my_cert.pem -out my_cert.der

PROJECT_FILES_DIR=$BEREMIZPATH/tests/projects/opcua_browse_encrypted/project_files
mkdir $PROJECT_FILES_DIR -p
cp my_cert.der my_private_key.pem $PROJECT_FILES_DIR

echo "CERTS READY"

# Run server
exec $BEREMIZPYTHONPATH - << EOF

import sys
import os
import time
import asyncio

from asyncua import ua, Server
from asyncua.server.users import User, UserRole

# Asyncua can't work without (over)simple shared cerificates/privkey.
# No user is involved in that case, but asyncua needs it.
# Over permessive User Manager hereafter helps cuting that corner.
class AllAdminUserManager:
    def get_user(self, iserver, username=None, password=None, certificate=None):
        return User(role=UserRole.Admin)

async def main():
    server = Server(user_manager=AllAdminUserManager())
    host = os.environ.get("OPCUA_DEFAULT_HOST", "127.0.0.1")
    endpoint = "opc.tcp://"+host+":4840/freeopcua/server/"
    await server.init()
    server.set_endpoint(endpoint)

    server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
    await server.load_certificate("my_cert.der")
    await server.load_private_key("my_private_key.pem")

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
