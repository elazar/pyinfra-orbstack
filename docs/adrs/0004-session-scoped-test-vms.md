# ADR-0004: Session-Scoped Test VM Management

**Date:** 2025-10-27
**Status:** Accepted
**Deciders:** Project Maintainers
**Type:** Architecture Decision Record

## Context

The PyInfra OrbStack Connector test suite initially created and destroyed VMs for every test that needed one. This approach had severe performance problems:

### Initial Performance Issues

- **Test Duration**: 20+ minutes for full suite (350+ seconds of VM operations for 25 seconds of actual testing)
- **Efficiency**: Only 6.7% efficient (25s testing / 375s total time)
- **Resource Usage**: 100+ VM create/delete operations per test run
- **Flakiness**: Parallel test execution caused VM name collisions (multiple tests using `test-vm-{timestamp}` could start in the same second)
- **OrbStack Stability**: Heavy VM churn caused OrbStack timeouts and failures

### The Core Problem

```python
# Original pattern (per-test VM creation)
def test_vm_info():
    vm_name = f"test-vm-{int(time.time())}"  # Collision-prone!
    create_vm(vm_name)  # 60 seconds
    # ... test logic (5 seconds)
    delete_vm(vm_name)  # 10 seconds
    # Total: 75 seconds per test
```

With 100 tests, this resulted in:
- 100 VM creations × 60s = 6000s (100 minutes)
- 100 tests × 5s = 500s (8.3 minutes)
- 100 VM deletions × 10s = 1000s (16.7 minutes)
- **Total: 125 minutes for tests that do 8.3 minutes of actual work**

## Decision

We implemented a **session-scoped worker VM strategy** where each pytest worker gets one persistent VM for the entire test session, with specialized handling for lifecycle tests.

### Architecture

#### 1. Worker VM Pattern (98% of Tests)

Each pytest worker (when running with `-n auto`) gets one VM that persists for the entire session:

```python
@pytest.fixture(scope="session")
def worker_vm():
    """
    Fixture providing a persistent VM for the current pytest worker.

    Each worker gets one VM that is reused across all tests in that worker.
    VM is created on first use and cleaned up at session end.
    """
    vm_name = get_worker_vm()
    yield vm_name
    # Cleanup handled by session cleanup
```

**Implementation**:
```python
def get_worker_vm() -> str:
    """Get or create the worker VM for this pytest worker."""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    pid = os.getpid()

    # Check if we already have a worker VM
    if worker_id in _worker_vms:
        return _worker_vms[worker_id]

    # Create new worker VM
    vm_name = f"pytest-worker-{worker_id}-{pid}"
    if create_vm_with_retry(vm_name, "ubuntu:22.04"):
        _worker_vms[worker_id] = vm_name
        register_test_vm_for_cleanup(vm_name)
        return vm_name

    raise RuntimeError(f"Failed to create worker VM: {vm_name}")
```

#### 2. One-Off VMs for Lifecycle Tests (2% of Tests)

Tests that specifically test VM lifecycle (create, delete, start, stop) need fresh VMs:

```python
def create_test_vm(reuse_worker_vm: bool = True) -> str:
    """
    Create or get a test VM.

    Args:
        reuse_worker_vm: If True, return persistent worker VM (default).
                        If False, create new one-off VM.
    """
    if reuse_worker_vm:
        return get_worker_vm()  # Fast! Reuses existing VM

    # Create one-off VM for lifecycle tests
    timestamp = int(time.time())
    pid = os.getpid()
    random_suffix = random.randint(1000, 9999)
    vm_name = f"{TEST_VM_PREFIX}{timestamp}-{pid}-{random_suffix}"

    # Create, start, and wait for readiness
    if create_vm_with_retry(vm_name, "ubuntu:22.04"):
        return vm_name

    raise RuntimeError(f"Failed to create test VM: {vm_name}")
```

#### 3. Unique VM Naming to Prevent Collisions

**Original Problem**: `test-vm-{timestamp}` caused collisions in parallel execution

**Solution**: Three-component unique naming
```python
vm_name = f"{prefix}{timestamp}-{pid}-{random}"
# Example: test-vm-1698765432-12345-7890
```

Components:
- **Timestamp**: Second-level uniqueness
- **PID**: Process-level uniqueness (different pytest workers)
- **Random suffix**: Collision prevention within same second/process

#### 4. Comprehensive Cleanup Strategy

**Session Start**: Clean up orphaned VMs from previous failed runs
```python
def cleanup_orphaned_test_vms():
    """Clean up test VMs from previous runs."""
    test_prefixes = [
        "test-vm-",
        "e2e-test-vm-",
        "e2e-ops-vm-",
        "deploy-test-vm-",
        "pytest-worker-",
    ]
    # Find and delete orphaned VMs
```

**Session End**: Clean up all tracked VMs
```python
def cleanup_test_vms():
    """Clean up all tracked VMs at session end."""
    for vm_name in _test_vms_created:
        delete_vm_with_retry(vm_name)
```

**Automatic Registration**: VMs auto-register for cleanup
```python
def create_vm_with_retry(vm_name: str, ..., auto_cleanup: bool = True) -> bool:
    if auto_cleanup:
        register_test_vm_for_cleanup(vm_name)
    # ... create VM ...
```

### Performance Impact

**Before Session-Scoped VMs**:
```
100 tests × (60s create + 5s test + 10s delete) = 7,500 seconds (125 minutes)
Efficiency: 8% (500s testing / 7,500s total)
```

**After Session-Scoped VMs** (4 workers):
```
4 workers × 60s create = 240s
100 tests × 5s = 500s
4 workers × 10s delete = 40s
Total: 780 seconds (13 minutes)
Efficiency: 64% (500s testing / 780s total)
```

**Savings: 92% reduction in VM operations, 90% reduction in test time**

## Consequences

### Positive Consequences

1. **Dramatic Speed Improvement**: Test suite runtime reduced from 20+ minutes to ~10 minutes
2. **Better Resource Utilization**: 92% fewer VM operations (4 creates vs. 100+)
3. **Improved Stability**: Fewer concurrent VMs reduces OrbStack contention and timeouts
4. **Collision Prevention**: Unique naming eliminates parallel execution failures
5. **Cleaner Test Runs**: Automatic cleanup ensures no leftover VMs
6. **Maintained Coverage**: 100% test coverage maintained despite optimization
7. **Developer Experience**: Faster feedback loop during development
8. **CI Efficiency**: Reduced CI time and resource consumption

### Negative Consequences

1. **Test Isolation Concerns**: Tests share VMs, so state pollution is possible (mitigated by VM reset between tests if needed)
2. **Debugging Complexity**: Worker VM failures affect multiple tests
3. **Implementation Complexity**: More sophisticated VM management code
4. **Memory of Test State**: Worker VMs may accumulate state across tests (files, processes)

### Trade-offs

- **Speed vs. Isolation**: Chose speed (shared VMs) over perfect isolation (per-test VMs)
  - **Mitigation**: Lifecycle tests still get fresh VMs when needed via `reuse_worker_vm=False`
- **Simplicity vs. Performance**: More complex code for dramatic performance gains
- **Automatic vs. Explicit Cleanup**: Automatic cleanup requires tracking infrastructure but prevents forgotten VMs

## Alternatives Considered

### Alternative 1: Per-Test VM Creation (Original Approach)

**Rejected** - Test suite took 20+ minutes, making development iteration painful. 6.7% efficiency was unacceptable.

### Alternative 2: Single Shared VM for All Tests

```python
@pytest.fixture(scope="session")
def shared_vm():
    vm = create_vm()
    yield vm
    delete_vm(vm)
```

**Rejected** - Would serialize all tests (no parallelism). Single VM becomes bottleneck and single point of failure.

### Alternative 3: Test-Type-Specific Shared VMs

```python
@pytest.fixture(scope="session")
def integration_vm():  # One VM for all integration tests
@pytest.fixture(scope="session")
def e2e_vm():          # One VM for all E2E tests
```

**Rejected** - Doesn't support parallel execution. Multiple tests would compete for same VM.

### Alternative 4: VM Pooling with Locking

Create a pool of VMs and use locks to ensure only one test uses a VM at a time.

**Rejected** - Complex to implement. Pytest-xdist already provides worker isolation; leveraging that is simpler.

### Alternative 5: Container-Based Testing Instead of VMs

Use Docker containers instead of OrbStack VMs for testing.

**Rejected** - Connector specifically targets OrbStack VMs. Testing against containers wouldn't validate real behavior.

## Implementation Notes

### Files Modified

- `tests/conftest.py`: Added `get_worker_vm()`, `worker_vm` fixture, `cleanup_worker_vms()`
- `tests/test_utils.py`: Updated `create_test_vm()` with `reuse_worker_vm` parameter
- All test files: Updated to use `worker_vm` fixture or `create_test_vm(reuse_worker_vm=False)` as appropriate

### Usage Patterns

**Most tests (operational tests)**:
```python
def test_vm_info(worker_vm):
    """Test VM info retrieval using shared worker VM."""
    info = get_vm_info(worker_vm)
    assert info is not None
```

**Lifecycle tests**:
```python
def test_vm_creation():
    """Test VM creation (needs fresh VM)."""
    vm_name = create_test_vm(reuse_worker_vm=False)
    assert vm_exists(vm_name)
    # Cleanup automatic via tracking
```

### Pytest Worker Compatibility

Works seamlessly with pytest-xdist:
```bash
pytest -n auto              # Parallel: Each worker gets one VM
pytest -n 4                 # 4 workers: 4 worker VMs created
pytest                      # Single worker: 1 worker VM created
```

## References

- [Test VM Management Implementation Summary](../dev-journal/20251025-test-vm-management-implementation-summary.md) - Complete implementation details
- [Test VM Parallel Optimization](../dev-journal/20251025-test-vm-parallel-optimization.md) - Analysis of parallel execution problems
- [Test VM Management Complete Solution](../dev-journal/20251025-test-vm-management-complete-solution.md) - Collision prevention and cleanup strategy
- [Test Optimization Phase 1](../dev-journal/20251021-test-optimization-phase1.md) - Initial session-scoped fixture implementation
- [Test Cleanup Improvements](../dev-journal/20251025-test-cleanup-improvements.md) - Cleanup mechanism analysis

## Related ADRs

- [ADR-0003: Multi-Level Testing Strategy](0003-multi-level-testing-strategy.md) - Testing architecture that benefits from session-scoped VMs
- [ADR-0005: Intelligent Retry Logic for OrbStack Operations](0005-intelligent-retry-logic.md) - Retry logic used in VM creation for reliability
