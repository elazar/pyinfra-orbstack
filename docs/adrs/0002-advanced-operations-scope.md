# ADR-0002: Scope Limitation for Advanced Operations

**Date:** 2025-10-23
**Status:** Accepted
**Deciders:** Project Maintainers
**Type:** Architecture Decision Record

## Context

During planning for advanced operations and cross-VM communication features, a comprehensive feasibility analysis was conducted to verify that:

1. Proposed operations align with OrbStack CLI capabilities
2. Operations fit within PyInfra's architectural patterns
3. Operations provide value beyond existing PyInfra functionality

The analysis (documented separately in `dev-journal/20251023-phase3-feasibility-analysis.md`) revealed several constraints:

1. Several proposed operations are not supported by OrbStack CLI (e.g., per-VM resource limits)
2. Some operations conflict with PyInfra's host-centric architectural model (e.g., cross-VM operations)
3. Other operations duplicate existing PyInfra functionality without adding OrbStack-specific value
4. Some operations were too vague to implement without further specification

## Decision

**Advanced operations will be limited to those that:**
1. Are supported by OrbStack CLI
2. Align with PyInfra's host-centric architectural model
3. Provide OrbStack-specific value beyond standard PyInfra operations

The implementation will be structured into three focused areas:

### Area 1: VM Networking Information Operations

Implement operations that expose OrbStack's networking capabilities within PyInfra's host-centric model:

- `vm_network_details()` - Get comprehensive network info for current VM (IPs, domain, subnet)
- `vm_test_connectivity(target, method)` - Test connectivity from current VM to target
- `vm_dns_lookup(hostname)` - Resolve hostname from current VM

### Area 2: Global Configuration Management

Implement operations for OrbStack-level configuration (not per-VM limits):

- `orbstack_config_get(key)` - Get OrbStack configuration value
- `orbstack_config_set(key, value)` - Set OrbStack configuration value
- `vm_username_set(vm_name, username)` - Set default username for a VM (only available per-VM setting)

### Area 3: VM Logging and Diagnostics

Implement operations for VM troubleshooting:

- `vm_logs(lines, follow)` - Get VM system logs for current host
- `vm_status_detailed()` - Get detailed status for current VM

### Rejected Operations

The following types of operations were excluded from implementation:

1. **Cross-VM command execution (`vm_execute(target_vm, command)`)** - Violates PyInfra's host-centric model
2. **Cross-VM file transfers (`vm_copy_file(source_vm, dest_vm, path)`)** - Spans two hosts, not supported by PyInfra's operation model
3. **Per-VM resource configuration** - Not supported by OrbStack CLI (resources are managed globally)
4. **Generic health checking (`vm_health_check()`)** - Too vague; health checking is application-specific
5. **Automated recovery operations** - Insufficient specification; recovery logic is use-case specific

## Consequences

### Positive Consequences

1. **Architectural Alignment**: Operations respect PyInfra's host-centric model
2. **OrbStack Capability Match**: Operations align with actual CLI capabilities
3. **Clear Value Proposition**: Each operation provides OrbStack-specific value
4. **Maintainability**: Operations are well-defined with clear implementation paths
5. **Testing Feasibility**: Operations can be tested with established patterns

### Negative Consequences

1. **Reduced feature scope**: Some initially desired operations are not feasible
2. **Cross-VM operation limitations**: No native support for cross-VM file transfers or remote execution
3. **Resource management constraints**: Cannot configure per-VM CPU/memory limits (OrbStack architectural limitation)

### Trade-offs

- **Native Cross-VM Operations vs. Standard PyInfra Patterns**: Chose to use standard PyInfra multi-host patterns via inventory rather than custom cross-VM operations
- **Per-VM Resource Limits vs. Global Configuration**: Chose to expose only OrbStack's global configuration and document the limitation
- **Comprehensive Health Monitoring vs. Focused Diagnostics**: Chose to provide basic diagnostic operations rather than application-specific health monitoring

## Alternatives Considered

### Alternative 1: Implement All Proposed Operations As-Is

**Rejected** - Would require implementing operations with no CLI support, would violate PyInfra's architectural patterns, and would create maintenance burden.

### Alternative 2: Skip Advanced Operations Entirely

**Rejected** - Networking information, configuration management, and diagnostic operations provide real value.

### Alternative 3: Implement Custom Cross-VM Communication Layer

**Rejected** - Would require significant architectural work conflicting with PyInfra's connector model; OrbStack's networking already enables VM-to-VM communication via standard tools.

## Implementation Notes

- Area 1 (Networking) estimated at 2-3 days
- Area 2 (Configuration) estimated at 2 days
- Area 3 (Diagnostics) estimated at 1-2 days
- Maintain 90%+ test coverage target
- Document host-centric model limitations clearly
- Provide user guide for cross-VM scenarios using standard PyInfra patterns

## References

- [Feasibility Analysis](../dev-journal/20251023-phase3-feasibility-analysis.md) - Detailed analysis of OrbStack capabilities and PyInfra constraints that informed this decision
- [OrbStack CLI Documentation](https://docs.orbstack.dev/headless) - Command line reference
- [PyInfra Operations Documentation](https://docs.pyinfra.com/en/2.x/operations.html) - PyInfra operation patterns

## Related ADRs

- [ADR-0001: Package Namespace Structure](0001-package-namespace.md) - Establishes package organization patterns used in implementation
