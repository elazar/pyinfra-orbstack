# PyInfra OrbStack Connector

A PyInfra connector for managing OrbStack VMs and containers with native integration.

## Overview

The PyInfra OrbStack Connector provides seamless integration between PyInfra and OrbStack, allowing you to manage VMs and containers using PyInfra's declarative infrastructure automation framework.

## Features

- **Native PyInfra Integration**: Use the `@orbstack` connector for seamless VM management
- **VM Lifecycle Management**: Create, start, stop, restart, and delete VMs
- **Command Execution**: Run commands inside VMs with proper user and working directory support
- **File Transfer**: Upload and download files to/from VMs
- **Information Retrieval**: Get VM status, IP addresses, and network information
- **Cross-VM Communication**: Test connectivity between VMs

## Installation

### Prerequisites

- Python 3.8 or higher
- PyInfra 2.0.0 or higher
- OrbStack installed and configured
- uv (recommended) or pip for package management

### Install the Connector

```bash
# Using uv (recommended)
uv add pyinfra-orbstack

# Using pip
pip install pyinfra-orbstack
```

### Development Installation

```bash
git clone https://github.com/elazar/pyinfra-orbstack.git
cd pyinfra-orbstack

# Using uv (recommended)
uv sync --dev

# Using pip
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
# inventory.py
from pyinfra import inventory

# Use @orbstack connector to automatically discover VMs
inventory.add_group("@orbstack", {
    "orbstack_vm": True,
})
```

```python
# deploy.py
from pyinfra import host
from pyinfra.operations import server
from pyinfra_orbstack.operations.vm import vm_info, vm_status

# Operations will automatically use the connector
if host.data.orbstack_vm:
    # Get VM information
    vm_data = vm_info()
    status = vm_status()

    print(f"VM Status: {status}")
    print(f"VM IP: {vm_data.get('ip4', 'unknown')}")

    # Install packages
    server.packages(
        name="Install nginx",
        packages=["nginx"],
    )

    # Start services
    server.service(
        name="Start nginx",
        service="nginx",
        running=True,
    )
```

### Manual VM Configuration

```python
# inventory.py
inventory.add_host("@orbstack/my-vm", {
    "vm_name": "my-vm",
    "vm_image": "ubuntu:22.04",
    "vm_arch": "arm64",
})
```

## Operations

### VM Lifecycle Operations

```python
from pyinfra_orbstack.operations.vm import (
    vm_create, vm_delete, vm_start, vm_stop, vm_restart
)

# Create a new VM
vm_create(
    name="test-vm",
    image="ubuntu:22.04",
    arch="arm64",
    user="ubuntu",
)

# Start a VM
vm_start("test-vm")

# Stop a VM
vm_stop("test-vm", force=True)

# Restart a VM
vm_restart("test-vm")

# Delete a VM
vm_delete("test-vm", force=True)
```

### VM Information Operations

```python
from pyinfra_orbstack.operations.vm import (
    vm_info, vm_list, vm_status, vm_ip, vm_network_info
)

# Get detailed VM information
vm_data = vm_info()
print(f"VM Status: {vm_data.get('record', {}).get('state')}")

# List all VMs
all_vms = vm_list()
for vm in all_vms:
    print(f"VM: {vm['name']}, Status: {vm['state']}")

# Get VM status
status = vm_status()
print(f"Current VM Status: {status}")

# Get VM IP address
ip = vm_ip()
print(f"VM IP: {ip}")

# Get network information
network_info = vm_network_info()
print(f"IPv4: {network_info['ip4']}")
print(f"IPv6: {network_info['ip6']}")
```

## Connector Features

### Automatic VM Discovery

The connector automatically discovers all OrbStack VMs and makes them available as PyInfra hosts:

```python
# All VMs are automatically available
# Use @orbstack connector to access them
```

### VM Groups

VMs are automatically grouped based on their characteristics:

- `orbstack`: All OrbStack VMs
- `orbstack_running`: Running VMs only
- `orbstack_arm64`: ARM64 architecture VMs
- `orbstack_amd64`: AMD64 architecture VMs

### Command Execution

Execute commands inside VMs with full PyInfra integration:

```python
from pyinfra.operations import server

# Commands run inside the VM automatically
server.shell(
    name="Check system info",
    commands=["uname -a", "cat /etc/os-release"],
)
```

### File Transfer

Upload and download files to/from VMs:

```python
from pyinfra.operations import files

# Upload a file to the VM
files.put(
    name="Upload config file",
    src="local_config.conf",
    dest="/etc/myapp/config.conf",
)

# Download a file from the VM
files.get(
    name="Download log file",
    src="/var/log/myapp.log",
    dest="local_log.log",
)
```

## Configuration

### VM Configuration

Configure VM properties in your inventory:

```python
# inventory.py
inventory.add_host("@orbstack/my-vm", {
    "vm_name": "my-vm",
    "vm_image": "ubuntu:22.04",
    "vm_arch": "arm64",
    "vm_username": "ubuntu",
    "ssh_user": "ubuntu",
    "ssh_key": "/path/to/ssh/key",
})
```

### SSH Configuration

The connector uses OrbStack's built-in SSH configuration:

- SSH keys are automatically managed by OrbStack
- Default location: `~/.orbstack/ssh/id_ed25519`
- SSH connection strings are automatically generated

## Examples

### Complete VM Setup

```python
# deploy.py
from pyinfra import host
from pyinfra.operations import server, files
from pyinfra_orbstack.operations.vm import vm_create, vm_start

# Create and start a VM
vm_create(
    name="web-server",
    image="ubuntu:22.04",
    arch="arm64",
    user="ubuntu",
)

vm_start("web-server")

# Install and configure nginx
server.packages(
    name="Install nginx",
    packages=["nginx"],
)

files.put(
    name="Upload nginx config",
    src="nginx.conf",
    dest="/etc/nginx/sites-available/default",
)

server.service(
    name="Start nginx",
    service="nginx",
    running=True,
    enabled=True,
)
```

### Multi-VM Deployment

```python
# inventory.py
from pyinfra import inventory

# Define multiple VMs
inventory.add_host("@orbstack/web-server", {
    "vm_name": "web-server",
    "vm_image": "ubuntu:22.04",
})

inventory.add_host("@orbstack/db-server", {
    "vm_name": "db-server",
    "vm_image": "ubuntu:22.04",
})

# Group them
inventory.add_group("web_servers", ["@orbstack/web-server"])
inventory.add_group("db_servers", ["@orbstack/db-server"])
```

```python
# deploy.py
from pyinfra import host
from pyinfra.operations import server

# Deploy to web servers
if host in inventory.get_group("web_servers"):
    server.packages(
        name="Install nginx",
        packages=["nginx"],
    )

# Deploy to database servers
if host in inventory.get_group("db_servers"):
    server.packages(
        name="Install PostgreSQL",
        packages=["postgresql"],
    )
```

## Development

For detailed development information, standards, and guidelines, see the [Documentation Index](docs/README.md).

### Quick Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format and lint code
uv run black src/ tests/
uv run flake8 src/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/matttu/pyinfra-orbstack/issues)
- **Documentation**: [GitHub README](https://github.com/matttu/pyinfra-orbstack#readme)
- **PyInfra Documentation**: [pyinfra.com](https://pyinfra.com)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.
