# Test VM Management Centralization Analysis

## Current State

### Existing Infrastructure

**`tests/test_utils.py`** already provides:

- ✅ `create_vm_with_retry()` - Resilient VM creation with automatic cleanup registration
- ✅ `delete_vm_with_retry()` - Resilient VM deletion
- ✅ `start_vm_with_retry()` - Resilient VM start
- ✅ `stop_vm_with_retry()` - Resilient VM stop
- ✅ `register_test_vm_for_cleanup()` - Manual cleanup registration
- ✅ `execute_orbctl_with_retry()` - Generic retry logic for orbctl commands

### The Problem

**Tests are NOT using these utilities consistently:**

```bash
# Found 55 direct orbctl calls across 10 test files
tests/test_benchmarks.py:1
tests/test_vm_command_builders.py:6
tests/test_utils.py:1
tests/test_vm_operations_phase2.py:1
tests/test_vm_operations_integration.py:9
tests/test_e2e.py:9
tests/test_vm_operations_unit.py:20
tests/test_pyinfra_deployment.py:2
tests/test_connector.py:2
tests/test_connector_coverage_e2e.py:4
```

**Issues with direct `subprocess.run()` calls:**

1. ❌ No automatic cleanup registration
2. ❌ No retry logic for network errors
3. ❌ Inconsistent timeouts (60s vs 120s vs 180s)
4. ❌ Duplicated error handling
5. ❌ Hard to maintain (changes need to be made in multiple places)

## Proposed Solution

### Phase 1: Enhanced Test Utilities (Immediate)

Add higher-level helpers to `test_utils.py`:

```python
class TestVMManager:
    """Context manager for test VM lifecycle management."""

    def __init__(self, image: str = "ubuntu:22.04", name_prefix: str = "test-vm"):
        self.image = image
        self.name_prefix = name_prefix
        self.vm_name = f"{name_prefix}-{int(time.time())}"
        self.created = False

    def __enter__(self):
        """Create VM and register for cleanup."""
        self.created = create_vm_with_retry(
            self.image,
            self.vm_name,
            auto_cleanup=True
        )
        if self.created:
            # Wait for VM to be ready
            time.sleep(2)
            start_vm_with_retry(self.vm_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up VM."""
        if self.created:
            delete_vm_with_retry(self.vm_name, force=True)
        return False  # Don't suppress exceptions


def create_test_vm(
    image: str = "ubuntu:22.04",
    name_prefix: str = "test-vm",
    arch: Optional[str] = None,
    user: Optional[str] = None,
    start: bool = True,
) -> str:
    """
    Create a test VM with automatic cleanup registration.

    This is the recommended way to create VMs in tests.

    Args:
        image: VM image (default: ubuntu:22.04)
        name_prefix: VM name prefix (default: test-vm)
        arch: Architecture (optional)
        user: Default user (optional)
        start: Start VM after creation (default: True)

    Returns:
        VM name

    Raises:
        RuntimeError: If VM creation fails

    Example:
        vm_name = create_test_vm()
        # VM is automatically registered for cleanup
        # Use vm_name in your tests
    """
    vm_name = f"{name_prefix}-{int(time.time())}"

    success = create_vm_with_retry(
        image=image,
        vm_name=vm_name,
        arch=arch,
        user=user,
        auto_cleanup=True
    )

    if not success:
        raise RuntimeError(f"Failed to create VM: {vm_name}")

    if start:
        time.sleep(2)  # Wait for VM to be ready
        if not start_vm_with_retry(vm_name):
            delete_vm_with_retry(vm_name, force=True)
            raise RuntimeError(f"Failed to start VM: {vm_name}")

    return vm_name
```

### Phase 2: Pytest Fixtures (Better)

Add fixtures to `conftest.py`:

```python
@pytest.fixture
def test_vm():
    """Fixture that provides a ready-to-use test VM."""
    vm_name = create_test_vm()
    yield vm_name
    # Cleanup handled by auto_cleanup_test_vm fixture


@pytest.fixture
def test_vm_manager():
    """Fixture that provides a VM manager context."""
    managers = []

    def _create_vm(image="ubuntu:22.04", name_prefix="test-vm", **kwargs):
        manager = TestVMManager(image, name_prefix)
        managers.append(manager)
        return manager

    yield _create_vm

    # Cleanup all managers
    for manager in managers:
        if manager.created:
            delete_vm_with_retry(manager.vm_name, force=True)


@pytest.fixture
def vm_pool():
    """Fixture that provides a pool of VMs for concurrent tests."""
    vms = []

    def _create_pool(count: int, image="ubuntu:22.04"):
        for i in range(count):
            vm_name = create_test_vm(name_prefix=f"pool-vm-{i}")
            vms.append(vm_name)
        return vms

    yield _create_pool

    # Cleanup all VMs in pool
    for vm_name in vms:
        delete_vm_with_retry(vm_name, force=True)
```

## Benefits of Centralization

### 1. Consistency

- ✅ All VMs created with same retry logic
- ✅ All VMs automatically registered for cleanup
- ✅ Consistent timeouts across all tests
- ✅ Consistent error handling

### 2. Maintainability

- ✅ Single place to update VM creation logic
- ✅ Easy to add new features (e.g., resource tagging)
- ✅ Easy to adjust timeouts globally
- ✅ Easier to debug issues

### 3. Reliability

- ✅ Automatic cleanup registration prevents orphaned VMs
- ✅ Retry logic handles transient failures
- ✅ Better error messages
- ✅ Reduced test flakiness

### 4. Developer Experience

- ✅ Simple API: `vm_name = create_test_vm()`
- ✅ Context manager for automatic cleanup
- ✅ Fixtures for common patterns
- ✅ Less boilerplate in tests

## Migration Strategy

### Step 1: Enhance `test_utils.py` (Now)

- Add `TestVMManager` context manager
- Add `create_test_vm()` convenience function
- Add `delete_test_vm()` convenience function
- Document usage patterns

### Step 2: Add Fixtures to `conftest.py` (Now)

- Add `test_vm` fixture
- Add `test_vm_manager` fixture
- Add `vm_pool` fixture
- Document in docstrings

### Step 3: Update High-Impact Tests (Priority)

- `test_e2e.py` (9 direct calls)
- `test_vm_operations_integration.py` (9 direct calls)
- `test_vm_operations_unit.py` (20 direct calls)

### Step 4: Update Remaining Tests (As Needed)

- Update other test files gradually
- Keep old patterns working during transition
- Remove deprecated patterns in next major version

## Example Refactoring

### Before (Current)

```python
def test_vm_lifecycle_end_to_end(self):
    # Create VM
    create_result = subprocess.run(
        ["orbctl", "create", self.test_image, self.test_vm_name],
        capture_output=True,
        text=True,
        timeout=60,  # Might timeout!
    )
    assert create_result.returncode == 0

    # Start VM
    time.sleep(5)
    start_result = subprocess.run(
        ["orbctl", "start", self.test_vm_name],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Test logic...

    # Cleanup (might not run if test fails!)
    subprocess.run(
        ["orbctl", "delete", "--force", self.test_vm_name],
        capture_output=True,
        timeout=30,
    )
```

### After (With Utilities)

```python
def test_vm_lifecycle_end_to_end(self):
    # Create VM with automatic cleanup and retry
    vm_name = create_test_vm()  # That's it!

    # Test logic...
    # VM is automatically cleaned up even if test fails
```

### After (With Context Manager)

```python
def test_vm_lifecycle_end_to_end(self):
    with TestVMManager() as vm:
        # VM is created and started
        # Test logic using vm.vm_name
        pass
    # VM is automatically cleaned up
```

### After (With Fixture)

```python
def test_vm_lifecycle_end_to_end(self, test_vm):
    # test_vm is already created and started
    # Test logic using test_vm
    pass
    # VM is automatically cleaned up
```

## Recommendation

**Implement Phase 1 + Phase 2 immediately:**

1. ✅ Enhance `test_utils.py` with convenience functions
2. ✅ Add fixtures to `conftest.py`
3. ✅ Document usage in `docs/20251021-running-tests.md`
4. ⏳ Gradually migrate tests (not urgent, but beneficial)

**Benefits:**

- Immediate improvement for new tests
- Existing tests continue to work
- Gradual migration path
- Better developer experience

**Effort:**

- Phase 1+2: ~2 hours
- Migration: Can be done incrementally over time

## Conclusion

**Yes, it's absolutely worth centralizing VM management!**

The infrastructure already exists in `test_utils.py`, but it's not being used consistently.
By adding convenience functions and fixtures, we can:

1. Make tests more reliable (automatic cleanup, retry logic)
2. Make tests easier to write (less boilerplate)
3. Make tests easier to maintain (single source of truth)
4. Reduce orphaned VMs (automatic registration)
5. Improve developer experience (simple API)

The migration can be done gradually without breaking existing tests.
