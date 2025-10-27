#!/usr/bin/env python3
"""
Basic VM Deployment Example

This example demonstrates:
- Creating a VM with the OrbStack connector
- Installing packages
- Creating users and files
- Running basic system operations

Usage:
    pyinfra @orbstack/vm-name 01-basic-vm-deployment.py
"""

from pyinfra.operations import apt, files, server

# Update package cache
apt.update(
    name="Update apt cache",
    cache_time=3600,
)

# Install essential packages
apt.packages(
    name="Install essential packages",
    packages=[
        "curl",
        "wget",
        "git",
        "htop",
        "vim",
    ],
    update=False,
)

# Create a directory
files.directory(
    name="Create application directory",
    path="/opt/myapp",
    present=True,
    user="root",
    group="root",
    mode="755",
)

# Create a configuration file
files.file(
    name="Create config file",
    path="/opt/myapp/config.txt",
    user="root",
    group="root",
    mode="644",
)

# Write content to the file
files.put(
    name="Write configuration",
    src=None,
    dest="/opt/myapp/config.txt",
    content="# Application Configuration\nENV=production\nDEBUG=false\n",
)

# Run a shell command
server.shell(
    name="Check system information",
    commands=[
        "uname -a",
        "lsb_release -a",
    ],
)

# Create a system user
server.user(
    name="Create application user",
    user="appuser",
    system=True,
    home="/opt/myapp",
    shell="/bin/bash",
)

print("✅ Basic deployment complete!")
