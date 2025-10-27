# ADR-0003: Multi-Level Testing Strategy

**Date:** 2025-10-27
**Status:** Accepted
**Deciders:** Project Maintainers
**Type:** Architecture Decision Record

## Context

The PyInfra OrbStack Connector requires testing at multiple levels due to its nature as a bridge between PyInfra's operation framework and OrbStack's CLI. Early development faced challenges with:

1. **Decorator-Wrapped Operations**: PyInfra's `@operation()` decorator transforms functions into generators, causing coverage tools to miss actual command construction logic (showing 36% coverage when logic was actually fully tested).
2. **External Dependencies**: Tests depend on OrbStack CLI and VM infrastructure, which are slow and network-dependent.
3. **Test Duration**: Initial test suite took 20+ minutes due to repeated VM creation/deletion.
4. **Coverage Metrics**: Standard coverage tools gave misleading results for decorator-heavy code.

A comprehensive testing strategy was needed to balance test speed, coverage accuracy, reliability, and maintainability.

## Decision

We adopted a **three-tier testing architecture** with distinct test types, each serving specific purposes:

### Test Type Definitions

#### 1. Unit Tests (~80 tests, <20 seconds)
- **Scope**: Individual components in isolation
- **Dependencies**: Mocked (subprocess, OrbStack CLI)
- **Marker**: `@pytest.mark.unit`
- **Files**: `test_connector.py`, `test_operations.py`, `test_orbstack_cli_mocks.py`, `test_vm_operations_unit.py`, `test_vm_command_builders.py`
- **Purpose**: Test logic without external dependencies

#### 2. Integration Tests (~45 tests, 3-5 minutes)
- **Scope**: Component interactions
- **Dependencies**: Real OrbStack VMs (session-scoped, shared)
- **Marker**: `@pytest.mark.integration`
- **Files**: `test_integration.py`, `test_vm_operations_integration.py`, `test_pyinfra_deployment.py`
- **Purpose**: Verify components work together with real infrastructure

#### 3. End-to-End Tests (~36 tests, 5-10 minutes)
- **Scope**: Complete workflows and real-world scenarios
- **Dependencies**: Real OrbStack VMs, full PyInfra deployment context
- **Marker**: `@pytest.mark.e2e`
- **Files**: `test_e2e.py`, `test_pyinfra_operations_e2e.py`, `test_connector_coverage_e2e.py`
- **Purpose**: Validate complete user workflows

### Command Builder Extraction Pattern

To address decorator coverage issues, we separate command construction from operations:

```python
# Testable command builder (pure function)
def build_vm_create_command(name: str, image: str, arch: Optional[str] = None) -> str:
    """Build the orbctl create command."""
    cmd = ["orbctl", "create", image, name]
    if arch:
        cmd.extend(["--arch", arch])
    return " ".join(cmd)

# Operation (thin wrapper)
@operation()
def vm_create(name: str, image: str, arch: Optional[str] = None):
    """Create OrbStack VM."""
    yield build_vm_create_command(name, image, arch)
```

**Benefits**:
- Command builders: 100% testable without decorator complexity
- Operations: Thin wrappers (low coverage is expected and acceptable)
- Accurate coverage metrics (65% vs. misleading 36%)
- Fast unit tests without PyInfra infrastructure

### Test Markers for Selective Execution

```python
# pytest.ini
markers = [
    "unit: Unit tests with mocked dependencies (fast)",
    "integration: Integration tests with shared VMs (medium speed)",
    "e2e: End-to-end tests with full workflows (slow)",
    "expensive: Tests that create new VMs (very slow)",
]
```

**Usage**:
```bash
pytest -m unit                    # Fast: unit tests only (~20s)
pytest -m "integration and not expensive"  # Medium: integration with shared VMs
pytest -m e2e                     # Slow: end-to-end tests
pytest                            # Full suite (~10-15 minutes)
```

### Coverage Expectations

We accept different coverage percentages for different components based on their nature:

| Component | Expected Coverage | Rationale |
|-----------|------------------|-----------|
| Command Builders | 90-100% | Pure functions, fully testable |
| Connector | 65-80% | Some paths only executed in E2E context |
| Operations | 30-50% | Decorator-wrapped, tested via integration/E2E |
| Overall Project | 90%+ | High overall coverage despite decorator limitations |

## Consequences

### Positive Consequences

1. **Accurate Coverage Metrics**: Separating command builders from operations provides realistic coverage measurements
2. **Fast Feedback Loop**: Unit tests run in <20 seconds, enabling rapid development
3. **Comprehensive Testing**: Three-tier approach catches issues at appropriate levels
4. **Selective Execution**: Developers can run fast tests during development, full suite in CI
5. **Clear Test Organization**: Each test file has a clear purpose and scope
6. **Maintainable Tests**: Command builders are simple to test without mocking PyInfra infrastructure
7. **Realistic Integration Testing**: Real VMs catch issues that mocks would miss

### Negative Consequences

1. **More Test Code**: Command builders add extra functions and tests
2. **Learning Curve**: Developers must understand when to write unit vs. integration vs. E2E tests
3. **Infrastructure Requirements**: Integration and E2E tests require OrbStack installation
4. **Test Duration**: Full suite still takes 10-15 minutes despite optimizations
5. **Coverage Tool Limitations**: Standard coverage tools still underreport decorator-wrapped code

### Trade-offs

- **Speed vs. Realism**: Unit tests are fast but use mocks; integration/E2E tests are slower but catch real issues
- **Coverage Numbers vs. Actual Testing**: Accept lower coverage percentages for decorator-wrapped code rather than pursue meaningless 100%
- **Test Complexity vs. Accuracy**: Command builder extraction adds code but provides accurate testability
- **Development Speed vs. Confidence**: Fast unit tests for quick iteration, slower E2E tests for confidence

## Alternatives Considered

### Alternative 1: Integration Tests Only

**Rejected** - Too slow for development iteration (every test run would take 10+ minutes). Would also miss logic errors that unit tests catch quickly.

### Alternative 2: Unit Tests Only with Heavy Mocking

**Rejected** - Would miss integration issues between PyInfra and OrbStack. Mocking PyInfra's operation framework is complex and fragile.

### Alternative 3: Coverage Pragmas to Hide Decorator Code

```python
@operation()  # pragma: no cover
def vm_create(...):
    ...
```

**Rejected** - Hides untested code rather than solving the problem. Doesn't improve actual testing quality.

### Alternative 4: Monkey Patching Decorators in Tests

```python
@patch('pyinfra.api.operation', lambda: lambda f: f)
def test_vm_create():
    ...
```

**Rejected** - Tests the wrong thing (function without decorator). Decorator behavior is critical to operation functionality.

### Alternative 5: Single Test Level (Mixed Approach)

**Rejected** - Makes it impossible to run fast tests during development. All tests would be slow and require OrbStack infrastructure.

## Implementation Notes

- **Test File Naming**: Use `test_*_unit.py`, `test_*_integration.py`, `test_*_e2e.py` for clarity
- **Command Builders**: Located in `src/pyinfra_orbstack/operations/vm.py` alongside operations
- **Test Utilities**: Shared helpers in `tests/test_utils.py` and `tests/conftest.py`
- **CI Configuration**: Run all test levels in CI; developers run unit tests locally for speed
- **Documentation**: Test running instructions in `docs/dev-journal/20251021-running-tests.md`

## References

- [Testing and Coverage Methodology](../dev-journal/20251021-testing-and-coverage-methodology.md) - Comprehensive coverage analysis
- [Improving Decorator Coverage](../dev-journal/20251021-improving-decorator-coverage.md) - Command builder extraction rationale
- [Test Analysis and Deployment Evaluation](../dev-journal/20250116-test-analysis-and-deployment-evaluation.md) - Test redundancy analysis and multi-level approach
- [PyInfra Operations Documentation](https://docs.pyinfra.com/en/2.x/operations.html) - PyInfra operation patterns
- [Pytest Documentation on Markers](https://docs.pytest.org/en/stable/example/markers.html) - Test marker usage

## Related ADRs

- [ADR-0006: PyInfra Operation Generator Pattern with Command Builders](0006-operation-generator-pattern.md) - Details the command builder extraction pattern used in unit testing
