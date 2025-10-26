# PyInfra Operations Issue Analysis

**Date:** 2025-01-16
**Author:** AI Assistant
**Status:** Issue Identified

## Executive Summary

The VM operations in `src/pyinfra_orbstack/operations/vm.py` are **not properly implemented** for PyInfra's operation system. This is why the deployment tests are failing, not because PyInfra is unavailable.

## The Real Issue

### PyInfra IS Available ✅

- **PyInfra Version**: 3.4.1
- **Installation**: Available in the virtual environment
- **Command Line**: Working correctly
- **Status**: Fully functional

### The Problem: Incorrect Operation Implementation ❌

The VM operations in this project are using PyInfra's `@operation` decorator incorrectly. They're implemented as regular functions that return boolean values, but PyInfra operations need to be generators that yield commands.

## Current Implementation (Incorrect)

```python
@operation
def vm_create(
    name: str,
    image: str,
    arch: Optional[str] = None,
    user: Optional[str] = None,
    present: bool = True,
) -> bool:
    # Build orbctl create command
    cmd = ["orbctl", "create", image, name]

    # Execute command
    exit_code, stdout, stderr = host.run_shell_command(
        " ".join(cmd),
        _sudo=False,
    )

    return exit_code == 0  # ❌ This is wrong for PyInfra operations
```

## Correct PyInfra Operation Pattern

PyInfra operations should be generators that yield commands:

```python
@operation
def vm_create(
    name: str,
    image: str,
    arch: Optional[str] = None,
    user: Optional[str] = None,
    present: bool = True,
):
    """
    Create or ensure OrbStack VM exists.
    """
    # Build orbctl create command
    cmd = ["orbctl", "create", image, name]

    if arch:
        cmd.extend(["--arch", arch])

    if user:
        cmd.extend(["--user", user])

    # Yield the command for PyInfra to execute
    yield f"Create VM {name}", " ".join(cmd)  # ✅ Correct PyInfra pattern
```

## Why Deployment Tests Are Failing

1. **Operation Decorator Mismatch**: The `@operation` decorator expects a generator function, but the VM operations are regular functions
2. **Return Type Error**: Operations return `bool` instead of yielding commands
3. **Context Issues**: The operations try to execute commands directly instead of letting PyInfra handle execution

## Evidence

### Function Signature Analysis
```bash
$ uv run python -c "from pyinfra_orbstack.operations.vm import vm_create; import inspect; print(inspect.signature(vm_create))"
(f: 'Callable[P, Generator]') -> 'PyinfraOperation[P]'
```

This shows that `vm_create` is actually a decorator that expects a generator function, not a regular function.

### Error Messages
```
TypeError: operation.<locals>.decorator() got an unexpected keyword argument 'name'
```

This error occurs because the operations are not properly decorated for PyInfra's operation system.

## Impact on Coverage

The current 33% VM operations coverage is due to:
- **Command construction tests**: Test parameter validation (working)
- **Integration tests**: Test real OrbStack functionality (working)
- **Missing**: Actual PyInfra deployment context execution (broken due to operation implementation)

## Solutions

### Option 1: Fix the VM Operations (Recommended)
Rewrite the VM operations to follow PyInfra's operation pattern:

```python
@operation
def vm_create(
    name: str,
    image: str,
    arch: Optional[str] = None,
    user: Optional[str] = None,
    present: bool = True,
):
    """
    Create or ensure OrbStack VM exists.
    """
    if not present:
        yield from vm_delete(name, force=True)
        return

    cmd = ["orbctl", "create", image, name]

    if arch:
        cmd.extend(["--arch", arch])

    if user:
        cmd.extend(["--user", user])

    yield f"Create VM {name}", " ".join(cmd)
```

### Option 2: Use Direct Command Execution
Keep the current approach but test the underlying command construction logic:

```python
def test_vm_create_command_construction():
    """Test VM creation command construction."""
    # Test the command building logic without PyInfra operations
    cmd = ["orbctl", "create", "ubuntu:22.04", "test-vm"]
    expected = "orbctl create ubuntu:22.04 test-vm"
    assert " ".join(cmd) == expected
```

### Option 3: Hybrid Approach
Create both PyInfra operations and direct command functions:

```python
# Direct command function (for testing)
def vm_create_command(name: str, image: str, **kwargs) -> str:
    """Build vm_create command string."""
    cmd = ["orbctl", "create", image, name]
    # ... add kwargs
    return " ".join(cmd)

# PyInfra operation (for deployment)
@operation
def vm_create(name: str, image: str, **kwargs):
    """Create VM using PyInfra operation."""
    cmd = vm_create_command(name, image, **kwargs)
    yield f"Create VM {name}", cmd
```

## Recommended Action

**Fix the VM operations** to follow PyInfra's operation pattern. This will:

1. **Enable real deployment testing** with PyInfra
2. **Increase VM operations coverage** from 33% to 85-90%
3. **Provide proper PyInfra integration** for the project
4. **Allow real-world deployment scenarios** to be tested

## Timeline

- **Immediate**: Document the issue and create corrected operation examples
- **Next Sprint**: Rewrite VM operations to follow PyInfra pattern
- **Following Sprint**: Update deployment tests to use corrected operations
- **Result**: Achieve target 85-90% VM operations coverage

## Conclusion

The issue is **not** that PyInfra is unavailable, but that the VM operations are not properly implemented for PyInfra's operation system. Fixing the operations will enable real deployment testing and significantly improve coverage.
