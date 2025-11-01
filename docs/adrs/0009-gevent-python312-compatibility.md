# ADR-0009: Gevent and Python 3.12 Compatibility

**Date:** 2025-11-01
**Status:** Accepted
**Deciders:** Project Maintainers
**Type:** Architecture Decision Record

## Context

When running PyInfra operations with the pyinfra_orbstack connector on Python 3.12, users may encounter repeated threading warnings:

```
Exception ignored in: <bound method _ForkHooks.after_fork_in_child of <gevent.threading._ForkHooks object at 0x...>>
Traceback (most recent call last):
  File ".../gevent/threading.py", line 398, in after_fork_in_child
    assert not thread.is_alive()
               ^^^^^^^^^^^^^^^^^
  File ".../threading.py", line 1476, in is_alive
    assert not self._is_stopped and self._started.is_set()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError:
```

### Investigation Results

#### Root Cause Analysis

1. **PyInfra's Gevent Usage**: PyInfra CLI (`pyinfra_cli/__init__.py`) applies `gevent.monkey.patch_all()` at startup, which patches the standard library's `threading` and `subprocess` modules.

2. **Python 3.12 Changes**: Python 3.12 introduced changes to the threading module's internals that affect how thread state is managed and checked.

3. **Gevent Compatibility**: Gevent 25.5.1's fork hooks (`_ForkHooks.after_fork_in_child`) contain assertions that fail with Python 3.12's threading implementation:
   - The assertion `assert not thread.is_alive()` fails
   - This check was designed to ensure no threads are alive in child processes after fork
   - Python 3.12's `is_alive()` implementation triggers a nested assertion that fails

4. **When It Occurs**: The warnings appear during:
   - Host connection phase (when connector calls `subprocess.run()` to verify VM exists)
   - Operation preparation phase (when commands are executed via `orbctl`)
   - Any subprocess invocation after gevent monkey patching

5. **Impact**:
   - **Non-blocking**: These are warnings, not errors - operations continue successfully
   - **Visual noise**: Repeated warnings clutter output during operations
   - **No functional impact**: All connector operations work correctly despite the warnings

#### Connector Analysis

The pyinfra_orbstack connector does NOT:
- Create any threads explicitly
- Use threading primitives
- Maintain persistent connections requiring thread management
- Share state across forks

The connector ONLY:
- Calls `subprocess.run()` for OrbStack CLI operations
- Uses standard Python file I/O
- Maintains simple state in instance variables

This confirms the issue is **not in the connector code** but in the interaction between:
- PyInfra's gevent monkey patching
- Python 3.12's threading changes
- Gevent's fork hook assertions

## Decision

**We will document this as a known compatibility issue with workarounds rather than modify the connector.**

Rationale:
1. **Not a connector bug**: The connector code is correct and thread-safe
2. **Upstream issue**: The problem is in gevent's compatibility with Python 3.12
3. **Non-blocking**: Operations complete successfully despite warnings
4. **No safe connector fix**: We cannot prevent PyInfra from applying monkey patching
5. **Temporary issue**: Likely to be fixed in future gevent releases

## Consequences

### Positive

- **No code changes needed**: Connector remains simple and maintainable
- **No performance impact**: Avoiding unnecessary complexity or workarounds
- **Transparency**: Users understand this is a known upstream issue
- **Future-proof**: When gevent fixes the issue, no changes needed

### Negative

- **Warning noise**: Users see repeated warnings during operations
- **Perceived instability**: Warnings may concern users unfamiliar with the issue
- **Support burden**: Need to explain the issue to users

### Workarounds Provided

We provide several workarounds for users who want to eliminate the warnings:

#### Option 1: Suppress Warnings (Recommended)

Set the Python warning filter to ignore these specific warnings:

```bash
export PYTHONWARNINGS="ignore::AssertionError"
```

Or in code:
```python
import warnings
warnings.filterwarnings("ignore", category=AssertionError)
```

#### Option 2: Use Python 3.11

Downgrade to Python 3.11 where this issue doesn't occur:

```bash
pyenv install 3.11.10
pyenv local 3.11.10
```

#### Option 3: Wait for Gevent Update

Monitor the gevent project for fixes:
- Issue: https://github.com/gevent/gevent/issues/2037
- This is a known issue being tracked by the gevent team

#### Option 4: Use Alternative Execution Context

If running standalone scripts (not using PyInfra CLI), you can avoid monkey patching:

```python
# Don't import pyinfra_cli which triggers monkey patching
# Import only what you need from pyinfra.api
```

However, this won't work with the `pyinfra` CLI command.

## Alternatives Considered

### Alternative 1: Modify Connector to Use gevent.subprocess

**Description**: Replace `subprocess.run()` with `gevent.subprocess` calls.

**Rejected because**:
- Adds gevent dependency to connector (coupling)
- Doesn't actually fix the root cause
- May introduce other compatibility issues
- Connector should be independent of PyInfra's gevent usage

### Alternative 2: Implement Custom Fork Safety

**Description**: Add fork-safe wrappers around subprocess calls.

```python
def _fork_safe_subprocess_run(cmd, **kwargs):
    # Attempt to work around gevent fork issues
    ...
```

**Rejected because**:
- Adds significant complexity
- Cannot reliably work around gevent's monkey patching
- May introduce subtle bugs
- Maintains code that fights against upstream behavior

### Alternative 3: Disable Gevent Monkey Patching

**Description**: Try to selectively undo or avoid gevent patching.

**Rejected because**:
- PyInfra requires gevent patching for its operation
- Cannot be controlled from connector code
- Would break PyInfra's concurrent execution model
- Not within connector's scope of control

### Alternative 4: Pin to Older Gevent Version

**Description**: Require users to use an older gevent version.

**Rejected because**:
- Older versions may have security issues
- Conflicts with PyInfra's gevent dependency
- Doesn't solve the problem, just delays it
- Users should use latest stable versions

## Monitoring

We will monitor the following for resolution:

1. **Gevent Issues**: Track https://github.com/gevent/gevent/issues/2037
2. **PyInfra Updates**: Check if PyInfra addresses this in future releases
3. **Python Changes**: Monitor if Python 3.13+ changes affect this
4. **User Reports**: Track feedback on whether this impacts users

## Documentation

This issue is documented in:
- This ADR (comprehensive technical analysis)
- [User Guide: Known Limitations](../user-guide/known-limitations.md) (user-facing summary)
- [User Guide: Troubleshooting](../user-guide/troubleshooting.md) (workarounds)

## References

- [Gevent Issue #2037](https://github.com/gevent/gevent/issues/2037) - Python 3.13 threading compatibility
- [HydroShare Issue #5949](https://github.com/hydroshare/hydroshare/issues/5949) - Similar issue reported
- [Gevent Threading Source](https://python-gevent.readthedocs.io/_modules/gevent/threading.html) - Fork hooks implementation
- [PyInfra Gevent Usage](https://github.com/Fizzadar/pyinfra) - PyInfra's gevent dependency

## Related ADRs

- None (this is the first ADR addressing runtime compatibility)

## Review Schedule

- **Next Review**: When gevent releases version with Python 3.12+ fix
- **Or**: If PyInfra changes its gevent usage
- **Or**: If user reports indicate this is a significant issue
