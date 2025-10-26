# Test VM Management - Parallel Optimization Analysis

## Current Problem: Wasteful VM Lifecycle

### What Happens Now (Inefficient)

```text
Test Runner (PID 12345) starts
├─ Worker 1 (PID 12346)
│  ├─ test_a: create VM (60s) → use VM (5s) → delete VM (10s)
│  ├─ test_b: create VM (60s) → use VM (5s) → delete VM (10s)
│  └─ test_c: create VM (60s) → use VM (5s) → delete VM (10s)
│
├─ Worker 2 (PID 12347)
│  ├─ test_d: create VM (60s) → use VM (5s) → delete VM (10s)
│  └─ test_e: create VM (60s) → use VM (5s) → delete VM (10s)
│
└─ Cleanup at end: (nothing left to clean up)

Total VM operations: 5 creates + 5 deletes = 10 operations
Total time wasted: 5 × 60s (create) + 5 × 10s (delete) = 350 seconds
Actual test time: 5 × 5s = 25 seconds
Efficiency: 25s / 375s = 6.7%
```

**Problem:** Each test creates and deletes a VM, even though VMs are identical (ubuntu:22.04).

## Better Approach: VM Pool with Worker Affinity

### Optimized Design

```text
Test Runner (PID 12345) starts
├─ Worker 1 (PID 12346)
│  ├─ Create worker VM once: worker-1-vm (60s)
│  ├─ test_a: reuse worker-1-vm (5s)
│  ├─ test_b: reuse worker-1-vm (5s)
│  └─ test_c: reuse worker-1-vm (5s)
│  └─ Keep VM alive until runner terminates
│
├─ Worker 2 (PID 12347)
│  ├─ Create worker VM once: worker-2-vm (60s)
│  ├─ test_d: reuse worker-2-vm (5s)
│  └─ test_e: reuse worker-2-vm (5s)
│  └─ Keep VM alive until runner terminates
│
└─ Cleanup at end: delete worker-1-vm + worker-2-vm

Total VM operations: 2 creates + 2 deletes = 4 operations
Total time: 2 × 60s (create) + 2 × 10s (delete) = 140 seconds
Actual test time: 5 × 5s = 25 seconds
Efficiency: 25s / 165s = 15.2%

Time saved: 350s - 140s = 210 seconds (60% reduction!)
```

## Implementation Strategy

### Approach 1: Session-Scoped Worker VMs (Recommended)

Each pytest worker gets one VM for the entire session:

```python
# tests/conftest.py

import os
import pytest
from tests.test_utils import create_vm_with_retry, delete_vm_with_retry, start_vm_with_retry

# Track worker VMs (keyed by worker PID)
_worker_vms = {}
_worker_vm_lock = None  # Will use threading.Lock if needed

def get_worker_vm() -> str:
    """
    Get or create a VM for the current pytest worker.

    Each worker gets one persistent VM for the entire test session.
    VMs are cleaned up when the test runner terminates.

    Returns:
        VM name for this worker
    """
    worker_pid = os.getpid()

    # Check if this worker already has a VM
    if worker_pid in _worker_vms:
        return _worker_vms[worker_pid]

    # Create a new VM for this worker
    timestamp = int(time.time())
    vm_name = f"pytest-worker-{worker_pid}-{timestamp}"

    print(f"\n[Worker {worker_pid}] Creating session VM: {vm_name}")

    if not create_vm_with_retry(
        image="ubuntu:22.04",
        vm_name=vm_name,
        auto_cleanup=True,
    ):
        raise RuntimeError(f"Failed to create worker VM: {vm_name}")

    time.sleep(5)

    if not start_vm_with_retry(vm_name):
        delete_vm_with_retry(vm_name, force=True)
        raise RuntimeError(f"Failed to start worker VM: {vm_name}")

    time.sleep(5)

    # Cache for this worker
    _worker_vms[worker_pid] = vm_name

    print(f"[Worker {worker_pid}] Session VM ready: {vm_name}")
    return vm_name


@pytest.fixture(scope="session")
def worker_vm():
    """
    Fixture providing a persistent VM for the current pytest worker.

    The VM is created once per worker and reused across all tests
    in that worker. Cleaned up when the test session ends.

    Example:
        def test_something(worker_vm):
            # worker_vm is ready to use
            result = subprocess.run(
                ["orbctl", "info", worker_vm, "--format", "json"],
                ...
            )
    """
    vm_name = get_worker_vm()
    yield vm_name
    # Cleanup handled by session cleanup


def cleanup_worker_vms():
    """Clean up worker VMs at session end."""
    if not _worker_vms:
        return

    print(f"\n\nCleaning up {len(_worker_vms)} worker VMs...")
    for worker_pid, vm_name in _worker_vms.items():
        print(f"[Worker {worker_pid}] Deleting {vm_name}")
        try:
            subprocess.run(
                ["orbctl", "delete", "--force", vm_name],
                capture_output=True,
                timeout=30,
            )
        except Exception as e:
            print(f"  Error: {e}")
    _worker_vms.clear()

# Register cleanup
atexit.register(cleanup_worker_vms)
```

### Approach 2: Hybrid - Worker VM + One-Off VMs

Some tests need fresh VMs (e.g., testing VM creation/deletion). Support both:

```python
# tests/test_utils.py

def create_test_vm(
    name_prefix: str = "test-vm",
    reuse_worker_vm: bool = True
) -> str:
    """
    Create or get a test VM.

    Args:
        name_prefix: VM name prefix (only used if reuse_worker_vm=False)
        reuse_worker_vm: If True, return the persistent worker VM (default).
                        If False, create a new one-off VM.

    Returns:
        VM name (ready to use)

    Example:
        # Most tests - reuse worker VM (fast!)
        vm_name = create_test_vm()

        # Tests that need fresh VM (e.g., testing VM lifecycle)
        vm_name = create_test_vm(reuse_worker_vm=False)
    """
    if reuse_worker_vm:
        # Get the persistent worker VM
        from tests.conftest import get_worker_vm
        return get_worker_vm()

    # Create a one-off VM (old behavior)
    timestamp = int(time.time())
    pid = os.getpid()
    random_suffix = uuid.uuid4().hex[:6]
    vm_name = f"{name_prefix}-{timestamp}-{pid}-{random_suffix}"

    # ... create, start, return (existing code)
```

## Usage Comparison

### Most Tests (98%) - Use Worker VM

```python
def test_vm_operations(worker_vm):
    """Test using the persistent worker VM."""
    # worker_vm is already created and started
    result = subprocess.run(
        ["orbctl", "info", worker_vm, "--format", "json"],
        capture_output=True,
        text=True,
    )
    # No cleanup - VM persists for next test
```

**Time:** 5 seconds (just the test logic)

### Lifecycle Tests (2%) - Create Fresh VM

```python
def test_vm_creation_and_deletion():
    """Test that specifically tests VM lifecycle."""
    vm_name = create_test_vm(reuse_worker_vm=False)

    # Test creation
    assert vm_exists(vm_name)

    # Test deletion
    delete_vm_with_retry(vm_name, force=True)
    assert not vm_exists(vm_name)
```

**Time:** 75 seconds (60s create + 5s test + 10s delete)

## Benefits

### Performance Improvement

**Serial Execution (no parallelism):**

- Current: N tests × (60s create + 5s test + 10s delete) = N × 75s
- Optimized: 1 × 60s create + N × 5s test + 1 × 10s delete = 70s + N × 5s
- **Savings: (N-1) × 70 seconds**

**Example with 100 tests:**

- Current: 100 × 75s = 7500s (125 minutes)
- Optimized: 70s + 100 × 5s = 570s (9.5 minutes)
- **Savings: 6930 seconds (115.5 minutes = 92% faster!)**

**Parallel Execution (4 workers):**

- Current: 25 tests/worker × 75s = 1875s (31 minutes)
- Optimized: 4 × 60s create + 25 × 5s test = 365s (6 minutes)
- **Savings: 1510 seconds (25 minutes = 81% faster!)**

### Resource Usage

- **Current:** Up to N VMs at once (if tests overlap)
- **Optimized:** Only W VMs (where W = number of workers)
- **Reduction:** From potentially hundreds to typically 4-8

### Reliability

- **Less OrbStack contention** - Fewer VMs = less resource pressure
- **Fewer network operations** - Less image pulling, less networking setup
- **Fewer timeouts** - Less likely to hit OrbStack limits

## Migration Path

### Phase 1: Add Worker VM Fixture (Now)

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def worker_vm():
    # Implementation above
```

### Phase 2: Use in New Tests (Immediately)

```python
def test_new_feature(worker_vm):
    # Use worker_vm
```

### Phase 3: Migrate Existing Tests (Gradual)

```python
# Before
def test_something(self):
    create_result = subprocess.run(
        ["orbctl", "create", self.test_image, self.test_vm_name], ...
    )
    # ... 20 lines ...

# After
def test_something(worker_vm):
    # Use worker_vm - 1 line change!
```

### Phase 4: Deprecate create_test_vm() (Optional)

Most tests should use `worker_vm` fixture. Keep `create_test_vm(reuse_worker_vm=False)`
only for the ~2% of tests that actually test VM lifecycle operations.

## Edge Cases

### Test Modifies VM State

**Problem:** Test A modifies the VM, affecting Test B

**Solution 1:** Reset VM state between tests (if needed)

```python
@pytest.fixture
def clean_worker_vm(worker_vm):
    """Worker VM with cleanup between tests."""
    yield worker_vm
    # Reset any state if needed
    subprocess.run(["orbctl", "run", "-m", worker_vm, "rm -rf /tmp/test-*"])
```

**Solution 2:** Tests that modify state use one-off VMs

```python
def test_that_modifies_vm():
    vm_name = create_test_vm(reuse_worker_vm=False)
    # Modify away - this VM is disposable
```

### Test Needs Specific Configuration

**Problem:** Test needs arm64, but worker VM is x86_64

**Solution:** One-off VM for special cases

```python
def test_arm64_specific():
    # This test needs special config - create one-off VM
    vm_name = create_test_vm(reuse_worker_vm=False)
    # ... test with arch-specific VM
```

### Worker Crashes Mid-Session

**Problem:** Worker dies, leaves VM behind

**Solution:** Orphan cleanup (already implemented!) will catch it

```python
def cleanup_orphaned_test_vms():
    # Already matches "pytest-worker-*"
    test_prefixes = [
        "test-vm-",
        "pytest-worker-",  # ← Catches worker VMs
        # ...
    ]
```

## Recommendation

**Implement the hybrid approach:**

1. Add `worker_vm` fixture for 98% of tests (session-scoped, reusable)
2. Keep `create_test_vm(reuse_worker_vm=False)` for lifecycle tests
3. Default to `reuse_worker_vm=True` for maximum efficiency
4. Migrate tests gradually (fixture parameter change)

**Expected results:**

- **80-90% reduction in test execution time**
- **90% reduction in VM operations**
- **Better OrbStack stability** (fewer concurrent VMs)
- **Lower resource usage**

**Implementation time:** ~2 hours

- Add fixture: 30 minutes
- Update `create_test_vm()`: 30 minutes
- Test and debug: 1 hour

This is a significant optimization that solves the root cause of many timeout issues!
