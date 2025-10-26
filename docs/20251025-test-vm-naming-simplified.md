# Test VM Naming - Simplified Design

## Problem: Too Many Prefixes

Current state has 6+ different prefixes:

```python
test_prefixes = [
    "test-vm-",              # Generic tests
    "e2e-ops-vm-",          # E2E ops tests
    "deploy-test-vm-",      # Deployment tests
    "consolidated-test-vm-", # ???
    "e2e-test-vm-",         # E2E tests
    "pytest-shared-",       # Shared fixtures
]
```

**Problems:**

- Inconsistent (some tests use one prefix, some another)
- Hard to maintain (need to update cleanup logic when adding prefixes)
- Unnecessary complexity (all are test VMs, why distinguish?)
- User-facing API (callers can specify prefix)

## Simplified Design: One Prefix

### Single Standard Prefix

```python
# All test VMs use this prefix
TEST_VM_PREFIX = "pytest-test-"

# Naming schemes:
# - One-off VMs: pytest-test-{timestamp}-{pid}-{random}
# - Worker VMs:  pytest-test-worker-{pid}-{timestamp}
```

**Benefits:**

- Single prefix to track and clean up
- Implementation detail (not user-facing)
- Easy to identify test VMs
- Consistent across all test types

### Implementation

```python
# tests/conftest.py

# Single prefix for ALL test VMs
TEST_VM_PREFIX = "pytest-test-"

def cleanup_orphaned_test_vms():
    """Clean up any orphaned test VMs from previous runs."""
    try:
        result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return

        vms = json.loads(result.stdout)

        # Single prefix - simple!
        test_vms = [
            vm["name"]
            for vm in vms
            if vm["name"].startswith(TEST_VM_PREFIX)
        ]

        if test_vms:
            print(f"\nCleaning up {len(test_vms)} orphaned test VMs...")
            for vm_name in test_vms:
                try:
                    subprocess.run(
                        ["orbctl", "delete", "--force", vm_name],
                        capture_output=True,
                        timeout=30,
                    )
                except subprocess.TimeoutExpired:
                    print(f"  Timeout deleting {vm_name}")
                except Exception as e:
                    print(f"  Error deleting {vm_name}: {e}")
    except Exception as e:
        print(f"Error during orphan cleanup: {e}")


# Track worker VMs (one per pytest worker)
_worker_vms = {}

def get_worker_vm() -> str:
    """
    Get or create a VM for the current pytest worker.

    Returns:
        VM name for this worker
    """
    worker_pid = os.getpid()

    if worker_pid in _worker_vms:
        return _worker_vms[worker_pid]

    from tests.test_utils import create_vm_with_retry, start_vm_with_retry, delete_vm_with_retry

    # Use standard prefix
    timestamp = int(time.time())
    vm_name = f"{TEST_VM_PREFIX}worker-{worker_pid}-{timestamp}"

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

    _worker_vms[worker_pid] = vm_name
    print(f"[Worker {worker_pid}] Session VM ready: {vm_name}")
    return vm_name


@pytest.fixture(scope="session")
def worker_vm():
    """
    Fixture providing a persistent VM for the current pytest worker.

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
```

```python
# tests/test_utils.py

# Import from conftest
from tests.conftest import TEST_VM_PREFIX

def create_test_vm(reuse_worker_vm: bool = True) -> str:
    """
    Create or get a test VM.

    By default, returns the persistent worker VM for maximum performance.
    Set reuse_worker_vm=False for tests that need a fresh VM.

    Args:
        reuse_worker_vm: If True, return the persistent worker VM (default).
                        If False, create a new one-off VM.

    Returns:
        VM name (ready to use)

    Examples:
        # Most tests - reuse worker VM (fast!)
        vm_name = create_test_vm()

        # Tests that need fresh VM
        vm_name = create_test_vm(reuse_worker_vm=False)
    """
    if reuse_worker_vm:
        from tests.conftest import get_worker_vm
        return get_worker_vm()

    # Create a one-off VM with standard prefix (no user choice)
    timestamp = int(time.time())
    pid = os.getpid()
    random_suffix = uuid.uuid4().hex[:6]
    vm_name = f"{TEST_VM_PREFIX}{timestamp}-{pid}-{random_suffix}"

    if not create_vm_with_retry(
        image="ubuntu:22.04",
        vm_name=vm_name,
        arch=None,
        user=None,
        auto_cleanup=True,
    ):
        raise RuntimeError(f"Failed to create VM: {vm_name}")

    time.sleep(5)

    if not start_vm_with_retry(vm_name):
        delete_vm_with_retry(vm_name, force=True)
        raise RuntimeError(f"Failed to start VM: {vm_name}")

    time.sleep(5)

    return vm_name
```

## Examples

### VM Names Generated

```python
# Worker VMs (session-scoped)
"pytest-test-worker-12345-1761248130"  # Worker 1
"pytest-test-worker-12346-1761248130"  # Worker 2

# One-off VMs (for lifecycle tests)
"pytest-test-1761248130-12345-a3f2e1"  # Test-specific VM
"pytest-test-1761248131-12345-b7d9c4"  # Another one
```

### Usage (Simplified API)

```python
# Most tests - use worker VM (no parameters!)
def test_something(worker_vm):
    # worker_vm is "pytest-test-worker-12345-1761248130"
    # (implementation detail - caller doesn't care)
    pass

# Lifecycle tests - create one-off VM (no name choice!)
def test_vm_creation():
    vm_name = create_test_vm(reuse_worker_vm=False)
    # vm_name is "pytest-test-1761248130-12345-a3f2e1"
    # (implementation detail - caller doesn't care)
    pass
```

### Cleanup (Simplified)

```python
# Single prefix - catches everything!
test_vms = [
    vm["name"]
    for vm in vms
    if vm["name"].startswith("pytest-test-")
]
```

## Benefits

### Simplicity

- **One prefix** instead of 6+
- **One cleanup rule** instead of multiple
- **No user choices** for naming

### Maintainability

- Adding new test types? No changes needed
- Cleanup logic never needs updating
- Easy to identify test VMs in OrbStack

### Consistency

- All test VMs follow same pattern
- No confusion about which prefix to use
- Clear distinction from non-test VMs

### Read-Only Names

Callers get VM names but can't control them:

```python
# API: Get a VM (implementation detail)
vm = worker_vm  # "pytest-test-worker-12345-1761248130"
vm = create_test_vm()  # "pytest-test-1761248130-12345-a3f2e1"

# Use it
subprocess.run(["orbctl", "info", vm, ...])

# Name is opaque - caller shouldn't care about format
```

## Migration

### Old Code

```python
def test_something(self):
    self.test_vm_name = f"e2e-test-vm-{int(time.time())}"
    # ... create VM with self.test_vm_name ...
```

### New Code

```python
def test_something(worker_vm):
    # worker_vm is provided - don't care about the name
    # ... use worker_vm ...
```

**Name goes from user-facing to implementation detail!**

## Summary

**Changes:**

1. ✅ Single prefix: `pytest-test-`
2. ✅ No user control over names (removed `name_prefix` parameter)
3. ✅ Names are read-only (returned, but format is opaque)
4. ✅ Simplified cleanup (one prefix to rule them all)

**Result:**

- Simpler API (one less parameter)
- Simpler implementation (one prefix)
- Simpler cleanup (one rule)
- Better encapsulation (names are implementation detail)
