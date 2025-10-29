# Troubleshooting Guide

**Last Updated:** 2025-10-26

This guide helps you diagnose and resolve common issues when using the PyInfra OrbStack connector.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Connection Problems](#connection-problems)
- [VM Creation Failures](#vm-creation-failures)
- [Performance Issues](#performance-issues)
- [Operation Failures](#operation-failures)
- [Getting Help](#getting-help)

## Installation Issues

### Package Not Found

**Problem:** `pip` or `uv` cannot find `pyinfra-orbstack` package.

**Solution:**

```bash
# Verify Python version (3.9+ required)
python --version

# For development installation from source
git clone https://github.com/yourusername/pyinfra-orbstack.git
cd pyinfra-orbstack
uv sync --dev  # or: pip install -e ".[dev]"
```

### Import Errors

**Problem:** `ImportError: No module named 'pyinfra_orbstack'`

**Causes:**
- Package not installed in active virtual environment
- Wrong Python interpreter being used

**Solution:**

```bash
# Verify package installation
uv pip list | grep pyinfra  # or: pip list | grep pyinfra

# Check Python interpreter
which python

# Reinstall if needed
uv pip install -e .  # or: pip install -e .
```

## Connection Problems

### OrbStack Not Running

**Problem:** `OrbStack is not running` or connection timeout errors.

**Solution:**

```bash
# Check if OrbStack is running
orbctl status

# Start OrbStack if not running
open -a OrbStack  # macOS

# Verify orbctl is accessible
which orbctl
```

### VM Not Found

**Problem:** `VM 'vm-name' not found` or `[-32602] no machine found`.

**Causes:**
- VM name typo
- VM was deleted
- Wrong OrbStack context

**Solution:**

```bash
# List all VMs
orbctl list

# Verify VM name matches exactly (case-sensitive)
orbctl info vm-name

# Check if VM is in stopped state
orbctl status vm-name
```

## VM Creation Failures

### VM Creation Timeout

**Problem:** VM creation times out after 180 seconds.

**Causes:**
- System memory pressure
- OrbStack resource constraints
- Network issues downloading image
- OrbStack in degraded state

**Solution:**

1. **Check system resources:**

```bash
# Check memory usage
vm_stat | grep "Pages free"

# Check OrbStack resource allocation
orbctl config show | grep -E "(memory|cpu)"
```

2. **Restart OrbStack:**

```bash
# Quit OrbStack
osascript -e 'quit app "OrbStack"'

# Wait a few seconds, then restart
open -a OrbStack

# Wait for OrbStack to be ready
sleep 10
orbctl status
```

3. **Pre-pull VM image:**

```bash
# Pre-pull the image to avoid timeout during creation
orbctl create temp-vm ubuntu:22.04
orbctl delete temp-vm
```

4. **Reduce concurrent operations:**

```bash
# Run tests serially instead of in parallel
pytest -n 1  # Disable pytest-xdist parallelization
```

### "Already Exists" Error

**Problem:** `[-32098] create 'vm-name' : machine already exists`

**Causes:**
- Previous creation attempt hung but succeeded
- VM was not properly cleaned up
- Name collision

**Solution:**

```bash
# Check if VM exists
orbctl list | grep vm-name

# If VM exists and is usable
orbctl start vm-name

# If VM exists but is corrupted, delete and retry
orbctl delete vm-name --force
```

**Note:** The connector automatically handles this scenario in `create_vm_with_retry()` by verifying the VM and treating it as a successful creation if usable.

### Image Pull Failures

**Problem:** Image download fails or times out.

**Solution:**

```bash
# Check network connectivity
ping -c 3 hub.docker.com

# Try pulling image manually
orbctl create test-image-pull ubuntu:22.04
orbctl delete test-image-pull

# Use a different image mirror if available
orbctl create my-vm ubuntu:22.04@sha256:...
```

## Performance Issues

### Slow VM Operations

**Problem:** VM operations take significantly longer than expected.

**Causes:**
- High system memory usage
- Swap thrashing
- Too many concurrent VMs
- OrbStack resource contention

**Solution:**

1. **Check memory and swap usage:**

```bash
# macOS memory pressure
memory_pressure

# Check swap usage
sysctl vm.swapusage

# If swap > 30%, reduce memory pressure:
# - Close unused applications
# - Restart OrbStack
# - Delete unused VMs
```

2. **Optimize OrbStack resources:**

```bash
# Check current allocation
orbctl config show

# Adjust if needed (example: increase memory to 16GB)
orbctl config set memory_mib 16384
```

3. **Reduce concurrent VM count:**

```bash
# List running VMs
orbctl list --running

# Stop unused VMs
orbctl stop unused-vm
```

### Test Suite Takes Too Long

**Problem:** Full test suite takes 20+ minutes.

**Solution:**

1. **Run only fast tests:**

```bash
# Skip slow E2E tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit
```

2. **Use test parallelization (with caution):**

```bash
# Run with 2 workers (balance between speed and reliability)
pytest -n 2

# Or auto-detect optimal worker count
pytest -n auto
```

3. **Reuse VMs in tests:**

The test suite already implements worker VM reuse via the `worker_vm` fixture in `conftest.py`.

## Operation Failures

### SSH Connection Failures

**Problem:** Cannot execute commands inside VM via SSH.

**Causes:**
- VM not fully started
- Network not initialized
- SSH daemon not running in VM

**Solution:**

```bash
# Verify VM is running
orbctl status vm-name

# Check VM has IP address
orbctl info vm-name | grep ip4

# Wait for VM to be fully ready (done automatically in connector)
sleep 5

# Test SSH manually
orbctl ssh vm-name echo "test"
```

### File Transfer Failures

**Problem:** `put_file` or `get_file` operations fail.

**Causes:**
- Invalid file paths
- Permission issues
- Disk space constraints

**Solution:**

```bash
# Verify source file exists (for put_file)
ls -l /local/path/file

# Check disk space in VM
orbctl run vm-name df -h

# Verify destination directory exists
orbctl run vm-name mkdir -p /path/to/destination

# Test file transfer manually
orbctl push vm-name local-file:/remote/path
orbctl pull vm-name /remote/path:local-file
```

### Operation Decorator Errors

**Problem:** `@operation` decorated functions fail with unexpected errors.

**Causes:**
- Missing PyInfra host context
- Incorrect operation signature
- State object not passed correctly

**Solution:**

1. **Verify host context:**

```python
from pyinfra import host

# Inside operation or deployment
if not host:
    print("No host context available")
```

2. **Check operation signature:**

```python
from pyinfra.api import operation

@operation
def my_operation():
    """Correct operation signature."""
    # Must be called within PyInfra execution context
    pass
```

3. **Run with PyInfra CLI:**

```bash
# Ensure operations are run via pyinfra command
pyinfra inventory.py deploy.py

# Not directly as Python script:
# python deploy.py  # This won't work!
```

## Network and Connectivity

### Cross-VM Communication Fails

**Problem:** VMs cannot communicate with each other.

**Causes:**
- Incorrect hostname resolution
- Network not initialized
- Firewall rules

**Solution:**

```bash
# Verify .orb.local domain resolution
orbctl run vm1 ping -c 3 vm2.orb.local

# Check VM IP addresses
orbctl info vm1 | grep ip4
orbctl info vm2 | grep ip4

# Test direct IP connectivity
orbctl run vm1 ping -c 3 <vm2-ip>
```

### DNS Resolution Issues

**Problem:** DNS lookups fail inside VM.

**Solution:**

```bash
# Test DNS resolution
orbctl run vm-name nslookup google.com

# Check DNS configuration
orbctl run vm-name cat /etc/resolv.conf

# Verify network connectivity
orbctl run vm-name ping -c 3 8.8.8.8
```

## Common Error Messages

### `[-32602] no machine found: 'vm-name'`

**Meaning:** VM does not exist.

**Solution:** Verify VM name and create if needed:

```bash
orbctl list
orbctl create vm-name ubuntu:22.04
```

### `[-32098] create 'vm-name' : machine already exists`

**Meaning:** VM already exists (may be from failed previous attempt).

**Solution:** Use existing VM or delete and recreate:

```bash
orbctl start vm-name  # Use existing
# OR
orbctl delete vm-name && orbctl create vm-name ubuntu:22.04
```

### `subprocess.TimeoutExpired: Command 'orbctl create ...' timed out after 180 seconds`

**Meaning:** VM creation exceeded timeout (usually due to system resources).

**Solution:** See [VM Creation Timeout](#vm-creation-timeout) section above.

### `Connection refused` or `Connection timeout`

**Meaning:** Cannot connect to VM or service.

**Solution:**
- Verify VM is running: `orbctl status vm-name`
- Check VM IP: `orbctl info vm-name | grep ip4`
- Wait for VM to be fully ready (10-30 seconds after start)

## Diagnostic Commands

### System Health Check

```bash
# Check OrbStack status
orbctl status

# List all VMs
orbctl list

# Check system resources
vm_stat | head -5
top -l 1 | grep -E "CPU|PhysMem"
```

### Connector Health Check

```bash
# Verify connector is importable
python -c "from pyinfra_orbstack.connector import OrbStackConnector; print('OK')"

# Test VM discovery
python -c "from pyinfra_orbstack.connector import OrbStackConnector; \
    data = OrbStackConnector.make_names_data(); print(f'Found {len(data)} VMs')"
```

### Test Specific Operation

```bash
# Test VM creation flow
cd tests
pytest tests/test_vm_operations_integration.py::test_vm_lifecycle_integration -v
```

## Getting Help

### Information to Gather

When reporting issues, please provide:

1. **Environment:**
   - Python version: `python --version`
   - PyInfra version: `pip show pyinfra`
   - OrbStack version: `orbctl version` or check About in UI
   - macOS version: `sw_vers`

2. **Error details:**
   - Full error message and stack trace
   - Command that failed
   - Relevant log output

3. **Reproduction steps:**
   - Minimal code to reproduce the issue
   - Any relevant configuration files

### Support Channels

- **GitHub Issues:** [pyinfra-orbstack issues](https://github.com/yourusername/pyinfra-orbstack/issues)
- **PyInfra Documentation:** [pyinfra.com](https://pyinfra.com)
- **OrbStack Documentation:** [docs.orbstack.dev](https://docs.orbstack.dev)

### Known Limitations

See [Known Limitations](known-limitations.md) for architectural constraints and unsupported features.

### Debug Mode

Enable verbose output for more diagnostic information:

```bash
# PyInfra verbose mode
pyinfra -v inventory.py deploy.py

# Very verbose (debug level)
pyinfra -vv inventory.py deploy.py

# Pytest verbose mode
pytest -vv tests/
```

## Related Documentation

- [README.md](../README.md) - Main project documentation
- [Installation Guide](installation.md) - Detailed installation instructions
- [Known Limitations](known-limitations.md) - Architectural constraints
- [Development Journal](../dev-journal/) - Historical issues and solutions
