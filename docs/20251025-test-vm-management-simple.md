# Test VM Management - Simplified Proposal

## Analysis: Current Usage Patterns

After reviewing all test files, **100% of VM creations follow this pattern:**

```python
# Create VM
create_result = subprocess.run(["orbctl", "create", image, vm_name], ...)
if create_result.returncode == 0:
    time.sleep(5)  # Wait for VM to be ready
    subprocess.run(["orbctl", "start", vm_name], ...)  # Always start immediately
    time.sleep(5)  # Wait for VM to start
    # Use VM...
```

**Key findings:**

- ✅ VMs are **always** started immediately after creation
- ✅ Tests **always** wait 5-10 seconds after create and after start
- ✅ Tests **always** check `returncode == 0` before proceeding
- ❌ No tests create a VM without starting it
- ❌ No tests need fine-grained control over the create/start sequence

## Simplified Proposal

### Keep It Simple: Just Two Functions

```python
# tests/test_utils.py

def create_test_vm(
    image: str = "ubuntu:22.04",
    name_prefix: str = "test-vm",
    arch: Optional[str] = None,
    user: Optional[str] = None,
) -> str:
    """
    Create and start a test VM with automatic cleanup.

    This is the recommended way to create VMs in tests. The VM is:
    - Created with retry logic
    - Started automatically
    - Registered for automatic cleanup

    Args:
        image: VM image (default: ubuntu:22.04)
        name_prefix: VM name prefix (default: test-vm)
        arch: Architecture (optional)
        user: Default user (optional)

    Returns:
        VM name (ready to use)

    Raises:
        RuntimeError: If VM creation or start fails

    Example:
        vm_name = create_test_vm()
        # VM is ready to use, will be cleaned up automatically
    """
    vm_name = f"{name_prefix}-{int(time.time())}"

    # Create with retry and auto-cleanup registration
    if not create_vm_with_retry(
        image=image,
        vm_name=vm_name,
        arch=arch,
        user=user,
        auto_cleanup=True,
    ):
        raise RuntimeError(f"Failed to create VM: {vm_name}")

    # Wait for VM to be ready
    time.sleep(5)

    # Start VM
    if not start_vm_with_retry(vm_name):
        delete_vm_with_retry(vm_name, force=True)
        raise RuntimeError(f"Failed to start VM: {vm_name}")

    # Wait for VM to fully start
    time.sleep(5)

    return vm_name


def cleanup_test_vm(vm_name: str) -> bool:
    """
    Clean up a test VM (convenience wrapper).

    Args:
        vm_name: VM name to delete

    Returns:
        True if successful, False otherwise
    """
    return delete_vm_with_retry(vm_name, force=True)
```

### Optional: Simple Pytest Fixture

```python
# tests/conftest.py

@pytest.fixture
def test_vm():
    """Fixture that provides a ready-to-use test VM."""
    from tests.test_utils import create_test_vm

    vm_name = create_test_vm()
    yield vm_name
    # Cleanup handled automatically by auto_cleanup_test_vm fixture
```

## Usage Examples

### Before (Current - 10+ lines of boilerplate)

```python
def test_vm_lifecycle_end_to_end(self):
    # Create VM
    create_result = subprocess.run(
        ["orbctl", "create", self.test_image, self.test_vm_name],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if create_result.returncode == 0:
        # Wait for VM to be ready
        time.sleep(5)

        # Start VM
        subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )

        time.sleep(5)

        # Test logic...

        # Cleanup (might not run if test fails!)
        subprocess.run(
            ["orbctl", "delete", "--force", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )
```

### After (1 line!)

```python
def test_vm_lifecycle_end_to_end(self):
    vm_name = create_test_vm()

    # Test logic...
    # VM automatically cleaned up even if test fails
```

### With Fixture (Even Simpler)

```python
def test_vm_lifecycle_end_to_end(self, test_vm):
    # test_vm is ready to use
    # Test logic...
    # VM automatically cleaned up
```

## What We're NOT Adding

❌ Context managers (unnecessary complexity)
❌ VM pools (no use case)
❌ `start=False` parameter (never used)
❌ Separate create/start functions (always used together)
❌ Complex configuration options (not needed)

## Benefits

### Simplicity

- ✅ Just **one function** to remember: `create_test_vm()`
- ✅ Sensible defaults for 95% of cases
- ✅ Optional parameters for special cases (arch, user)

### Reliability

- ✅ Automatic cleanup registration (no orphaned VMs)
- ✅ Retry logic for network errors
- ✅ Proper wait times between operations
- ✅ Error handling built-in

### Maintainability

- ✅ Single place to update VM creation logic
- ✅ Easy to adjust wait times globally
- ✅ Easy to add new features (e.g., health checks)

### Developer Experience

- ✅ **90% reduction in boilerplate** (1 line vs 10+ lines)
- ✅ Can't forget cleanup registration
- ✅ Can't forget to wait between operations
- ✅ Can't forget error handling

## Implementation Effort

- **Add `create_test_vm()` to `test_utils.py`:** 30 minutes
- **Add `test_vm` fixture to `conftest.py`:** 10 minutes
- **Document in `docs/20251021-running-tests.md`:** 20 minutes
- **Total:** ~1 hour

Migration is optional and can be done gradually.

## Recommendation

**Implement the simplified version:**

1. Add `create_test_vm()` to `test_utils.py`
2. Add `test_vm` fixture to `conftest.py`
3. Document usage
4. Use in new tests (existing tests continue to work)

**Skip:**

- Context managers (over-engineering)
- VM pools (no use case)
- Complex configuration (YAGNI)

This gives us 90% of the benefits with 10% of the complexity.
