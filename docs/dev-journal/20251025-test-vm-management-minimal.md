# Test VM Management - Minimal Proposal

## Deep Analysis: What Do Tests Actually Use?

After analyzing all test files, here's what's **actually used**:

### Images

- **100% use `ubuntu:22.04`** (defined as `self.test_image = "ubuntu:22.04"`)
- **0 tests** use debian, alpine, or any other image
- **0 tests** pass different images to VM creation

### Architecture (`--arch`)

- **2 tests** use `--arch arm64` (testing the feature itself)
- **98% of tests** use default architecture
- Both arch tests are **feature tests** (testing that `--arch` works), not actual use cases

### User (`--user`)

- **2 tests** use `--user ubuntu` (testing the feature itself)
- **98% of tests** use default user
- Both user tests are **feature tests** (testing that `--user` works), not actual use cases

### Name Prefix

- **All tests** use pattern: `f"{prefix}-{int(time.time())}"`
- **4 different prefixes** used:
  - `test-vm-` (integration tests)
  - `e2e-test-vm-` (e2e tests)
  - `e2e-ops-vm-` (operations e2e tests)
  - `deploy-test-vm-` (deployment tests)
- Prefix distinguishes test type for debugging

## The Minimal Solution

### Just One Function, Zero Optional Parameters

```python
# tests/test_utils.py

def create_test_vm(name_prefix: str = "test-vm") -> str:
    """
    Create and start a test VM with automatic cleanup.

    Creates a VM with ubuntu:22.04, starts it, and registers for cleanup.
    This is the recommended way to create VMs in tests.

    Args:
        name_prefix: VM name prefix for identification (default: test-vm)

    Returns:
        VM name (ready to use)

    Raises:
        RuntimeError: If VM creation or start fails

    Example:
        # Default prefix
        vm_name = create_test_vm()

        # Custom prefix for test type identification
        vm_name = create_test_vm("e2e-test-vm")
    """
    vm_name = f"{name_prefix}-{int(time.time())}"

    # Create with retry and auto-cleanup registration
    if not create_vm_with_retry(
        image="ubuntu:22.04",  # Hardcoded - 100% of tests use this
        vm_name=vm_name,
        arch=None,  # Not needed - only 2 feature tests use this
        user=None,  # Not needed - only 2 feature tests use this
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
```

### For Feature Tests (arch/user)

Keep using `create_vm_with_retry()` directly:

```python
# Only for tests that specifically test arch/user features
success = create_vm_with_retry(
    "ubuntu:22.04",
    vm_name,
    arch="arm64",  # Testing arch feature
    auto_cleanup=True
)
```

## Comparison

### Current State (98% of tests)

```python
def test_something(self):
    # Create VM
    create_result = subprocess.run(
        ["orbctl", "create", self.test_image, self.test_vm_name],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if create_result.returncode == 0:
        time.sleep(5)

        subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )

        time.sleep(5)

        # Test logic...

        subprocess.run(
            ["orbctl", "delete", "--force", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )
```

Lines of boilerplate: 23

### With Minimal Function

```python
def test_something(self):
    vm_name = create_test_vm()

    # Test logic...
```

Lines of boilerplate: 1

Reduction: 96%

## What We're NOT Adding

❌ `image` parameter (100% use ubuntu:22.04)
❌ `arch` parameter (only 2 feature tests need it)
❌ `user` parameter (only 2 feature tests need it)
❌ `start` parameter (100% start immediately)
❌ Context managers (unnecessary)
❌ Fixtures (one function is simpler)
❌ VM pools (no use case)

## Benefits

### Ultimate Simplicity

- ✅ **One function**: `create_test_vm()`
- ✅ **One optional parameter**: `name_prefix` (for test identification)
- ✅ **Zero configuration**: Works for 98% of tests

### Reliability

- ✅ Automatic cleanup registration
- ✅ Retry logic for network errors
- ✅ Proper wait times
- ✅ Error handling

### Maintainability

- ✅ Single place to update image (when ubuntu:24.04 comes out)
- ✅ Single place to adjust wait times
- ✅ Easy to add health checks

### Developer Experience

- ✅ **96% reduction in boilerplate** (1 line vs 23 lines)
- ✅ Can't forget cleanup
- ✅ Can't forget to wait
- ✅ Can't use wrong image

## Migration Examples

### Example 1: Basic Integration Test

**Before:**

```python
def test_vm_lifecycle_integration(self):
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

        # Test VM operations
        info_result = subprocess.run(
            ["orbctl", "info", self.test_vm_name, "--format", "json"],
            ...
        )

        subprocess.run(["orbctl", "delete", "--force", self.test_vm_name], ...)
```

**After:**

```python
def test_vm_lifecycle_integration(self):
    vm_name = create_test_vm()

    # Test VM operations
    info_result = subprocess.run(
        ["orbctl", "info", vm_name, "--format", "json"],
        ...
    )
```

### Example 2: E2E Test

**Before:**

```python
class TestE2E:
    def setup_method(self):
        self.test_vm_name = f"e2e-test-vm-{int(time.time())}"
        self.test_image = "ubuntu:22.04"

    def test_something(self):
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            ...
        )
        # ... 20 more lines ...
```

**After:**

```python
class TestE2E:
    def test_something(self):
        vm_name = create_test_vm("e2e-test-vm")
        # Test logic...
```

### Example 3: Feature Test (arch) - No Change Needed

```python
def test_vm_creation_with_arch(self):
    # Still use create_vm_with_retry directly for feature testing
    arm64_vm_name = f"test-vm-arm64-{int(time.time())}"
    success = create_vm_with_retry(
        "ubuntu:22.04",
        arm64_vm_name,
        arch="arm64",
        auto_cleanup=True
    )
    # Test arch-specific behavior...
```

## Implementation

### Step 1: Add Function (15 minutes)

Add `create_test_vm()` to `tests/test_utils.py` (shown above).

### Step 2: Document (10 minutes)

Add to `docs/20251021-running-tests.md`:

```markdown
## Creating Test VMs

Use `create_test_vm()` for all test VMs:

\`\`\`python
from tests.test_utils import create_test_vm

def test_something(self):
    vm_name = create_test_vm()
    # VM is ready to use and will be cleaned up automatically
\`\`\`

For tests that need specific arch/user (rare), use `create_vm_with_retry()` directly.
```

### Step 3: Migration (Optional, Gradual)

- New tests: Use `create_test_vm()`
- Existing tests: Migrate as needed (no rush)
- Feature tests (arch/user): Keep using `create_vm_with_retry()`

Total effort: 25 minutes

## Recommendation

**Implement the minimal version:**

1. Add `create_test_vm(name_prefix="test-vm")` to `test_utils.py`
2. Hardcode `ubuntu:22.04` (used by 100% of tests)
3. No `arch`, `user`, or `image` parameters (only 2 feature tests need them)
4. Document usage
5. Use in new tests

**Why this is better:**

- Even simpler than the "simple" proposal
- Based on actual usage data, not speculation
- 96% reduction in boilerplate
- Zero configuration for 98% of tests
- 25 minutes to implement

**The 2 feature tests** that test arch/user can continue using `create_vm_with_retry()` directly.
They're testing the feature itself, so it makes sense they use the lower-level API.
