#!/usr/bin/env python3

from pyinfra.operations import server

# Use a simple PyInfra operation
server.shell(commands=["echo 'hello world'"])
