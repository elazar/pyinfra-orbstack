# Migration Guide: From orbctl to PyInfra Connector

**Last Updated:** 2025-10-26

This guide helps you migrate from using raw `orbctl` commands to the PyInfra OrbStack connector, showing command mappings and highlighting architectural differences.

## Table of Contents

- [Why Migrate](#why-migrate)
- [Quick Reference](#quick-reference)
- [VM Lifecycle Operations](#vm-lifecycle-operations)
- [VM Information Operations](#vm-information-operations)
- [File Transfer Operations](#file-transfer-operations)
- [Configuration Operations](#configuration-operations)
- [Networking Operations](#networking-operations)
- [Unsupported Operations](#unsupported-operations)
- [Migration Examples](#migration-examples)

## Why Migrate

### Benefits of Using the Connector

**Before (orbctl):**
```bash
#!/bin/bash
# Script-based deployment
orbctl create web-vm ubuntu:22.04
orbctl start web-vm
orbctl run web-vm apt-get update
orbctl run web-vm apt-get install -y nginx
orbctl run web-vm systemctl start nginx
```

**After (PyInfra connector):**
```python
# deploy.py
from pyinfra.operations import server
from pyinfra_orbstack.operations.vm import vm_create, vm_start

# Idempotent, declarative infrastructure
vm_create(name="web-vm", image="ubuntu:22.04")
vm_start("web-vm")

server.packages(
    name="Install nginx",
    packages=["nginx"],
)

server.service(
    name="Ensure nginx is running",
    service="nginx",
    running=True,
    enabled=True,
)
```

**Advantages:**
- **Idempotent:** Safe to run multiple times
- **Declarative:** Describe desired state, not steps
- **Integrated:** Use full PyInfra ecosystem
- **Testable:** Better testing and validation
- **Reusable:** Share deployments as code
- **Multi-host:** Deploy to multiple VMs simultaneously

## Quick Reference

| Task | orbctl Command | PyInfra Connector Operation |
|------|---------------|---------------------------|
| Create VM | `orbctl create vm-name ubuntu:22.04` | `vm_create(name="vm-name", image="ubuntu:22.04")` |
| Start VM | `orbctl start vm-name` | `vm_start("vm-name")` |
| Stop VM | `orbctl stop vm-name` | `vm_stop("vm-name")` |
| Delete VM | `orbctl delete vm-name` | `vm_delete("vm-name")` |
| List VMs | `orbctl list -f json` | `vm_list()` |
| VM Info | `orbctl info vm-name -f json` | `vm_info()` |
| Run Command | `orbctl run vm-name command` | `server.shell(commands=["command"])` |
| Copy to VM | `orbctl push vm-name local:remote` | `files.put(src="local", dest="remote")` |
| Copy from VM | `orbctl pull vm-name remote:local` | `files.get(src="remote", dest="local")` |
| Clone VM | `orbctl clone vm1 vm2` | `vm_clone(source_name="vm1", new_name="vm2")` |

## VM Lifecycle Operations

### Creating VMs

**orbctl:**
```bash
# Basic creation
orbctl create my-vm ubuntu:22.04

# With architecture
orbctl create my-vm ubuntu:22.04 --arch arm64

# With username
orbctl config set machine.my-vm.username myuser
orbctl create my-vm ubuntu:22.04
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_create, vm_username_set

# Basic creation
vm_create(
    name="my-vm",
    image="ubuntu:22.04",
)

# With architecture
vm_create(
    name="my-vm",
    image="ubuntu:22.04",
    arch="arm64",
)

# With username (set after creation)
vm_create(name="my-vm", image="ubuntu:22.04")
vm_username_set("my-vm", "myuser")
```

### Starting/Stopping VMs

**orbctl:**
```bash
orbctl start my-vm
orbctl stop my-vm
orbctl restart my-vm
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_start, vm_stop, vm_restart

vm_start("my-vm")
vm_stop("my-vm")
vm_restart("my-vm")
```

### Deleting VMs

**orbctl:**
```bash
# Normal deletion
orbctl delete my-vm

# Force deletion
orbctl delete my-vm --force
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_delete

# Normal deletion
vm_delete("my-vm")

# Force deletion
vm_delete("my-vm", force=True)
```

### Cloning VMs

**orbctl:**
```bash
orbctl clone source-vm new-vm
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_clone

vm_clone(
    source_name="source-vm",
    new_name="new-vm",
)
```

### Exporting/Importing VMs

**orbctl:**
```bash
# Export
orbctl export my-vm -o /backups/my-vm.tar.zst

# Import
orbctl import /backups/my-vm.tar.zst my-vm-restored
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_export, vm_import

# Export
vm_export(
    name="my-vm",
    output_path="/backups/my-vm.tar.zst",
)

# Import
vm_import(
    input_path="/backups/my-vm.tar.zst",
    name="my-vm-restored",
)
```

## VM Information Operations

### Listing VMs

**orbctl:**
```bash
orbctl list
orbctl list -f json  # JSON output
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_list

# Returns list of VM data dictionaries
vms = vm_list()
for vm in vms:
    print(f"VM: {vm['name']}, State: {vm['state']}")
```

### Getting VM Information

**orbctl:**
```bash
orbctl info my-vm
orbctl info my-vm -f json
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_info

# Get info for current host
vm_data = vm_info()
print(f"State: {vm_data['record']['state']}")
print(f"IP: {vm_data['ip4']}")
```

### Getting VM Status

**orbctl:**
```bash
orbctl status my-vm
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_status

status = vm_status()  # Returns: "running", "stopped", etc.
print(f"VM Status: {status}")
```

### Getting VM IP Address

**orbctl:**
```bash
orbctl info my-vm -f json | jq -r '.ip4'
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_ip

ip_address = vm_ip()  # Returns IP address string
print(f"VM IP: {ip_address}")
```

## File Transfer Operations

### Copying Files to VM

**orbctl:**
```bash
orbctl push my-vm /local/file.txt:/remote/path/file.txt
orbctl push my-vm /local/dir:/remote/dir
```

**PyInfra connector:**
```python
from pyinfra.operations import files

# Single file
files.put(
    name="Upload config file",
    src="/local/file.txt",
    dest="/remote/path/file.txt",
)

# Directory
files.sync(
    name="Sync directory",
    src="/local/dir/",
    dest="/remote/dir/",
)
```

### Copying Files from VM

**orbctl:**
```bash
orbctl pull my-vm /remote/file.txt:/local/file.txt
orbctl pull my-vm /remote/dir:/local/dir
```

**PyInfra connector:**
```python
from pyinfra.operations import files

# Single file
files.get(
    name="Download log file",
    src="/remote/file.txt",
    dest="/local/file.txt",
)
```

**Note:** PyInfra's `files.get()` has limitations compared to `orbctl pull`. For complex scenarios, you may need to use `server.shell()` with tar/scp.

## Configuration Operations

### Global Configuration

**orbctl:**
```bash
# Get configuration
orbctl config get memory_mib
orbctl config show

# Set configuration
orbctl config set memory_mib 24576
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import (
    orbstack_config_get,
    orbstack_config_set,
    orbstack_config_show,
)

# Get configuration
memory = orbstack_config_get("memory_mib")
print(f"Memory: {memory} MiB")

# Show all config
config = orbstack_config_show()

# Set configuration (affects ALL VMs)
orbstack_config_set("memory_mib", "24576")
```

**Important:** These settings are **global** and affect all VMs, not just the current host.

### Per-VM Configuration

**orbctl:**
```bash
# Only username is configurable per-VM
orbctl config set machine.my-vm.username myuser
orbctl config get machine.my-vm.username
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_username_set

# Set username for specific VM
vm_username_set("my-vm", "myuser")
```

**Limitation:** Only username can be configured per-VM via OrbStack CLI.

## Networking Operations

### Cross-VM Connectivity

**orbctl:**
```bash
# Test ping between VMs
orbctl run vm1 ping -c 3 vm2.orb.local

# Test HTTP endpoint
orbctl run vm1 curl -I http://vm2.orb.local:8080

# Test port connectivity
orbctl run vm1 nc -zv vm2.orb.local 5432
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_test_connectivity

# Ping test (default)
vm_test_connectivity("vm2.orb.local")

# Ping with custom count
vm_test_connectivity("vm2.orb.local", method="ping", count=5)

# HTTP endpoint test
vm_test_connectivity("http://vm2.orb.local:8080", method="curl")

# Port connectivity test
vm_test_connectivity("vm2.orb.local:5432", method="nc")
```

### DNS Resolution

**orbctl:**
```bash
# Resolve domain
orbctl run my-vm nslookup google.com

# Get specific record type
orbctl run my-vm dig google.com A
orbctl run my-vm dig google.com AAAA
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_dns_lookup

# A record (default)
ip = vm_dns_lookup("google.com")

# AAAA record
ipv6 = vm_dns_lookup("google.com", lookup_type="AAAA")

# MX record
mx_records = vm_dns_lookup("example.com", lookup_type="MX")
```

### Network Information

**orbctl:**
```bash
orbctl info my-vm -f json | jq '.ip4, .ip6'
```

**PyInfra connector:**
```python
from pyinfra_orbstack.operations.vm import vm_network_info, vm_network_details

# Basic network info
network = vm_network_info()
print(f"IPv4: {network['ip4']}")
print(f"IPv6: {network['ip6']}")

# Detailed network info
details = vm_network_details()
print(f"Hostname: {details.get('hostname')}")
```

## Unsupported Operations

Some `orbctl` capabilities are **not directly supported** by the connector due to OrbStack or PyInfra architectural constraints.

### VM-to-VM File Transfer

**orbctl:** ❌ Not supported
```bash
# This does NOT exist in orbctl
# orbctl copy vm1:/file vm2:/file  # Not a real command
```

**Workaround:**
```python
from pyinfra.operations import files

# Two-step: VM1 → Host → VM2
# On VM1 (in inventory)
files.get(src="/source/file.txt", dest="/tmp/transfer.txt")

# On VM2 (in inventory)
files.put(src="/tmp/transfer.txt", dest="/dest/file.txt")
```

**Alternative workaround:**
```python
from pyinfra.operations import server

# Use scp within VM (if SSH configured)
server.shell(
    name="Copy between VMs",
    commands=["scp user@vm1.orb.local:/source/file.txt /dest/"],
)
```

**Reference:** [Known Limitations - VM-to-VM File Transfer](known-limitations.md#no-direct-vm-to-vm-file-transfer)

### VM Snapshots

**orbctl:** ❌ Not supported
```bash
# These commands do NOT exist
# orbctl snapshot create my-vm
# orbctl snapshot restore my-vm snapshot-name
```

**Workaround:** Use export/import for backup/restore
```python
from pyinfra_orbstack.operations.vm import vm_export, vm_import, vm_delete

# Backup VM
vm_export("my-vm", "/backups/my-vm.tar.zst")

# Restore VM
vm_delete("my-vm", force=True)
vm_import("/backups/my-vm.tar.zst", "my-vm")
```

**Reference:** [Known Limitations - No Snapshot Support](known-limitations.md#no-snapshot-support)

### Per-VM Resource Limits

**orbctl:** ❌ Not supported at per-VM level
```bash
# Cannot set per-VM limits
# Global settings only
orbctl config set memory_mib 16384  # Affects ALL VMs
```

**Impact:** Cannot guarantee resources for specific VMs

**Workaround:** Manage VM count and workloads manually

**Reference:** [Known Limitations - No Per-VM Resource Limits](known-limitations.md#no-per-vm-resource-limits)

## Migration Examples

### Example 1: Simple Web Server Deployment

**Before (bash + orbctl):**
```bash
#!/bin/bash
set -e

# Create and start VM
orbctl create web-vm ubuntu:22.04
orbctl start web-vm

# Wait for VM to be ready
sleep 10

# Install nginx
orbctl run web-vm apt-get update
orbctl run web-vm apt-get install -y nginx

# Copy configuration
orbctl push web-vm nginx.conf:/etc/nginx/nginx.conf

# Start nginx
orbctl run web-vm systemctl restart nginx
orbctl run web-vm systemctl enable nginx

echo "Deployment complete!"
```

**After (PyInfra):**
```python
# deploy.py
from pyinfra import host
from pyinfra.operations import server, files
from pyinfra_orbstack.operations.vm import vm_create, vm_start

# Create VM (idempotent)
vm_create(name=host.name, image="ubuntu:22.04")
vm_start(host.name)

# Install nginx
server.packages(
    name="Install nginx",
    packages=["nginx"],
    update=True,
)

# Upload configuration
files.put(
    name="Upload nginx config",
    src="nginx.conf",
    dest="/etc/nginx/nginx.conf",
)

# Ensure nginx is running
server.service(
    name="Ensure nginx running",
    service="nginx",
    running=True,
    enabled=True,
    restarted=True,
)
```

**Run deployment:**
```bash
pyinfra @orbstack/web-vm deploy.py
```

### Example 2: Multi-VM Application Stack

**Before (bash + orbctl):**
```bash
#!/bin/bash
set -e

# Create VMs
orbctl create db-vm ubuntu:22.04
orbctl create api-vm ubuntu:22.04
orbctl create web-vm ubuntu:22.04

# Start VMs
orbctl start db-vm
orbctl start api-vm
orbctl start web-vm

sleep 10

# Setup database
orbctl run db-vm apt-get update
orbctl run db-vm apt-get install -y postgresql
orbctl run db-vm systemctl start postgresql

# Setup API
orbctl run api-vm apt-get update
orbctl run api-vm apt-get install -y python3-pip
orbctl push api-vm api-server:/opt/api-server
orbctl run api-vm "pip3 install -r /opt/api-server/requirements.txt"
orbctl run api-vm "systemctl start api-server"

# Setup web
orbctl run web-vm apt-get update
orbctl run web-vm apt-get install -y nginx
orbctl push web-vm nginx.conf:/etc/nginx/nginx.conf
orbctl run web-vm systemctl restart nginx
```

**After (PyInfra):**
```python
# inventory.py
hosts = [
    "@orbstack/db-vm",
    "@orbstack/api-vm",
    "@orbstack/web-vm",
]

# deploy.py
from pyinfra import host
from pyinfra.operations import server, files
from pyinfra_orbstack.operations.vm import vm_create, vm_start

# Create and start VM (runs for each host)
vm_create(name=host.name, image="ubuntu:22.04")
vm_start(host.name)

# Database server
if "db-vm" in host.name:
    server.packages(
        name="Install PostgreSQL",
        packages=["postgresql"],
        update=True,
    )

    server.service(
        name="Start PostgreSQL",
        service="postgresql",
        running=True,
        enabled=True,
    )

# API server
if "api-vm" in host.name:
    server.packages(
        name="Install Python",
        packages=["python3-pip"],
        update=True,
    )

    files.sync(
        name="Upload API code",
        src="api-server/",
        dest="/opt/api-server/",
    )

    server.shell(
        name="Install Python dependencies",
        commands=["pip3 install -r /opt/api-server/requirements.txt"],
    )

    server.service(
        name="Start API server",
        service="api-server",
        running=True,
        enabled=True,
    )

# Web server
if "web-vm" in host.name:
    server.packages(
        name="Install nginx",
        packages=["nginx"],
        update=True,
    )

    files.put(
        name="Upload nginx config",
        src="nginx.conf",
        dest="/etc/nginx/nginx.conf",
    )

    server.service(
        name="Start nginx",
        service="nginx",
        running=True,
        enabled=True,
        restarted=True,
    )
```

**Run deployment:**
```bash
# Deploy to all VMs in parallel
pyinfra inventory.py deploy.py --parallel 3
```

### Example 3: Backup and Restore

**Before (bash + orbctl):**
```bash
#!/bin/bash
VM_NAME="production-vm"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d)

# Backup
orbctl export ${VM_NAME} -o ${BACKUP_DIR}/${VM_NAME}-${DATE}.tar.zst

# Restore (if needed)
# orbctl delete ${VM_NAME}
# orbctl import ${BACKUP_DIR}/${VM_NAME}-${DATE}.tar.zst ${VM_NAME}
```

**After (PyInfra):**
```python
# backup.py
from datetime import datetime
from pyinfra_orbstack.operations.vm import vm_export

# Backup with date stamp
date_str = datetime.now().strftime("%Y%m%d")
vm_export(
    name=host.name,
    output_path=f"/backups/{host.name}-{date_str}.tar.zst",
)

# restore.py
from pyinfra_orbstack.operations.vm import vm_delete, vm_import

# Restore from backup
vm_delete(host.name, force=True)
vm_import(
    input_path="/backups/production-vm-20251026.tar.zst",
    name=host.name,
)
```

**Run operations:**
```bash
# Backup
pyinfra @orbstack/production-vm backup.py

# Restore
pyinfra @local restore.py
```

## Next Steps

After migrating to the PyInfra connector:

1. **Explore Examples:** Check the `examples/` directory for more patterns
2. **Read Documentation:** Review [README.md](../../README.md) for all operations
3. **Test Deployments:** Start with development VMs before production
4. **Leverage PyInfra:** Use PyInfra's full feature set (facts, conditionals, loops)
5. **Join Community:** Share your experiences and learn from others

## Related Documentation

- [README.md](../../README.md) - Complete operation reference
- [Known Limitations](known-limitations.md) - What's not supported
- [Troubleshooting Guide](troubleshooting.md) - Common issues
- [Examples](../../examples/) - Practical deployment examples

---

**Questions or Issues?** Open an issue on [GitHub](https://github.com/yourusername/pyinfra-orbstack/issues)
