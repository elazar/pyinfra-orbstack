# ADR-0006: PyInfra Operation Generator Pattern with Command Builders

**Date:** 2025-10-27
**Status:** Accepted
**Deciders:** Project Maintainers
**Type:** Architecture Decision Record

## Context

PyInfra operations use a decorator-based system that transforms functions into operation objects. The project initially implemented operations incorrectly, causing deployment tests to fail.

### Initial Implementation Problems

#### 1. Incorrect Operation Pattern (Functions Returning Booleans)

```python
@operation
def vm_create(
    name: str,
    image: str,
    arch: Optional[str] = None,
) -> bool:
    """Create OrbStack VM."""
    cmd = ["orbctl", "create", image, name]
    if arch:
        cmd.extend(["--arch", arch])

    # ❌ WRONG: Trying to execute directly
    exit_code, stdout, stderr = host.run_shell_command(" ".join(cmd))
    return exit_code == 0  # ❌ WRONG: Operations shouldn't return booleans
```

**Problems**:
- Operations tried to execute commands directly instead of yielding them
- Returned boolean values instead of yielding command strings
- Used `@operation` without parentheses (incorrect decorator usage)
- PyInfra couldn't execute operations due to incorrect pattern

**Error Message**:
```
TypeError: operation.<locals>.decorator() got an unexpected keyword argument 'name'
```

#### 2. Coverage Tool Limitations

Even after fixing the operation pattern, coverage tools showed misleading results:

```python
@operation()
def vm_create(name: str, image: str, arch: Optional[str] = None):
    cmd = ["orbctl", "create", image, name]
    if arch:
        cmd.extend(["--arch", arch])
    yield " ".join(cmd)
```

**Coverage**: 36% (misleading - logic was fully tested but decorator transformation hid it from coverage tools)

### The Core Issue

PyInfra's `@operation()` decorator transforms functions into generator-based operation objects. This transformation:
1. Prevents direct testing of decorated functions
2. Obscures code from coverage analysis
3. Requires PyInfra's execution context to test properly

## Decision

We adopted the **generator pattern with command builder extraction**, separating testable command construction from PyInfra operation wrappers.

### Architecture

#### 1. Correct PyInfra Operation Pattern

Operations must be **generators that yield commands**, not functions that execute commands:

```python
@operation()  # ✅ Parentheses required
def vm_create(
    name: str,
    image: str,
    arch: Optional[str] = None,
    user: Optional[str] = None,
):
    """
    Create OrbStack VM.

    Args:
        name: VM name
        image: VM image (e.g., ubuntu:22.04)
        arch: CPU architecture (arm64 or amd64)
        user: Default user for the VM

    Example:
        pyinfra @orbstack vm.vm_create my-vm ubuntu:22.04 --arch arm64
    """
    # Build command (or use command builder)
    cmd = build_vm_create_command(name, image, arch, user)

    # Yield command for PyInfra to execute
    yield cmd  # ✅ Yield, don't execute
```

**Key Points**:
- Use `@operation()` with parentheses
- Operations are generator functions (use `yield`)
- Yield command strings for PyInfra to execute
- Don't execute commands directly
- Don't return boolean values

#### 2. Command Builder Extraction

Extract command construction logic into separate pure functions:

```python
def build_vm_create_command(
    name: str,
    image: str,
    arch: Optional[str] = None,
    user: Optional[str] = None,
) -> str:
    """
    Build the orbctl create command.

    Args:
        name: VM name
        image: VM image
        arch: CPU architecture
        user: Default user

    Returns:
        Command string for orbctl

    Example:
        >>> build_vm_create_command("test-vm", "ubuntu:22.04", arch="arm64")
        'orbctl create ubuntu:22.04 test-vm --arch arm64'
    """
    cmd = ["orbctl", "create", image, name]

    if arch:
        cmd.extend(["--arch", arch])

    if user:
        cmd.extend(["--user", user])

    return " ".join(cmd)
```

**Benefits of Command Builders**:
- Pure functions - 100% testable
- No decorator complexity
- No PyInfra infrastructure required
- Fast unit tests
- Accurate coverage metrics

#### 3. Operation as Thin Wrapper

Operations become thin wrappers around command builders:

```python
@operation()
def vm_create(name: str, image: str, arch: Optional[str] = None, user: Optional[str] = None):
    """Create OrbStack VM."""
    yield build_vm_create_command(name, image, arch, user)

@operation()
def vm_delete(name: str, force: bool = False):
    """Delete OrbStack VM."""
    yield build_vm_delete_command(name, force)

@operation()
def vm_start(name: str):
    """Start OrbStack VM."""
    yield build_vm_start_command(name)
```

**Pattern**: Operations delegate to command builders, keeping operations simple and maintainable.

#### 4. Testing Strategy

**Unit Tests for Command Builders** (fast, no mocks):
```python
def test_build_vm_create_command():
    """Test basic VM creation command."""
    cmd = build_vm_create_command("test-vm", "ubuntu:22.04")
    assert cmd == "orbctl create ubuntu:22.04 test-vm"

def test_build_vm_create_command_with_arch():
    """Test VM creation with architecture."""
    cmd = build_vm_create_command("test-vm", "ubuntu:22.04", arch="arm64")
    assert cmd == "orbctl create ubuntu:22.04 test-vm --arch arm64"

def test_build_vm_create_command_with_user():
    """Test VM creation with custom user."""
    cmd = build_vm_create_command("test-vm", "ubuntu:22.04", user="admin")
    assert cmd == "orbctl create ubuntu:22.04 test-vm --user admin"
```

**Integration/E2E Tests for Operations** (slower, real infrastructure):
```python
@pytest.mark.integration
def test_vm_create_operation(worker_vm):
    """Test VM creation via PyInfra deployment."""
    # Test in real PyInfra context
    # Verifies operation works with PyInfra's execution engine
```

### Coverage Expectations

| Component | Expected Coverage | Test Method |
|-----------|------------------|-------------|
| Command Builders | 90-100% | Direct unit tests |
| Operations (decorator-wrapped) | 30-50% | Integration/E2E tests |
| Overall Logic | 100% | Command builders fully tested |

**Coverage Reality**:
- Command builders: 100% coverage, directly testable
- Operations: 36% coverage (decorator obscures), but fully tested via integration tests
- **Total functional coverage: 100%** (all logic tested, just not all captured by coverage tools)

## Consequences

### Positive Consequences

1. **Correct PyInfra Integration**: Operations work properly with PyInfra's execution engine
2. **Testable Logic**: Command builders are pure functions, easily tested
3. **Fast Unit Tests**: Test command construction without PyInfra infrastructure (~0.3s for 24 tests)
4. **Accurate Coverage**: Command builders show 100% coverage, reflecting actual testing
5. **Clear Separation**: Command construction (business logic) separated from PyInfra wrapper (framework code)
6. **Easy Maintenance**: Changes to command logic only affect builders
7. **No Mocking Needed**: Command builders don't require PyInfra mocks
8. **Deployment Tests Work**: Operations execute correctly in real PyInfra deployments

### Negative Consequences

1. **More Code**: Each operation requires a command builder function (roughly doubles operation file size)
2. **Two-Step Process**: Must update both builder and operation for changes
3. **Coverage Metrics Look Lower**: Operations show low coverage despite being tested
4. **Indirection**: Extra function call between operation and command construction
5. **Documentation Duplication**: Both builder and operation need docstrings

### Trade-offs

- **Code Simplicity vs. Testability**: Accept more code (builders) for dramatically better testability
- **Coverage Numbers vs. Actual Testing**: Accept lower coverage percentages for decorator-wrapped operations rather than pursue meaningless 100%
- **Direct Testing vs. Integration Testing**: Fast unit tests for logic + integration tests for PyInfra integration
- **DRY vs. Separation of Concerns**: Some duplication (builders + operations) for clear separation

## Alternatives Considered

### Alternative 1: Test Operations Directly Without Extraction

**Rejected** - Can't test decorator-wrapped functions without PyInfra's execution context. Requires slow integration tests for everything.

### Alternative 2: Mock the Decorator

```python
@patch('pyinfra.api.operation', lambda: lambda f: f)
def test_vm_create():
    result = vm_create("test", "ubuntu:22.04")
    assert result == "orbctl create ubuntu:22.04 test"
```

**Rejected** - Tests the wrong thing (function without decorator). Decorator behavior is critical to operation functionality. Creates false confidence.

### Alternative 3: Coverage Pragmas to Hide Low Coverage

```python
@operation()  # pragma: no cover
def vm_create(...):
    ...
```

**Rejected** - Hides untested code rather than solving the problem. Doesn't improve actual testing. Masks real coverage gaps.

### Alternative 4: Complex Command Construction Within Operations

Keep all logic in operations without extraction.

**Rejected** - Can't unit test complex logic without PyInfra infrastructure. Slow tests. No isolation. Complex operations are hard to test thoroughly.

### Alternative 5: Integration Tests Only

Skip unit tests entirely, test everything via PyInfra deployments.

**Rejected** - Too slow for development iteration (minutes instead of seconds). Can't test edge cases efficiently. Debugging is harder.

## Implementation Notes

### File Organization

```
src/pyinfra_orbstack/operations/
├── __init__.py
└── vm.py
    ├── build_vm_create_command()      # Command builder
    ├── vm_create()                     # Operation (uses builder)
    ├── build_vm_delete_command()
    ├── vm_delete()
    ├── ...                             # Other command builders and operations
```

### Command Builder Conventions

1. **Naming**: `build_{operation_name}_command`
2. **Parameters**: Match operation parameters exactly
3. **Return Type**: `str` (command string) or `List[str]` (command parts)
4. **Documentation**: Full docstring with examples
5. **Testing**: Comprehensive unit tests for all parameter combinations

### Operation Conventions

1. **Decorator**: Always `@operation()` with parentheses
2. **Generator**: Use `yield` to return commands
3. **Documentation**: PyInfra-style docstrings with examples
4. **Delegation**: Call command builder, yield result
5. **Complexity**: Keep operations thin (3-5 lines max)

### Testing Approach

1. **Unit Tests**: Test command builders directly (fast, comprehensive)
2. **Integration Tests**: Test operations work with PyInfra (medium speed)
3. **E2E Tests**: Test operations in real deployment scenarios (slow, realistic)

## References

- [PyInfra Operations Issue Analysis](../dev-journal/20250116-pyinfra-operations-issue-analysis.md) - Discovery of incorrect operation pattern
- [Improving Decorator Coverage](../dev-journal/20251021-improving-decorator-coverage.md) - Command builder extraction rationale
- [Test Implementation Analysis](../dev-journal/20250817-test-implementation-analysis.md) - Insights on PyInfra operation requirements
- [PyInfra Operations Documentation](https://docs.pyinfra.com/en/2.x/operations.html) - Official PyInfra operation patterns
- [PyInfra API Documentation](https://docs.pyinfra.com/en/2.x/api/operations.html) - Operation decorator API

## Related ADRs

- [ADR-0003: Multi-Level Testing Strategy](0003-multi-level-testing-strategy.md) - Testing strategy that uses command builder extraction for unit tests
- [ADR-0001: Package Namespace Structure](0001-package-namespace.md) - Package organization that includes operations module
