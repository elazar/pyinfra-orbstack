# ADR-001: Package Namespace Structure

**Date:** 2025-01-16
**Status:** Accepted
**Deciders:** Project Team
**Type:** Architecture Decision Record

## Context

The PyInfra OrbStack Connector project needed to establish a package namespace structure that would integrate seamlessly with PyInfra's architecture while avoiding conflicts and following Python packaging best practices.

## Decision

We chose to use `pyinfra_orbstack` as the package namespace (separate package) rather than `pyinfra.orbstack` (nested namespace within PyInfra).

### Final Structure

```plain
src/pyinfra_orbstack/
├── __init__.py
├── connector.py
└── operations/
    ├── __init__.py
    └── vm.py
```

### Entry Point Configuration

```toml
[project.entry-points."pyinfra.connectors"]
orbstack = "pyinfra_orbstack.connector:OrbStackConnector"
```

## Consequences

### Positive Consequences

1. **No Namespace Conflicts**: `pyinfra_orbstack` doesn't interfere with PyInfra's core `pyinfra` package
2. **Clear Separation**: Makes it obvious this is a third-party extension
3. **Standard Pattern**: Follows Python packaging conventions for third-party packages
4. **Future-Proof**: Won't conflict if PyInfra adds official OrbStack support
5. **Independent Installation**: Can be installed/uninstalled without affecting PyInfra core
6. **Clear Ownership**: Establishes clear boundaries between core PyInfra and extensions

### Negative Consequences

1. **Longer Import Paths**: `from pyinfra_orbstack.operations.vm import vm_create` vs `from pyinfra.orbstack.operations.vm import vm_create`
2. **Less Intuitive**: Doesn't appear as a "native" PyInfra module
3. **Potential Confusion**: Users might expect it to be part of core PyInfra

## Alternatives Considered

### Alternative 1: `pyinfra.orbstack` (Nested Namespace)

- **Pros**: Appears more integrated with PyInfra, shorter import paths
- **Cons**: Creates namespace conflicts, violates Python packaging principles, potential installation issues
- **Rejected**: Creates conflicts with PyInfra's core namespace

### Alternative 2: `orbstack_connector`

- **Pros**: Completely independent naming
- **Cons**: Less discoverable, doesn't indicate PyInfra integration
- **Rejected**: Too generic and doesn't indicate PyInfra relationship

### Alternative 3: `pyinfra_orbstack_connector`

- **Pros**: Very explicit about being a connector
- **Cons**: Verbose naming, redundant with "connector" in name
- **Rejected**: Too verbose and redundant

## Implementation Notes

- Package is registered as `pyinfra-orbstack` on PyPI
- Uses `src/` layout for modern Python packaging
- Entry point registers the connector as `orbstack` for PyInfra
- Import pattern: `from pyinfra_orbstack.operations.vm import vm_create`

*Note: Implementation details are documented in the project's README.md and pyproject.toml files.*

## References

- [PyInfra Connector Documentation](https://docs.pyinfra.com/en/2.x/api/connectors.html)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Architecture Decision Records](https://github.com/joelparkerhenderson/architecture-decision-record)
