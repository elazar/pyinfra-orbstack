# PyInfra OrbStack Connector Examples

This directory contains practical, runnable examples demonstrating how to use the PyInfra OrbStack Connector for various deployment scenarios.

## Prerequisites

Before running these examples, ensure you have:

1. **OrbStack** installed and running on your macOS machine
2. **PyInfra** installed: `pip install pyinfra`
3. **pyinfra-orbstack** connector installed: `pip install pyinfra-orbstack`

## Examples Overview

### 1. Basic VM Deployment (`01-basic-vm-deployment.py`)

**Demonstrates:**
- Creating a VM with the OrbStack connector
- Installing system packages
- Creating directories, files, and users
- Running shell commands

**Prerequisites:**
```bash
orbctl create my-vm ubuntu:22.04
```

**Usage:**
```bash
pyinfra @orbstack/my-vm examples/01-basic-vm-deployment.py
```

**What it does:**
- Updates package cache
- Installs essential packages (curl, wget, git, htop, vim)
- Creates application directory `/opt/myapp`
- Creates configuration file
- Creates system user `appuser`

---

### 2. Multi-VM Web Application (`02-multi-vm-deployment.py`)

**Demonstrates:**
- Managing multiple VMs simultaneously
- Setting up a web server (Nginx + Python)
- Setting up a database server (PostgreSQL)
- Inter-VM communication using `.orb.local` domains

**Prerequisites:**
```bash
orbctl create web-vm ubuntu:22.04
orbctl create db-vm ubuntu:22.04
```

**Create inventory file** (`inventories/web-stack.py`):
```python
web_server = [("@orbstack/web-vm",)]
db_server = [("@orbstack/db-vm",)]
```

**Usage:**
```bash
pyinfra inventories/web-stack.py examples/02-multi-vm-deployment.py
```

**What it does:**
- **On db-vm**: Installs and configures PostgreSQL, creates database
- **On web-vm**: Installs Nginx, deploys Python web app, configures reverse proxy
- Tests connectivity between VMs using OrbStack's automatic `.orb.local` domains

**Access:**
- Web application: `http://web-vm.orb.local`
- Database: `postgresql://appuser@db-vm.orb.local:5432/appdb`

---

### 3. VM Lifecycle Management (`03-vm-lifecycle-management.py`)

**Demonstrates:**
- Using OrbStack-specific operations
- VM creation, start, stop, restart, deletion
- Getting VM information
- Listing all VMs

**Usage:**
```bash
# List all VMs
pyinfra @local examples/03-vm-lifecycle-management.py

# Get info about specific VM
pyinfra @orbstack/my-vm examples/03-vm-lifecycle-management.py
```

**What it does:**
- Lists all OrbStack VMs
- Gets detailed VM information
- Demonstrates lifecycle operations (commented out for safety)
- Shows OrbStack status

**Note:** Actual lifecycle operations (create, delete, etc.) are commented out to prevent accidental execution. Uncomment them to use.

---

### 4. Docker Container Deployment (`04-docker-deployment.py`)

**Demonstrates:**
- Installing Docker on an OrbStack VM
- Deploying containerized applications with Docker Compose
- Managing Docker containers via PyInfra

**Prerequisites:**
```bash
orbctl create docker-vm ubuntu:22.04
```

**Usage:**
```bash
pyinfra @orbstack/docker-vm examples/04-docker-deployment.py
```

**What it does:**
- Installs Docker and Docker Compose
- Creates a Docker Compose stack (Nginx + Redis)
- Deploys custom HTML content
- Starts services automatically

**Access:**
- Web application: `http://docker-vm.orb.local:8080`

**Useful commands:**
```bash
orbctl run docker-vm -- docker ps
orbctl run docker-vm -- docker compose -f /opt/webapp/docker-compose.yml logs
```

---

### 5. Development Environment Setup (`05-dev-environment.py`)

**Demonstrates:**
- Setting up a complete development environment
- Installing multiple language runtimes (Python, Node.js, Go)
- Configuring shell environment
- Creating development user and project structure

**Prerequisites:**
```bash
orbctl create dev-vm ubuntu:22.04
```

**Usage:**
```bash
pyinfra @orbstack/dev-vm examples/05-dev-environment.py
```

**What it does:**
- Installs Python 3, Node.js LTS, Go 1.21+
- Installs Docker for containerized development
- Creates `developer` user with configured shell
- Installs common development tools (git, tmux, vim, etc.)
- Installs Python packages (ipython, pytest, black, flake8, mypy)
- Installs Node packages (typescript, nodemon, yarn, pnpm)
- Configures bash with aliases and environment variables

**Connect to environment:**
```bash
orbctl run dev-vm -- su - developer
```

---

## General Usage Patterns

### Basic PyInfra with OrbStack

**Target a single VM:**
```bash
pyinfra @orbstack/vm-name deploy.py
```

**Target multiple VMs:**
```bash
pyinfra @orbstack/vm1,@orbstack/vm2 deploy.py
```

**Using an inventory file:**
```python
# inventory.py
production = [
    ("@orbstack/web-1",),
    ("@orbstack/web-2",),
]
database = [("@orbstack/db-1",)]
```

```bash
pyinfra inventory.py deploy.py
```

### OrbStack-Specific Operations

Import OrbStack operations in your deployment scripts:

```python
from pyinfra_orbstack.operations.vm import (
    vm_create,
    vm_delete,
    vm_info,
    vm_list,
    vm_start,
    vm_stop,
    vm_restart,
)

# Use in your deployments
vm_list(name="List all VMs")
vm_info(name="Get VM info")
```

### Inter-VM Communication

OrbStack automatically assigns `.orb.local` domains to VMs:

```python
# Connect from one VM to another
server.shell(
    name="Test connectivity",
    commands=[
        "ping -c 4 other-vm.orb.local",
        "curl http://web-vm.orb.local:8080",
        "psql -h db-vm.orb.local -U appuser -d appdb",
    ],
)
```

## Tips and Best Practices

### 1. VM Naming

Use descriptive names for your VMs:
```bash
orbctl create web-prod-1 ubuntu:22.04
orbctl create db-staging ubuntu:22.04
orbctl create cache-dev ubuntu:22.04
```

### 2. Idempotency

PyInfra operations are idempotent by default. Running the same deployment multiple times is safe:
```bash
# Safe to run multiple times
pyinfra @orbstack/my-vm deploy.py
pyinfra @orbstack/my-vm deploy.py  # No-op if nothing changed
```

### 3. Testing

Test your deployments on a dedicated VM before applying to production:
```bash
orbctl create test-vm ubuntu:22.04
pyinfra @orbstack/test-vm deploy.py
# Verify
orbctl delete test-vm
```

### 4. Debugging

Use PyInfra's verbose mode to see detailed execution:
```bash
pyinfra @orbstack/my-vm deploy.py -vv
```

Check OrbStack VM status:
```bash
orbctl list
orbctl info my-vm
orbctl logs my-vm
```

### 5. Cleanup

Remove VMs when done:
```bash
orbctl delete my-vm
```

## Common Patterns

### Conditional Execution

Run operations only on specific VMs:
```python
from pyinfra import host

if host.name == "web-vm":
    # Web-specific operations
    pass

if "production" in host.groups:
    # Production-specific operations
    pass
```

### Using Facts

Access VM information:
```python
from pyinfra import host
from pyinfra.facts.server import Home, Hostname

home = host.get_fact(Home)
hostname = host.get_fact(Hostname)

print(f"Home: {home}")
print(f"Hostname: {hostname}")
```

### File Transfers

Transfer files to VMs:
```python
from pyinfra.operations import files

files.put(
    name="Upload config",
    src="local/config.yml",
    dest="/etc/myapp/config.yml",
)
```

### Using Templates

Use Jinja2 templates:
```python
files.template(
    name="Deploy Nginx config",
    src="templates/nginx.conf.j2",
    dest="/etc/nginx/sites-available/myapp",
    server_name=host.name,
    port=8080,
)
```

## Troubleshooting

### VM Not Found
```bash
# Check VMs exist
orbctl list

# Create if needed
orbctl create my-vm ubuntu:22.04
```

### Connection Issues
```bash
# Check VM is running
orbctl info my-vm

# Start if stopped
orbctl start my-vm

# Check SSH is accessible
orbctl ssh my-vm
```

### OrbStack Networking
```bash
# Test connectivity
ping web-vm.orb.local

# Check OrbStack status
orbctl status
```

## Additional Resources

- [Main Documentation](../docs/README.md)
- [User Guide](../docs/user-guide/)
- [Troubleshooting Guide](../docs/user-guide/troubleshooting.md)
- [Migration Guide](../docs/user-guide/migration-guide.md)
- [PyInfra Documentation](https://docs.pyinfra.com/)
- [OrbStack Documentation](https://docs.orbstack.dev/)

## Contributing

Have a useful example? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing examples.

Good examples:
- Demonstrate a specific use case
- Are well-documented with comments
- Include prerequisites and expected output
- Follow PyInfra best practices
- Are tested and working
