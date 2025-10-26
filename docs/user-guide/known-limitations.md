# Known Limitations

**Last Updated:** 2025-10-26

This document consolidates known limitations of the PyInfra OrbStack connector, distinguishing between limitations of OrbStack itself, architectural constraints of PyInfra, and design decisions in the connector.

## Table of Contents

- [OrbStack Limitations](#orbstack-limitations)
- [PyInfra Architectural Constraints](#pyinfra-architectural-constraints)
- [Connector Design Limitations](#connector-design-limitations)
- [Workarounds](#workarounds)

## OrbStack Limitations

These limitations exist in OrbStack itself and cannot be addressed by the connector.

### Resource Management

#### No Per-VM Resource Limits

**Limitation:** OrbStack uses a global resource pool shared by all VMs. Individual VMs cannot have dedicated CPU or memory limits.

**Details:**
- Configuration settings like `cpu` and `memory_mib` apply to **all VMs collectively**
- OrbStack dynamically allocates resources from the global pool as needed
- Cannot guarantee specific resources for critical VMs
- Cannot prevent one VM from consuming all available resources

**Example:**

```bash
# These settings apply GLOBALLY, not per-VM
orbctl config get cpu           # 11 (total for all VMs)
orbctl config get memory_mib    # 16384 (16GB total for all VMs)
```

**Workaround:** Manually manage VM count and workloads to avoid resource contention.

**Reference:** ADR-002 Section 1 (Phase 3 Feasibility Analysis)

#### No Disk Quotas

**Limitation:** Cannot set disk space limits per VM via OrbStack CLI.

**Details:**
- VMs share host filesystem space
- No way to prevent one VM from filling disk
- No way to reserve space for specific VMs

**Workaround:** Monitor disk usage within VMs using standard Linux tools (`df`, `du`).

### VM-to-VM Operations

#### No Direct VM-to-VM File Transfer

**Limitation:** OrbStack CLI does not support direct file copying between VMs.

**Details:**
- `orbctl push` and `orbctl pull` only work between **host** and **VM**
- No built-in command for VM1 → VM2 file transfer

**Workaround 1:** Use PyInfra's `files.get()` and `files.put()` operations:

```python
from pyinfra.operations import files

# Copy file from VM1 to host, then to VM2
files.get(
    name="Download from VM1",
    src="/path/on/vm1/file.txt",
    dest="/tmp/file.txt",
)

# Switch to VM2 in inventory, then:
files.put(
    name="Upload to VM2",
    src="/tmp/file.txt",
    dest="/path/on/vm2/file.txt",
)
```

**Workaround 2:** Use rsync/scp within VMs (requires SSH setup):

```python
from pyinfra.operations import server

server.shell(
    name="Copy file between VMs",
    commands=[
        "scp user@vm1.orb.local:/path/file.txt /destination/",
    ],
)
```

**Reference:** ADR-002 Section 3.1

### VM Snapshots

#### No Snapshot Support

**Limitation:** OrbStack does not support VM snapshots via CLI.

**Details:**
- Cannot create point-in-time snapshots
- Cannot revert VMs to previous states
- No snapshot management commands

**Workaround:** Use `vm_export()` and `vm_import()` operations for backup/restore:

```python
from pyinfra_orbstack.operations.vm import vm_export, vm_import

# Backup VM
vm_export(
    name="my-vm",
    output_path="/backups/my-vm-backup.tar.zst",
)

# Restore VM
vm_delete("my-vm", force=True)
vm_import(
    input_path="/backups/my-vm-backup.tar.zst",
    name="my-vm",
)
```

**Reference:** ADR-002 Section 3.2.3

### Network Configuration

#### No Manual Network Interface Configuration

**Limitation:** Network configuration is fully managed by OrbStack and cannot be manually configured per VM.

**Details:**
- IP addresses assigned automatically
- Cannot set static IPs for VMs
- Cannot configure custom network interfaces
- Cannot modify routing tables via OrbStack

**Automatic Features (not limitations):**
- VMs automatically get `.orb.local` domains
- VMs on same network can communicate
- DNS resolution works automatically

**Workaround:** Use standard Linux networking tools within VMs if custom configuration needed:

```python
from pyinfra.operations import server

server.shell(
    name="Configure networking inside VM",
    commands=[
        "ip route add 10.0.0.0/8 via 192.168.138.1",
    ],
)
```

**Reference:** ADR-002 Section 2

### VM Images

#### Limited to OrbStack-Supported Distributions

**Limitation:** Can only use Linux distributions supported by OrbStack.

**Supported:**
- Ubuntu (all recent versions)
- Debian
- Fedora
- Arch Linux
- Alpine
- Others as listed in [OrbStack documentation](https://docs.orbstack.dev/machines/)

**Not Supported:**
- Windows VMs
- Custom ISO images
- Non-Linux operating systems

**Reference:** [OrbStack Compatibility Matrix](compatibility.md)

## PyInfra Architectural Constraints

These limitations stem from PyInfra's architecture and design patterns.

### Per-Host Operations Model

**Limitation:** PyInfra operations execute on a single host at a time.

**Details:**
- Operations decorated with `@operation` execute in per-host context
- Cannot directly coordinate between multiple hosts within one operation
- Global state operations don't fit PyInfra's model

**Impact on Connector:**
- `orbctl config` operations modify global OrbStack settings, affecting all VMs
- No way to ensure atomic global configuration changes in PyInfra context

**Design Decision:** Implemented `orbstack_config_*` operations despite architectural mismatch, with clear documentation of their global nature.

**Example:**

```python
from pyinfra_orbstack.operations.vm import orbstack_config_set

# This affects ALL VMs, not just current host
orbstack_config_set("memory_mib", "24576")
```

**Reference:** ADR-002 Section 4.2

### State Fact System

**Limitation:** PyInfra's fact system is designed for per-host state, not global state.

**Details:**
- Facts are cached per-host
- No built-in mechanism for global facts
- Refresh behavior assumes host isolation

**Impact:**
- OrbStack global config changes may not be immediately visible across hosts
- No automatic cache invalidation for global state

**Workaround:** Explicitly re-query state when needed rather than relying on fact caching.

**Reference:** ADR-002 Section 4.1

## Connector Design Limitations

These are conscious design decisions in the connector implementation.

### No Async Operation Support

**Limitation:** All operations are synchronous.

**Rationale:**
- PyInfra operations are synchronous by design
- OrbStack CLI is synchronous
- Adds unnecessary complexity for minimal benefit

**Impact:**
- Long-running operations (VM creation, export) block
- Cannot start multiple VMs in parallel within one operation

**Workaround:** Use PyInfra's parallel execution at the inventory level:

```bash
# Execute operations in parallel across hosts
pyinfra inventory.py deploy.py --parallel 5
```

### Limited Error Context

**Limitation:** Error messages from OrbStack CLI are passed through with minimal enhancement.

**Rationale:**
- Preserves original error information
- Avoids misinterpreting OrbStack errors
- Simpler implementation

**Impact:**
- Some error messages may be cryptic (e.g., `[-32098] machine already exists`)
- Users may need to consult OrbStack documentation

**Mitigation:** Comprehensive [Troubleshooting Guide](troubleshooting.md) documents common errors.

### No Docker Container Support

**Limitation:** Connector only supports Linux VMs, not Docker containers.

**Rationale:**
- OrbStack has separate commands for Docker vs. VMs
- Different architectural models (containers vs. VMs)
- Focus on VM management for initial release

**Future Consideration:** Docker container support may be added in future releases if there's demand.

**Reference:** Project scope in README.md

### No Custom VM Parameters Beyond Username

**Limitation:** Only username can be configured per-VM via `vm_username_set()`.

**Rationale:**
- OrbStack only exposes `machine.<name>.username` config via CLI
- No other per-VM configuration options available in OrbStack

**Impact:**
- Cannot set per-VM memory limits
- Cannot set per-VM CPU limits
- Cannot configure per-VM disk size
- Cannot set custom environment variables via config

**Workaround:** Use PyInfra operations to configure VMs after creation:

```python
from pyinfra.operations import server, files

# Install packages
server.packages(
    name="Install dependencies",
    packages=["nginx", "postgresql"],
)

# Configure environment
files.line(
    name="Set environment variable",
    path="/etc/environment",
    line="MYVAR=value",
)
```

**Reference:** ADR-002 Section 1

## Workarounds

### Common Workaround Patterns

#### 1. Global Config Changes

For global configuration that affects all VMs:

```python
from pyinfra_orbstack.operations.vm import orbstack_config_set

# Document that this is global
orbstack_config_set("memory_mib", "24576")
```

**Best Practice:** Document global operations clearly in deployment scripts.

#### 2. VM-to-VM File Transfer

Use two-step transfer via host:

```python
from pyinfra.operations import files

# On source VM
files.get(src="/source/file.txt", dest="/tmp/transfer.txt")

# On destination VM (different host in inventory)
files.put(src="/tmp/transfer.txt", dest="/dest/file.txt")
```

#### 3. Resource Management

Monitor and manage manually:

```python
from pyinfra.operations import server

server.shell(
    name="Check memory usage",
    commands=["free -h", "df -h"],
)
```

#### 4. Backup/Restore Instead of Snapshots

```python
from pyinfra_orbstack.operations.vm import vm_export, vm_import

# Regular backups
vm_export("my-vm", f"/backups/my-vm-{date}.tar.zst")
```

## Non-Limitations (Common Misconceptions)

### Not a Limitation: Cross-VM Communication

**Misconception:** VMs cannot communicate with each other.

**Reality:** VMs can communicate via `.orb.local` domains or IP addresses.

```python
from pyinfra_orbstack.operations.vm import vm_test_connectivity

# This works
vm_test_connectivity("backend-vm.orb.local", method="ping")
```

### Not a Limitation: SSH Access

**Misconception:** Must use `orbctl run` for all commands.

**Reality:** PyInfra can use SSH directly via the connector. The connector transparently uses `orbctl run` under the hood.

```python
from pyinfra.operations import server

# This works - connector handles the details
server.shell(commands=["echo 'Hello World'"])
```

### Not a Limitation: File Transfer

**Misconception:** Cannot transfer files to/from VMs.

**Reality:** File transfer works via `orbctl push`/`pull` (handled by connector).

```python
from pyinfra.operations import files

# This works
files.put(src="local.txt", dest="/remote/path/file.txt")
```

## Future Improvements

Potential areas for enhancement (not guaranteed):

- [ ] Docker container support
- [ ] Enhanced error messages with context
- [ ] Operation retry logic for transient failures
- [ ] Performance optimizations for large-scale deployments
- [ ] Async operation support (if PyInfra adds async support)

## Reporting Issues

If you encounter a limitation not documented here:

1. Check if it's an OrbStack limitation: Test with `orbctl` directly
2. Check if it's a PyInfra limitation: Test with other connectors
3. If connector-specific, open a GitHub Issue

## Related Documentation

- [ADR-0002: Scope Limitation for Advanced Operations](../adrs/0002-advanced-operations-scope.md) - Architectural decision on operational limitations
- [Phase 3 Feasibility Analysis](../dev-journal/20251023-phase3-feasibility-analysis.md) - Detailed analysis of OrbStack capabilities
- [Compatibility Matrix](compatibility.md) - Supported configurations
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [OrbStack Documentation](https://docs.orbstack.dev/) - Official OrbStack capabilities

---

**Note:** This document distinguishes between limitations that:
- **Cannot be fixed** (OrbStack architecture)
- **Should not be fixed** (PyInfra architectural fit)
- **May be fixed** (connector design decisions)

Always verify current OrbStack and PyInfra capabilities as they may evolve over time.
