# Test Optimization - Phase 1 Implementation

**Date**: 2025-01-21
**Status**: Implemented
**Goal**: Reduce test runtime from 21 min to ~8 min while maintaining coverage

## Changes Implemented

### 1. Session-Scoped Shared VM Fixtures

Created three session-scoped VM fixtures in `conftest.py` that are created once per test session and reused across multiple tests:

- **`shared_vm_basic`**: Basic Ubuntu 22.04 VM for general testing
- **`shared_vm_with_user`**: VM with custom user (`testuser`)
- **`shared_vm_with_arch`**: VM with specific architecture (`arm64`)

**Benefits**:
- VMs created once per session instead of once per test
- Reduces ~50+ VM creations to just 3
- Automatic cleanup via existing `_test_vms_created` tracking

**Usage Example**:
```python
def test_vm_info(shared_vm_basic):
    """Test using shared VM instead of creating new one."""
    result = get_vm_info(shared_vm_basic)
    assert result is not None

def test_command_execution(shared_vm_basic):
    """Reuse same VM for command testing."""
    result = run_command(shared_vm_basic, "echo test")
    assert result.success
```

### 2. Test Markers for Selective Execution

Added `expensive` marker to pytest configuration:

```toml
markers = [
    "expensive: mark tests that create VMs (use -m 'not expensive' to skip)",
]
```

**Usage**:
```python
@pytest.mark.expensive
def test_vm_creation_with_params():
    """This test creates a VM and is marked expensive."""
    pass
```

### 3. Fast Test Execution Options

**Run tests excluding expensive VM creations**:
```bash
pytest -m "not expensive"  # Skip VM creation tests
pytest -c .pytest-fast.ini  # Run only unit tests (~19 seconds)
```

**Run full suite**:
```bash
pytest  # All tests including expensive ones (~21 min → target ~8 min)
```

## Next Steps for Developers

### Migrating Existing Tests

**Before (creates new VM each time)**:
```python
def test_something():
    vm_name = f"test-vm-{int(time.time())}"
    create_vm_with_retry("ubuntu:22.04", vm_name)
    # ... test logic ...
    delete_vm_with_retry(vm_name)
```

**After (reuses shared VM)**:
```python
def test_something(shared_vm_basic):
    """Use shared VM - faster and no cleanup needed."""
    # ... test logic using shared_vm_basic ...
    pass
```

### When to Create New VMs

Only create new VMs when:
1. Testing VM creation/deletion specifically
2. Testing requires VM modification that affects other tests
3. Testing destructive operations

For these cases, mark the test as expensive:
```python
@pytest.mark.expensive
def test_vm_deletion():
    """Creates and deletes VM - marked expensive."""
    pass
```

## Expected Impact

### Runtime Reduction

**Before**:
- Full suite: ~21 minutes
- Unit tests: ~19 seconds
- ~50+ VM creations per run

**After (estimated)**:
- Full suite: ~8 minutes (62% reduction)
- Fast tests (`-m "not expensive"`): ~3 minutes
- Unit tests: ~19 seconds (unchanged)
- Only 3-5 VM creations per run

### Coverage Maintained

- Target: 80%+ coverage maintained
- Connector: 99%
- Operations: 36% (PyInfra decorator limitations)
- Overall: 80%

## CI/CD Recommendations

```yaml
# .github/workflows/test.yml
- name: Fast tests (PR)
  run: pytest -m "not expensive"
  if: github.event_name == 'pull_request'

- name: Full suite (main branch)
  run: pytest
  if: github.ref == 'refs/heads/main'
```

## Future Optimizations (Phase 2)

Potential further improvements:
1. Extract command-building logic from operations for unit testing
2. Parameterized tests to reduce duplication
3. Mock-based operation testing where feasible
4. Record/replay for deterministic testing

**Target**: 95%+ coverage with ~5 min runtime
