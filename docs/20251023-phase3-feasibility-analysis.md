# ADR-002: Phase 3 Feasibility Analysis and Implementation Strategy

**Date:** 2025-10-23
**Status:** Accepted
**Deciders:** Project Maintainers
**Type:** Architecture Decision Record

## Context

Phase 3 of the pyinfra-orbstack project roadmap outlines "Advanced Operations and
Cross-VM Communication" with two primary task groups:

1. **Task 3.1: Cross-VM Communication** - Operations for VM-to-VM connectivity
   testing, remote command execution, and file transfers
2. **Task 3.2: Advanced VM Configuration** - Resource management and health monitoring operations

Before beginning implementation, a comprehensive analysis was conducted to:

- Verify OrbStack CLI capabilities align with proposed operations
- Assess architectural fit with PyInfra's design patterns
- Identify gaps between task specifications and available functionality
- Determine if sufficient information exists to proceed with implementation

This ADR documents the findings from reviewing OrbStack documentation (via web
search), testing OrbStack CLI commands, analyzing existing connector
implementation patterns, and evaluating PyInfra's architectural constraints.

## Findings

### 1. OrbStack Configuration and Resource Management Capabilities

**OrbStack Config System Analysis:**

Testing `orbctl config show` revealed:

- **Global Settings**: CPU and memory are configured at the OrbStack-level
  - `cpu: 11` - Total CPU cores allocated to OrbStack
  - `memory_mib: 16384` - Total memory (16GB) allocated to OrbStack
  - Network configuration: `network.subnet4: 192.168.138.0/23`
  - Rosetta support: `rosetta: true`

- **Per-Machine Settings**: Limited to username configuration
  - `machine.nas-vm.username: matttu`
  - `machine.router-vm.username: matttu`
  - `machine.test-invalid-user.username: invalid-user`

**Key Insight:** [Inference] OrbStack uses a shared resource pool model where all
VMs share the configured CPU/memory allocation. There is no CLI support for
per-VM resource limits (CPU, memory, disk quotas).

### 2. OrbStack Networking Architecture

**Documented Capabilities:**

- Automatic domain assignment: `machine-name.orb.local`
- Docker Compose services: `service.project.orb.local`
- Custom domains via labels: `dev.orbstack.domains`
- Wildcard domain support
- IPv6 support
- VPN and custom DNS compatibility
- Network subnet configuration: `192.168.138.0/23`

**Cross-VM Networking:**

- VMs exist on the same virtual network (shared subnet)
- [Inference] VMs can communicate via IP addresses or `.orb.local` domains
- [Unverified] No explicit documentation on VM-to-VM connectivity guarantees
- [Inference] Standard network tools (ping, traceroute, ssh) should work between VMs using standard Linux networking

**Port Forwarding:**

- `machines.forward_ports: true` - Enables port forwarding from host to VMs
- `machines.expose_ports_to_lan: true` - Exposes VM ports to LAN

### 3. OrbStack CLI Command Coverage

**Available Commands:**

```text
Linux Machines:
✓ clone       - Create VM copy
✓ create      - Create new VM
✓ default     - Get/set default machine
✓ delete      - Delete VM
✓ export      - Export VM to file
✓ import      - Import VM from file
✓ info        - Get VM information (supports JSON output)
✓ list        - List all VMs (supports JSON output)
✓ logs        - View VM logs
✓ pull        - Copy files from VM to host
✓ push        - Copy files from host to VM
✓ rename      - Rename VM
✓ restart     - Restart VM
✓ run         - Execute commands in VM
✓ ssh         - Show SSH connection details
✓ start       - Start VM
✓ stop        - Stop VM

General:
✓ config      - Change OrbStack settings
✓ status      - Check OrbStack/VM status
```

**Missing CLI Commands:**

- ✗ Per-VM resource configuration (CPU, memory, disk limits)
- ✗ Direct VM-to-VM file transfer (no `vm_copy` between two VMs)
- ✗ VM health check commands
- ✗ Network interface configuration per VM
- ✗ Explicit VM-to-VM connectivity testing

### 4. PyInfra Architectural Constraints

**Host-Centric Operation Model:**

PyInfra operations follow a strict host-centric model:

- Operations execute on the "current host" (the host in context)
- Each operation targets `host.data` for the current host
- Cross-host operations are not part of PyInfra's design

**Example from existing implementation:**

```python
@operation()
def vm_info():
    """Get detailed VM information for current host."""
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return {}
    yield build_vm_info_command(vm_name)
```

**Implications:**

- Operations like `vm_execute(target_vm, command)` conflict with this model
- Cross-VM file transfers don't fit naturally (operation spans two hosts)
- PyInfra handles multi-host scenarios via inventory, not cross-host operations

### 5. Analysis of Proposed Phase 3 Operations

#### Task 3.1.1: Cross-VM Connectivity Operations

| Operation | Status | Notes |
|-----------|--------|-------|
| `vm_ping` | ⚠️ **Needs Redesign** | [Inference] Should execute ping from current VM to target VM using standard `server.shell()` operation, not a custom OrbStack operation |
| `vm_execute` | ❌ **Conflicts with Architecture** | Duplicates existing `run_shell_command` connector method; violates PyInfra's host-centric model |
| "User specification" | ✅ **Already Implemented** | Connector's `run_shell_command` supports `-u` flag |
| "Network routing/DNS" | ✅ **Handled by OrbStack** | Automatic `.orb.local` domains and shared subnet |

#### Task 3.1.2: VM-to-VM File Transfer Operations

| Operation | Status | Notes |
|-----------|--------|-------|
| `vm_copy_file` | ⚠️ **Architecturally Complex** | No direct OrbStack support; would require: VM1→Host (pull)→VM2 (push); violates host-centric model |
| Directory sync | ❌ **Not OrbStack-Specific** | Use standard PyInfra `files.sync()` or rsync via `server.shell()` |
| File permissions | ✅ **Standard PyInfra** | Use `files.put()` with mode parameter |
| Progress reporting | ❌ **Not Supported** | [Unverified] OrbStack's push/pull commands don't provide progress callbacks |

#### Task 3.2.1: VM Resource Management

| Operation | Status | Notes |
|-----------|--------|-------|
| CPU/memory config | ❌ **Not Supported** | Only global OrbStack-level settings available, no per-VM limits |
| Disk management | ❌ **Not OrbStack-Specific** | Use standard Linux tools via `server.shell()` |
| Network interface config | ❌ **Not Supported** | OrbStack manages networking automatically |
| Custom VM parameters | ⚠️ **Limited** | Only per-VM username configuration available |

#### Task 3.2.2: VM Health Monitoring Operations

| Operation | Status | Notes |
|-----------|--------|-------|
| `vm_health_check` | ⚠️ **Needs Definition** | What constitutes "health"? Should use standard PyInfra server operations |
| System resource monitoring | ❌ **Not OrbStack-Specific** | Use standard tools: top, free, df via `server.shell()` |
| Service status checking | ✅ **Standard PyInfra** | Use existing `server.service()` operations |
| Automated recovery | ❌ **Too Vague** | Needs detailed specification of recovery scenarios |

## Decision

**Phase 3 requires significant redesign before implementation.** The current task specifications include:

1. Operations not supported by OrbStack CLI
2. Operations that conflict with PyInfra's architectural model
3. Operations that duplicate existing PyInfra functionality
4. Operations that are too vague to implement

### Approved Approach: Redesign Phase 3 as "Enhanced VM Operations"

**Phase 3 will be restructured into three focused sub-phases:**

#### Phase 3A: VM Networking Information Operations ✅ **FEASIBLE**

Implement operations that expose OrbStack's networking capabilities:

```python
@operation()
def vm_network_details():
    """
    Get comprehensive network information for current VM.

    Returns:
        dict: Network configuration including:
            - IP addresses (IPv4, IPv6)
            - .orb.local domain name
            - Subnet information
            - Gateway address
    """
    pass

@operation()
def vm_test_connectivity(target: str, method: str = "ping"):
    """
    Test network connectivity from current VM to target.

    Args:
        target: Target hostname, IP, or machine-name.orb.local
        method: Test method (ping, curl, nc)

    Returns:
        bool: Connectivity status
    """
    # Uses standard Linux tools via server.shell()
    pass

@operation()
def vm_dns_lookup(hostname: str):
    """
    Resolve hostname from current VM.

    Args:
        hostname: Hostname to resolve

    Returns:
        str: Resolved IP address
    """
    pass
```

**Implementation Notes:**

- These operations execute standard Linux commands (ping, curl, host, dig)
- They respect PyInfra's host-centric model
- They provide OrbStack-aware helpers (e.g., automatic .orb.local domain handling)

#### Phase 3B: Global Configuration Management ✅ **FEASIBLE**

Implement operations for OrbStack-level configuration (not per-VM):

```python
@operation()
def orbstack_config_get(key: str):
    """
    Get OrbStack configuration value.

    Args:
        key: Configuration key (e.g., 'cpu', 'memory_mib')

    Returns:
        str: Configuration value
    """
    yield f"orbctl config get {key}"

@operation()
def orbstack_config_set(key: str, value: str):
    """
    Set OrbStack configuration value.

    Args:
        key: Configuration key
        value: New value

    Returns:
        bool: Success status
    """
    yield f"orbctl config set {key} {value}"

@operation()
def vm_username_set(vm_name: str, username: str):
    """
    Set default username for a VM.

    Args:
        vm_name: VM name
        username: Default username
    """
    yield f"orbctl config set machine.{vm_name}.username {username}"
```

**Implementation Notes:**

- Manages OrbStack global settings only
- Clearly documents that resource limits are OrbStack-wide, not per-VM
- Provides per-VM username configuration (only supported per-VM setting)

#### Phase 3C: VM Logging and Diagnostics ✅ **FEASIBLE**

Implement operations for VM troubleshooting:

```python
@operation()
def vm_logs(lines: int = 50, follow: bool = False):
    """
    Get VM system logs for current host.

    Args:
        lines: Number of log lines to retrieve
        follow: Stream logs continuously

    Returns:
        str: Log output
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return ""

    # Note: follow mode not suitable for operations
    yield f"orbctl logs {vm_name} --lines {lines}"

@operation()
def vm_status_detailed():
    """
    Get detailed status for current VM.

    Returns detailed status including:
    - Running state
    - Resource usage
    - Uptime
    - Recent log entries
    """
    pass
```

### Rejected Operations and Rationale

**Rejected from Phase 3:**

1. **`vm_execute(target_vm, command)`**
   - **Reason**: Violates PyInfra's host-centric model
   - **Alternative**: Use PyInfra's inventory to target specific VMs directly

2. **`vm_copy_file(source_vm, dest_vm, path)`**
   - **Reason**: Spans two hosts, not supported by PyInfra's operation model
   - **Alternative**: Use two separate operations (pull to host, push to target) or use standard rsync/scp within VMs

3. **Per-VM Resource Configuration (CPU/Memory/Disk)**
   - **Reason**: Not supported by OrbStack CLI
   - **Alternative**: Document that resource allocation is OrbStack-wide

4. **`vm_health_check()`**
   - **Reason**: Too vague; health checking is application-specific
   - **Alternative**: Use standard PyInfra server operations for specific checks

5. **"Automated Recovery Operations"**
   - **Reason**: Insufficient specification; recovery logic is use-case specific
   - **Alternative**: Users implement custom recovery logic using existing operations

## Consequences

### Positive Consequences

1. **Architectural Alignment**: Redesigned operations respect PyInfra's host-centric model
2. **OrbStack Capability Match**: Operations align with actual CLI capabilities
3. **Clear Value Proposition**: Each operation provides OrbStack-specific value
4. **Maintainability**: Operations are well-defined with clear implementation paths
5. **Testing Feasibility**: Redesigned operations can be tested with existing patterns
6. **Documentation Clarity**: Users understand what operations do and why they exist

### Negative Consequences

1. **Delayed Phase 3**: Redesign adds time before implementation begins
2. **Reduced Scope**: Some originally envisioned operations are not feasible
3. **User Expectations**: If Phase 3 was communicated externally, expectations need adjustment
4. **Cross-VM Limitations**: No native support for cross-VM file transfers or remote execution

### Trade-offs

#### Trade-off 1: Native Cross-VM Operations vs. Standard PyInfra Patterns

- **Chosen**: Use standard PyInfra multi-host patterns instead of custom cross-VM operations
- **Rationale**: Maintains architectural consistency; users familiar with PyInfra understand the pattern
- **Impact**: Users must explicitly target VMs via inventory rather than using cross-VM operations

#### Trade-off 2: Per-VM Resource Limits vs. Global Configuration

- **Chosen**: Expose only OrbStack's global configuration, document limitation
- **Rationale**: Cannot implement features not supported by underlying tool
- **Impact**: Users needing per-VM limits must use alternative solutions (Docker resource constraints, Kubernetes, etc.)

#### Trade-off 3: Comprehensive Health Monitoring vs. Focused Diagnostics

- **Chosen**: Provide basic diagnostic operations (logs, detailed status) rather than health monitoring
- **Rationale**: Health criteria are application-specific; better handled by users
- **Impact**: Users implement custom health checks using provided diagnostic operations

## Alternatives Considered

### Alternative 1: Implement Phase 3 As-Is

**Decision**: Rejected

**Reasoning**:

- Would require implementing operations with no CLI support (hacks/workarounds)
- Would violate PyInfra's architectural patterns
- Would create maintenance burden and user confusion
- Would deliver low-quality operations that don't work as users expect

### Alternative 2: Skip Phase 3 Entirely

**Decision**: Rejected

**Reasoning**:

- Networking information operations provide real value
- Configuration management operations are useful for automation
- Diagnostic operations aid troubleshooting
- Complete skip would miss opportunities for useful enhancements

### Alternative 3: Defer Phase 3 Until After Phase 4-5

**Decision**: Considered but not chosen

**Reasoning**:

- Testing (Phase 4) and documentation (Phase 5) are valuable
- However, redesigned Phase 3 is now well-defined and feasible
- Implementation can proceed in parallel with Phase 4-5 work
- User feedback from documentation phase could inform Phase 3 refinements

### Alternative 4: Implement Custom Cross-VM Communication Layer

**Decision**: Rejected

**Reasoning**:

- Would require significant architectural work
- Would conflict with PyInfra's connector model
- OrbStack's networking already enables VM-to-VM communication via standard tools
- Over-engineering for limited benefit

## Implementation Plan

### Phase 3A: VM Networking Information Operations

**Estimated Effort**: 2-3 days
**Dependencies**: None
**Deliverables**:

- 3-5 networking information operations
- Command builder functions
- Unit tests (mocked CLI responses)
- Integration tests (if OrbStack available)
- Documentation updates

### Phase 3B: Global Configuration Management

**Estimated Effort**: 2 days
**Dependencies**: None
**Deliverables**:

- 3-4 configuration management operations
- Command builder functions
- Unit tests
- Integration tests
- Documentation with clear per-VM vs. global setting explanations

### Phase 3C: VM Logging and Diagnostics

**Estimated Effort**: 1-2 days
**Dependencies**: None
**Deliverables**:

- 2-3 diagnostic operations
- Command builder functions
- Unit tests
- Integration tests
- Troubleshooting guide documentation

### Testing Strategy

- **Unit Tests**: Mock `orbctl config`, `orbctl logs` commands
- **Integration Tests**: Test against real OrbStack installation (conditional)
- **E2E Tests**: Multi-VM scenarios testing network connectivity
- **Coverage Target**: Maintain 90%+ overall coverage

### Documentation Requirements

1. **Operation Documentation**: Docstrings with usage examples
2. **Architecture Documentation**: Explain host-centric model limitations
3. **User Guide**: How to achieve common cross-VM scenarios
4. **Migration Guide**: If any Phase 3 tasks were previously documented

## Recommendations

### Immediate Actions

1. **Update TASKS.md**
   - Replace current Phase 3 tasks with redesigned sub-phases
   - Document rejected operations and rationale
   - Update timeline estimates

2. **Create User-Facing Documentation**
   - Document OrbStack's networking model
   - Provide patterns for cross-VM communication using standard PyInfra
   - Explain resource allocation model (global vs. per-VM)

3. **Begin Phase 3A Implementation**
   - Start with networking information operations
   - Follow established patterns from Phase 2
   - Maintain high test coverage

### Future Considerations

1. **Monitor OrbStack Updates**
   - Watch for new CLI commands supporting per-VM configuration
   - If per-VM resource limits are added, revisit rejected operations

2. **Gather User Feedback**
   - After Phase 5 (documentation), collect feedback on needed operations
   - Prioritize additional operations based on real use cases

3. **Consider Contrib Module**
   - For operations that don't fit core connector
   - For experimental or use-case-specific operations
   - For operations requiring external dependencies

## References

### OrbStack-Specific Documentation

- **OrbStack CLI Commands**: Output from `orbctl --help` (tested 2025-10-23)
  - Lists all available `orbctl` commands for VM lifecycle management
  - Documents: create, delete, start, stop, restart, clone, export, import, rename,
    list, info, run, ssh, push, pull, logs, config
  - Confirms absence of per-VM resource configuration commands

- **OrbStack Configuration System**: Output from `orbctl config show` (tested
  2025-10-23)
  - Documents global settings: `cpu`, `memory_mib`, `network.subnet4`
  - Documents per-machine settings: `machine.<name>.username` (only per-VM
    configuration available)
  - Confirms resource allocation is OrbStack-wide, not per-VM

- **OrbStack CLI Usage**: [Command line & CI
  usage](https://docs.orbstack.dev/headless) (docs.orbstack.dev)
  - Comprehensive CLI reference for headless and automation use cases
  - Documents `orb`/`orbctl` command syntax and examples
  - Configuration management via `orbctl config` commands

- **OrbStack Networking Guide**: [Switching from Docker Desktop to OrbStack on
  macOS](https://betterstack.com/community/guides/scaling-docker/switching-to-orbstack-on-macos/)
  (betterstack.com)
  - Documents automatic `.orb.local` domain assignment
  - Explains custom domain configuration via `dev.orbstack.domains` labels
  - Describes HTTPS certificate auto-generation
  - Covers wildcard domain support

- **OrbStack Features Overview**: [OrbStack
  Homepage](https://orbstack.dev/) (orbstack.dev)
  - Documents networking capabilities: seamless integration, IPv6, VPN support
  - Performance characteristics: low CPU/memory usage, native Swift application
  - General feature overview

### PyInfra Architecture Documentation

- **PyInfra Operations Model**: Understanding PyInfra's host-centric operation
  architecture
  - Operations execute on "current host" via `host.data`
  - No native support for cross-host operations
  - Multi-host scenarios handled via inventory, not cross-host operations

- **PyInfra Custom Connectors**: Guide to implementing custom connectors
  - Connector interface requirements
  - `handles_execution` flag and method contracts
  - `make_names_data()` for host discovery

### Project-Specific References

- **Existing Implementation Patterns**:
  - `src/pyinfra_orbstack/connector.py` - Demonstrates connector architecture
  - `src/pyinfra_orbstack/operations/vm.py` - Phase 2 operation patterns
  - Command builder pattern for testability

- **Phase 2 Completion**: Commit `0e31fe0` - "build: configure coverage to
  exclude @operation decorator code"
  - Demonstrates successful operation implementation
  - Established command builder pattern for testing
  - 94% test coverage with 208 tests

- **Testing Infrastructure**:
  - `tests/conftest.py` - Test fixtures and mocking patterns
  - `tests/test_vm_operations_unit.py` - Unit test patterns
  - `tests/test_integration.py` - Integration test patterns (conditional on
    OrbStack availability)

## Related Documents

- `TASKS.md` - Project task plan (requires update)
- `docs/20250116-package-namespace-structure.md` - Package organization patterns
- `docs/testing-and-coverage-methodology.md` - Testing standards
- `README.md` - User-facing documentation (requires Phase 3 updates)

## Changelog

- **2025-10-23**: Initial ADR created based on Phase 3 feasibility analysis
- **2025-10-23**: Accepted after review of OrbStack capabilities and PyInfra constraints

---

**Status Update**: This ADR supersedes the original Phase 3 task plan.
Implementation should proceed using the redesigned sub-phases (3A, 3B, 3C) as
defined in this document.
