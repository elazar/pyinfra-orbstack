# Test VM Management - Complete Solution Analysis

## The User's Critical Questions

1. **Would the solution involve just calling this one function?**
2. **Or is there more code to it?**
3. **How would this handle tests being run in parallel?**

## Current State Analysis

### Existing Infrastructure (Already Working)

```python
# tests/test_utils.py
def register_test_vm_for_cleanup(vm_name: str) -> None:
    """Register a test VM for automatic cleanup."""
    _test_vms_created.add(vm_name)  # Thread-safe set

def create_vm_with_retry(..., auto_cleanup: bool = True) -> bool:
    """Create VM with retry logic."""
    if auto_cleanup:
        register_test_vm_for_cleanup(vm_name)  # ✅ Already registers
    # ... create VM ...
    return return_code == 0

def start_vm_with_retry(vm_name: str) -> bool:
    """Start VM with retry logic."""
    # ... start VM ...
    return return_code == 0
```

```python
# tests/conftest.py
_test_vms_created = set()  # Global tracking

@pytest.fixture(autouse=True)
def auto_cleanup_test_vm(request):
    """Automatically clean up VMs after each test."""
    # Tracks VMs from request.instance.test_vm_name
    # Cleans up after test completes
    # ✅ Already handles cleanup

def cleanup_test_vms():
    """Clean up all tracked VMs at session end."""
    # ✅ Already registered with atexit

def cleanup_orphaned_test_vms():
    """Clean up orphaned VMs from previous runs."""
    # ✅ Already runs at session start
```

### The Problem: Parallel Execution Collision

**Current naming pattern:**

```python
vm_name = f"test-vm-{int(time.time())}"
```

**Issue: Two tests starting in the same second get the same name!**

```bash
# Test 1 (parallel worker 1): test-vm-1761248130
# Test 2 (parallel worker 2): test-vm-1761248130  ❌ COLLISION!
```

**This causes:**

- VM creation failures (name already exists)
- Test failures
- Cleanup confusion (which test owns the VM?)

## The Complete Solution

### Step 1: Fix Parallel Collision (Critical)

```python
# tests/test_utils.py
import os
import time
import uuid

def create_test_vm(name_prefix: str = "test-vm") -> str:
    """
    Create and start a test VM with automatic cleanup.

    Thread-safe for parallel test execution. VM name includes:
    - Timestamp (for chronological ordering)
    - Process ID (for parallel worker isolation)
    - Random suffix (for sub-second collision prevention)

    Args:
        name_prefix: VM name prefix for identification (default: test-vm)

    Returns:
        VM name (ready to use)

    Raises:
        RuntimeError: If VM creation or start fails

    Example:
        vm_name = create_test_vm()
        # VM is ready to use and will be cleaned up automatically

        vm_name = create_test_vm("e2e-test-vm")
        # Custom prefix for test type identification
    """
    # Generate unique VM name for parallel execution
    timestamp = int(time.time())
    pid = os.getpid()  # Unique per parallel worker
    random_suffix = uuid.uuid4().hex[:6]  # Prevent sub-second collisions
    vm_name = f"{name_prefix}-{timestamp}-{pid}-{random_suffix}"

    # Create with retry and auto-cleanup registration
    if not create_vm_with_retry(
        image="ubuntu:22.04",
        vm_name=vm_name,
        arch=None,
        user=None,
        auto_cleanup=True,  # ✅ Registers for cleanup
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
```

### Step 2: Update Cleanup to Handle New Pattern

```python
# tests/conftest.py

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
        test_prefixes = [
            "test-vm-",
            "e2e-test-vm-",
            "e2e-ops-vm-",
            "deploy-test-vm-",
            "pytest-shared-",
        ]

        # Find test VMs (now with longer names due to pid-random suffix)
        test_vms = [
            vm["name"] for vm in vms
            if any(vm["name"].startswith(prefix) for prefix in test_prefixes)
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
```

## Usage: Yes, Just One Function Call

### Simple Test

```python
def test_vm_operations(self):
    vm_name = create_test_vm()  # That's it!

    # Use the VM
    result = subprocess.run(
        ["orbctl", "info", vm_name, "--format", "json"],
        capture_output=True,
        text=True,
    )

    # No cleanup needed - automatic!
```

### Multiple VMs in One Test

```python
def test_multi_vm_scenario(self):
    vm1 = create_test_vm("test-vm-primary")
    vm2 = create_test_vm("test-vm-secondary")

    # Test cross-VM communication
    # Both VMs cleaned up automatically
```

### Class-Based Tests

```python
class TestVMLifecycle:
    def test_create_and_start(self):
        vm_name = create_test_vm()
        # Test logic...

    def test_stop_and_restart(self):
        vm_name = create_test_vm()
        # Test logic...

    # Each test gets its own VM, all cleaned up automatically
```

## Parallel Execution: Fully Supported

### How It Works

```python
# Worker 1 (PID 12345) at time 1761248130.123
vm_name = create_test_vm()
# Result: test-vm-1761248130-12345-a3f2e1

# Worker 2 (PID 12346) at time 1761248130.456
vm_name = create_test_vm()
# Result: test-vm-1761248130-12346-b7d9c4

# Worker 3 (PID 12347) at time 1761248130.789
vm_name = create_test_vm()
# Result: test-vm-1761248130-12347-e5a1f8
```

**Uniqueness guaranteed by:**

1. **Timestamp** - Different second = different name
2. **PID** - Different worker = different name (even in same second)
3. **Random suffix** - Different call in same worker/second = different name

### Cleanup in Parallel

Each worker's VMs are tracked in the **global** `_test_vms_created` set:

```python
# Worker 1 creates: test-vm-1761248130-12345-a3f2e1
_test_vms_created.add("test-vm-1761248130-12345-a3f2e1")

# Worker 2 creates: test-vm-1761248130-12346-b7d9c4
_test_vms_created.add("test-vm-1761248130-12346-b7d9c4")

# At session end, both are cleaned up
```

**Thread safety:** Python's `set.add()` is atomic, so parallel workers can safely add to the set.

## What Happens Behind the Scenes

### When You Call `create_test_vm()`

```text
1. Generate unique name (timestamp-pid-random)
   └─> test-vm-1761248130-12345-a3f2e1

2. Call create_vm_with_retry()
   ├─> Register for cleanup (add to _test_vms_created)
   ├─> Execute: orbctl create ubuntu:22.04 test-vm-1761248130-12345-a3f2e1
   ├─> Retry on network errors (up to 3 times)
   └─> Return success/failure

3. Wait 5 seconds for VM to be ready

4. Call start_vm_with_retry()
   ├─> Execute: orbctl start test-vm-1761248130-12345-a3f2e1
   ├─> Retry on errors (up to 2 times)
   └─> Return success/failure

5. Wait 5 seconds for VM to fully start

6. Return VM name to test

[Test runs...]

7. After test completes:
   ├─> auto_cleanup_test_vm fixture runs
   ├─> Finds all VMs matching the pattern
   └─> Deletes them with: orbctl delete --force

8. At session end:
   ├─> cleanup_test_vms() runs (atexit)
   └─> Deletes any VMs still in _test_vms_created (backup)
```

### Error Scenarios

**VM creation fails:**

```python
try:
    vm_name = create_test_vm()
except RuntimeError as e:
    # VM was registered for cleanup before creation attempt
    # Cleanup will try to delete (harmless if VM doesn't exist)
    pytest.skip(f"Could not create VM: {e}")
```

**VM creation times out:**

```python
# Pytest timeout (180s) kills the test
# VM is already registered in _test_vms_created
# Session cleanup will delete it
```

**Test crashes:**

```python
# atexit handler ensures cleanup_test_vms() runs
# All VMs in _test_vms_created are deleted
```

## Migration Path

### Phase 1: Add Function (Now)

```python
# tests/test_utils.py
def create_test_vm(name_prefix: str = "test-vm") -> str:
    # Implementation above
```

### Phase 2: Use in New Tests (Immediately)

```python
def test_new_feature(self):
    vm_name = create_test_vm()
    # Test logic...
```

### Phase 3: Migrate Existing Tests (Gradual)

**Before (23 lines):**

```python
def test_vm_lifecycle(self):
    create_result = subprocess.run(
        ["orbctl", "create", self.test_image, self.test_vm_name],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if create_result.returncode == 0:
        time.sleep(5)
        subprocess.run(["orbctl", "start", self.test_vm_name], ...)
        time.sleep(5)

        # Test logic...

        subprocess.run(["orbctl", "delete", "--force", self.test_vm_name], ...)
```

**After (1 line):**

```python
def test_vm_lifecycle(self):
    vm_name = create_test_vm()

    # Test logic...
```

## Summary: Complete Solution

### What You Get

✅ **One function call:** `vm_name = create_test_vm()`

✅ **Automatic cleanup:** Registered immediately, cleaned up after test

✅ **Parallel execution:** Unique names via timestamp-pid-random

✅ **Retry logic:** Network errors handled automatically

✅ **Error handling:** Proper exceptions, cleanup on failure

✅ **Thread-safe:** Python set operations are atomic

### What Happens Automatically

1. VM name generation (unique per call)
2. Cleanup registration (before creation)
3. VM creation with retries
4. Wait for VM ready
5. VM start with retries
6. Wait for VM fully started
7. Cleanup after test (auto_cleanup_test_vm fixture)
8. Backup cleanup at session end (atexit)
9. Orphan cleanup at session start (next run)

### Implementation Effort

- Add `create_test_vm()` function: 30 minutes
- Update cleanup pattern matching: 10 minutes
- Test with parallel execution: 15 minutes
- Document usage: 10 minutes
- **Total: ~1 hour**

### The Answer

**Yes, it's just one function call!** But behind that one call:

- Unique name generation (parallel-safe)
- Automatic cleanup registration
- Retry logic for reliability
- Proper error handling
- Multi-layer cleanup (immediate + session end + next run)

The complexity is hidden, the interface is simple.
