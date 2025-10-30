# User Guide

Welcome to the PyInfra OrbStack Connector user guide! This directory contains comprehensive documentation for installing, configuring, and using the connector.

## Quick Links

- **[Project README](../../README.md)** - Project overview and quick start
- **[Installation](#installation)** - Get up and running
- **[Compatibility](#compatibility)** - System requirements and tested configurations
- **[Migration Guide](#migration-guide)** - Migrate from CLI to PyInfra
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions
- **[Known Limitations](#known-limitations)** - Current constraints and workarounds
- **[Operation Timing](#operation-timing)** - Performance monitoring and debugging

## Getting Started

### New Users

If you're new to pyinfra-orbstack, follow this path:

1. **[Installation](#installation)** - Install and configure the connector
2. **[Project README: Quick Start](../../README.md#quick-start)** - Learn basic usage
3. **[Compatibility](#compatibility)** - Verify your system meets requirements
4. **[Project README: Operations](../../README.md#operations)** - Explore available operations

### Migrating from CLI

If you're currently using `orbctl` directly in PyInfra deployments:

1. **[Migration Guide](#migration-guide)** - Step-by-step migration instructions
2. **[Known Limitations](#known-limitations)** - Understand what's different
3. **[Troubleshooting](#troubleshooting)** - Common migration issues

## Documentation Index

### Installation

**File:** Installation instructions are in the [Project README](../../README.md#installation)

**Contents:**
- Prerequisites (Python 3.9+, PyInfra 2.0+, OrbStack)
- Installing from PyPI
- Development installation

**Quick Install:**
```bash
# Using uv (recommended)
uv add pyinfra-orbstack

# Using pip
pip install pyinfra-orbstack
```

### Compatibility

**File:** [compatibility.md](compatibility.md)

**Contents:**
- Verified configurations (Python, PyInfra, OrbStack versions)
- Tested Linux distributions
- Expected compatibility matrix
- Platform support (macOS, Linux)
- Version compatibility testing

**Use this when:**
- Setting up a new environment
- Upgrading Python, PyInfra, or OrbStack
- Troubleshooting version-related issues
- Planning system requirements

### Migration Guide

**File:** [migration-guide.md](migration-guide.md)

**Contents:**
- Before and after code examples
- CLI command to PyInfra operation mappings
- Step-by-step migration instructions
- Common patterns and best practices
- Performance comparisons

**Use this when:**
- Converting existing `orbctl` CLI scripts to PyInfra
- Learning PyInfra operation equivalents
- Understanding the benefits of the connector
- Planning a migration strategy

**Example Migration:**
```python
# Before (CLI approach)
server.shell(
    name="Create VM",
    commands=["orbctl create web-vm ubuntu:22.04"],
)

# After (Connector approach)
from pyinfra_orbstack.operations.vm import vm_create

vm_create(
    name="web-vm",
    image="ubuntu:22.04",
)
```

### Troubleshooting

**File:** [troubleshooting.md](troubleshooting.md)

**Contents:**
- Common issues and solutions
- Installation problems
- Connection and network issues
- VM lifecycle troubleshooting
- File transfer problems
- Performance issues
- Debugging techniques

**Use this when:**
- Encountering errors or unexpected behavior
- Operations failing or timing out
- Connection problems
- Looking for debugging tips

**Common Issues:**
- Package not found
- OrbStack connection errors
- VM operations timing out
- SSH connection failures
- File transfer errors

### Known Limitations

**File:** [known-limitations.md](known-limitations.md)

**Contents:**
- OrbStack CLI limitations
- PyInfra architectural constraints
- Unsupported features and why
- Workarounds and alternatives
- Future considerations

**Use this when:**
- Planning deployments
- Understanding what's not supported
- Looking for workarounds
- Considering feature requests

**Key Limitations:**
- No per-VM resource limits (global OrbStack pool)
- No VM snapshots (use `vm_clone` or `vm_export`)
- No direct VM-to-VM file transfer (use intermediate storage)
- Network configuration managed by OrbStack

### Operation Timing

**File:** [timing-guide.md](timing-guide.md)

**Contents:**
- Using the timing utility
- Context manager and decorator usage
- Logging configuration
- Performance analysis techniques
- Best practices

**Use this when:**
- Debugging slow operations
- Analyzing deployment performance
- Monitoring operation execution time
- Optimizing workflows

**Quick Example:**
```python
import logging
from pyinfra_orbstack.timing import timed_operation

logging.basicConfig(level=logging.INFO)

with timed_operation("vm_deployment"):
    vm_create(name="web-server", image="ubuntu:22.04")
```

## Additional Resources

### Official Documentation

- **[PyInfra Documentation](https://docs.pyinfra.com/)** - PyInfra framework documentation
- **[OrbStack Documentation](https://docs.orbstack.dev/)** - OrbStack features and CLI reference

### Project Documentation

- **[Architecture Decision Records](../adrs/)** - Key architectural decisions
- **[Development Journal](../dev-journal/)** - Implementation notes and analysis
- **[Contributing Guide](../../CONTRIBUTING.md)** - How to contribute
- **[Examples Directory](../../examples/)** - Practical usage examples

### Examples

The [examples directory](../../examples/) contains practical deployment scenarios:

- **[01-basic-vm-deployment.py](../../examples/01-basic-vm-deployment.py)** - Simple VM setup
- **[02-multi-vm-deployment.py](../../examples/02-multi-vm-deployment.py)** - Multiple VMs
- **[03-vm-lifecycle-management.py](../../examples/03-vm-lifecycle-management.py)** - VM lifecycle
- **[04-docker-deployment.py](../../examples/04-docker-deployment.py)** - Docker containers
- **[05-dev-environment.py](../../examples/05-dev-environment.py)** - Development environment

## Getting Help

### In This Documentation

1. Check the [Troubleshooting Guide](troubleshooting.md) first
2. Review [Known Limitations](known-limitations.md) for constraints
3. Consult the [Compatibility Matrix](compatibility.md) for version info

### Online Resources

- **[GitHub Issues](https://github.com/elazar/pyinfra-orbstack/issues)** - Report bugs or request features
- **[GitHub Discussions](https://github.com/elazar/pyinfra-orbstack/discussions)** - Ask questions
- **[PyInfra Community](https://pyinfra.com)** - General PyInfra help

## Quick Reference

### Common Operations

```python
from pyinfra_orbstack.operations.vm import (
    vm_create, vm_start, vm_stop, vm_delete,
    vm_info, vm_list, vm_status,
    vm_clone, vm_export, vm_import
)

# Create and start a VM
vm_create(name="my-vm", image="ubuntu:22.04")
vm_start("my-vm")

# Get VM information
info = vm_info()
status = vm_status()

# Clone for backup
vm_clone("my-vm", "my-vm-backup")

# Export for archival
vm_export("my-vm", "/backups/my-vm.tar.zst")

# Stop and delete
vm_stop("my-vm")
vm_delete("my-vm", force=True)
```

### Common Patterns

See the [Migration Guide](migration-guide.md) for complete before/after examples.

## Contributing to Documentation

Found an error or have a suggestion? See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on:

- Reporting documentation issues
- Submitting documentation improvements
- Documentation style and standards

---

**Need more help?** Check the [Troubleshooting Guide](troubleshooting.md) or [open an issue](https://github.com/elazar/pyinfra-orbstack/issues).
