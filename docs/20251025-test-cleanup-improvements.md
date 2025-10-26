# Test Cleanup Improvements Analysis

## Problem Identified

**Issue:** Test VMs are being left behind when tests fail or timeout during VM creation.

**Root Cause:** Tests that create VMs directly (using `subprocess.run`) don't properly track or clean up VMs when:
1. VM creation times out (VM may still be created after timeout)
2. Test fails before cleanup code runs
3. Test is interrupted (Ctrl+C)

## Current Cleanup Mechanisms

### What Works Well

1. **`cleanup_orphaned_test_vms()`** - Runs at session start
   - ✅ Cleans up VMs from previous runs
   - ✅ Uses pattern matching on VM names
   - ✅ Handles all test VM prefixes

2. **`cleanup_test_vms()`** - Runs at session end
   - ✅ Cleans up tracked VMs
   - ✅ Registered with `atexit` for crash handling
   - ✅ Called by `pytest_sessionfinish`

3. **`track_test_vm` fixture** - For explicit tracking
   - ✅ Allows tests to register VMs for cleanup
   - ✅ Works well when used

### What Needs Improvement

1. **Tests don't use `track_test_vm` fixture**
   - Many tests create VMs directly without tracking
   - Example: `test_e2e.py`, `test_vm_operations_integration.py`

2. **No per-test cleanup**
   - Tests rely on session-level cleanup
   - VMs accumulate during test run
   - Resource contention can cause later tests to fail

3. **Timeout handling**
   - When `subprocess.run(timeout=60)` expires, VM may still be creating
   - VM name is generated but never tracked
   - Orphaned VM cleanup only runs at next session start

## Recommended Improvements

### Option 1: Use Fixtures Properly (Recommended)

**Pros:** Leverages existing infrastructure, pytest-native
**Cons:** Requires updating many test files

**Implementation:**
```python
# In test files
def test_vm_lifecycle(track_test_vm):
    vm_name = f"test-vm-{int(time.time())}"
    track_test_vm(vm_name)  # Register for cleanup

    # Create VM
    subprocess.run(["orbctl", "create", "ubuntu:22.04", vm_name], ...)

    # Test logic...
    # VM will be cleaned up automatically even if test fails
```

### Option 2: Auto-Track VM Creation (Better)

**Pros:** Automatic, no test changes needed
**Cons:** More complex, requires parsing subprocess calls

**Implementation:**
```python
# In conftest.py
def auto_track_vm_creation(vm_name):
    """Automatically track VM for cleanup when name is generated."""
    _test_vms_created.add(vm_name)

@pytest.fixture(autouse=True)
def auto_cleanup_test_vms(request):
    """Automatically track and clean up VMs created in tests."""
    # Track VM names from test instance
    if hasattr(request.instance, 'test_vm_name'):
        _test_vms_created.add(request.instance.test_vm_name)

    yield

    # Cleanup after test
    if hasattr(request.instance, 'test_vm_name'):
        try:
            subprocess.run(
                ["orbctl", "delete", "--force", request.instance.test_vm_name],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass
```

### Option 3: Improve Orphan Cleanup (Easiest)

**Pros:** No test changes, works immediately
**Cons:** Doesn't solve resource contention during test run

**Implementation:**
```python
# In conftest.py
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
            "e2e-ops-vm-",
            "deploy-test-vm-",
            "consolidated-test-vm-",
            "e2e-test-vm-",
            "pytest-shared-",  # Add session-scoped VMs
        ]

        # More aggressive cleanup - delete ALL test VMs
        orphaned_vms = [
            vm["name"]
            for vm in vms
            if any(vm["name"].startswith(prefix) for prefix in test_prefixes)
        ]

        if orphaned_vms:
            print(f"\nCleaning up {len(orphaned_vms)} orphaned test VMs...")
            for vm_name in orphaned_vms:
                try:
                    subprocess.run(
                        ["orbctl", "delete", "--force", vm_name],
                        capture_output=True,
                        timeout=30,  # Increased from 10s
                    )
                    print(f"  Deleted: {vm_name}")
                except subprocess.TimeoutExpired:
                    print(f"  Timeout deleting: {vm_name}")
                except Exception as e:
                    print(f"  Error deleting {vm_name}: {e}")
    except Exception as e:
        print(f"Error during orphan cleanup: {e}")
```

## Recommended Solution: Combination Approach

Implement **Option 2 (Auto-Track) + Option 3 (Better Orphan Cleanup)**

### Phase 1: Immediate (No Test Changes)

1. ✅ Improve `cleanup_orphaned_test_vms()`:
   - Use `startswith()` instead of `in` for more precise matching
   - Increase timeout from 10s to 30s
   - Add logging for visibility
   - Add `pytest-shared-` prefix

2. ✅ Add auto-tracking fixture:
   - Automatically track VMs from `test_vm_name` attribute
   - Clean up after each test (not just at session end)
   - Handle timeouts gracefully

### Phase 2: Long-term (Requires Test Updates)

1. Update tests to use `track_test_vm` fixture explicitly
2. Add per-test cleanup in tearDown methods
3. Use session-scoped VMs where possible to reduce creation/deletion

## Impact Analysis

**Current State:**
- 13 tests failing due to VM creation timeouts
- 3 leftover VMs found after test run
- Resource contention causing failures

**After Improvements:**
- ✅ Orphaned VMs cleaned up before each run
- ✅ VMs cleaned up after each test (not just session end)
- ✅ Better timeout handling
- ✅ Reduced resource contention
- ✅ More reliable test execution

## Implementation Priority

1. **High Priority:** Improve orphan cleanup (Option 3) - Immediate fix, no test changes
2. **Medium Priority:** Add auto-tracking fixture (Option 2) - Better long-term solution
3. **Low Priority:** Update all tests to use fixtures (Option 1) - Nice to have, high effort

## Testing the Fix

```bash
# Before running tests
orbctl list  # Should show minimal VMs

# Run tests
uv run pytest tests/

# After tests
orbctl list  # Should show no test VMs

# Check cleanup worked
uv run pytest tests/ --collect-only  # Triggers cleanup_orphaned_test_vms
orbctl list  # Should still show no test VMs
```
