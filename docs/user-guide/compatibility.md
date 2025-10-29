# Compatibility Matrix

**Last Updated:** 2025-10-26

This document outlines tested configurations and compatibility information for the PyInfra OrbStack connector.

## Verified Configurations

The following configurations have been tested and verified during Phase 4 testing:

### Test Environment

- **Date Tested:** October 23-26, 2025
- **Test Coverage:** 287 tests, 100% pass rate
- **Test Duration:** ~18 minutes (full suite)

| Component | Version | Status |
|-----------|---------|--------|
| **OrbStack** | 2.0.4 | ✅ Verified |
| **Python** | 3.11+ | ✅ Verified |
| **PyInfra** | 2.0.0+ | ✅ Verified |
| **macOS** | macOS 15.x (Sequoia) | ✅ Verified |
| **Architecture** | arm64 (Apple Silicon) | ✅ Verified |

### Tested Linux Distributions

| Distribution | Image | Status | Notes |
|--------------|-------|--------|-------|
| **Ubuntu 22.04** | `ubuntu:22.04` | ✅ Verified | Primary test image |

**Note:** While only Ubuntu 22.04 was explicitly tested, the connector should work with any Linux distribution supported by OrbStack. The connector interacts with VMs through OrbStack's CLI, not directly with the Linux distribution.

## Expected Compatibility

Based on OrbStack's capabilities, the following should work but have not been explicitly tested:

### OrbStack Versions

- **2.0.x:** Expected to work (2.0.4 verified)
- **1.x:** May work but not tested

**Recommendation:** Use OrbStack 2.0.0 or later for best results.

### Python Versions

| Version | Status | Notes |
|---------|--------|-------|
| **3.12** | ✅ Verified | Tested in CI, recommended |
| **3.11** | ✅ Verified | Tested in CI, recommended |
| **3.10** | ✅ Verified | Tested in CI, recommended |
| **3.9** | ⚠️ Supported | Minimum version, **EOL Oct 2025** - recommend upgrading |
| **<3.9** | ❌ Not Supported | Too old |

**Note:** Python 3.9 reached end-of-life on October 5, 2025 and no longer receives security updates. While pyinfra-orbstack still supports Python 3.9 for compatibility with macOS system Python, we recommend using Python 3.10 or later for security reasons.

### PyInfra Versions

| Version | Status | Notes |
|---------|--------|-------|
| **2.0.0+** | ✅ Verified | Current version |
| **1.x** | ❌ Not Supported | Deprecated |

### Operating Systems

| OS | Support | Notes |
|----|---------|-------|
| **macOS** | ✅ Primary | OrbStack's primary platform |
| **Linux** | ⚠️ Experimental | OrbStack has beta Linux support |
| **Windows** | ❌ Not Supported | OrbStack not available |

### Architectures

| Architecture | Status | Notes |
|--------------|--------|-------|
| **arm64 (Apple Silicon)** | ✅ Verified | Tested on M-series Macs |
| **amd64 (Intel)** | 🟡 Expected | Should work but not tested |

### Linux Distributions (Guest VMs)

OrbStack supports a wide range of Linux distributions. While we've only tested Ubuntu 22.04, these should work:

| Distribution | Expected Support | Notes |
|--------------|------------------|-------|
| **Ubuntu** | ✅ All versions | Tested: 22.04 |
| **Debian** | ✅ All versions | Based on OrbStack support |
| **Fedora** | ✅ All versions | Based on OrbStack support |
| **Arch Linux** | ✅ Current | Based on OrbStack support |
| **Alpine** | ✅ Current | Based on OrbStack support |
| **Others** | 🟡 Varies | Check OrbStack documentation |

**Reference:** [OrbStack Linux Machines Documentation](https://docs.orbstack.dev/machines/)

## Limitations by OrbStack

The following are **limitations of OrbStack itself**, not the connector:

### Resource Management

- **Global Resource Pool:** OrbStack uses a single shared resource pool for all VMs
  - Setting: `orbctl config get memory_mib` (global, not per-VM)
  - Setting: `orbctl config get cpu` (global, not per-VM)
- **No Per-VM Limits:** Cannot set memory/CPU limits for individual VMs

### Networking

- **Automatic Configuration:** Network configuration is managed by OrbStack
  - VMs automatically get `.orb.local` domains
  - IP addresses assigned automatically
- **No Manual Network Config:** Cannot manually configure network interfaces per VM

### VM-to-VM Operations

- **No Direct File Transfer:** Cannot directly copy files between VMs using OrbStack CLI
  - Workaround: Use PyInfra's `files.get()` and `files.put()` operations
  - Workaround: Use rsync/scp within VMs if SSH is configured

### Storage

- **No VM Snapshots:** OrbStack does not support VM snapshots in CLI
- **Export/Import Only:** Use `vm_export()` and `vm_import()` for backup/restore

## Connector-Specific Requirements

### Python Package Requirements

```toml
[project]
requires-python = ">=3.9"
dependencies = [
    "pyinfra>=2.0.0",
]
```

### System Requirements

- **OrbStack CLI:** `orbctl` command must be in PATH
- **OrbStack Running:** OrbStack application must be running
- **Disk Space:** Sufficient space for VM images and VMs

## Testing Compatibility

### Running Compatibility Tests

To verify your system's compatibility:

```bash
# Quick check
python -c "from pyinfra_orbstack.connector import OrbStackConnector; print('✅ Connector imports successfully')"

# Verify OrbStack is accessible
orbctl status

# Run integration tests (requires OrbStack)
pytest -m integration

# Run full test suite (requires OrbStack)
pytest
```

### Recommended Test Commands

```bash
# Check Python version
python --version  # Should be 3.9+

# Check PyInfra version
pip show pyinfra  # Should be 2.0.0+

# Check OrbStack version
orbctl version  # Should be 2.0.0+

# Verify orbctl is in PATH
which orbctl

# Test VM creation
orbctl create test-compat-vm ubuntu:22.04
orbctl delete test-compat-vm
```

## Known Issues by Environment

### macOS Specific

- **Memory Pressure:** On systems with high memory pressure (>70% swap), VM creation may timeout
  - **Solution:** Restart OrbStack and close unused applications
  - **Reference:** See [Troubleshooting Guide](troubleshooting.md#vm-creation-timeout)

- **OrbStack Updates:** After OrbStack updates, restart required
  - **Solution:** Quit and restart OrbStack after updates

### Python Environment

- **Virtual Environment Required:** Installing in system Python may cause conflicts
  - **Solution:** Always use a virtual environment (`.venv/`, `venv/`, etc.)

## Version Compatibility Updates

As new versions are tested, this matrix will be updated. Please report successful usage with different configurations via GitHub Issues.

### Reporting Successful Configurations

If you successfully use the connector with a configuration not listed here, please report it:

1. Open a GitHub Issue with title: "Compatibility: [Your Config]"
2. Provide:
   - OrbStack version: `orbctl version`
   - Python version: `python --version`
   - PyInfra version: `pip show pyinfra`
   - OS version: `sw_vers` (macOS) or `uname -a` (Linux)
   - Guest VM distribution tested

## Official Documentation References

For authoritative compatibility information:

- **OrbStack Supported Distributions:** [docs.orbstack.dev/machines/](https://docs.orbstack.dev/machines/)
- **OrbStack System Requirements:** [docs.orbstack.dev/install](https://docs.orbstack.dev/install)
- **PyInfra Compatibility:** [docs.pyinfra.com](https://docs.pyinfra.com)

## Future Testing Plans

Planned testing for future releases:

- [ ] Additional Ubuntu versions (20.04, 24.04)
- [ ] Debian distributions (11, 12)
- [ ] Fedora latest
- [ ] Alpine Linux
- [ ] Intel Mac (amd64) verification
- [ ] OrbStack 2.1+ (when released)
- [ ] Python 3.12+ explicit testing

## Support Policy

- **Tested configurations:** Full support
- **Expected configurations:** Best-effort support
- **Untested configurations:** Community support

For issues with tested configurations, please open a GitHub Issue.

For untested configurations, please try first and report results.

---

**Related Documentation:**
- [Troubleshooting Guide](troubleshooting.md)
- [Known Limitations](known-limitations.md)
- [Installation Guide](installation.md)
