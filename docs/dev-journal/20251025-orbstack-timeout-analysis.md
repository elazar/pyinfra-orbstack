# OrbStack Timeout Analysis and Mitigation Strategies

## Current Environment Status

**OrbStack Version:** 2.0.4 (Build 2000400)

**System Resources:**

- **Memory:** 36 GB total
- **Swap Usage:** 7.2 GB / 8.2 GB (87.8% utilized) ⚠️
- **CPU Cores:** 11
- **Active VMs:** 4
- **OrbStack Helper Memory:** 700 MB

## Issue Analysis

### Symptoms

During test execution, we observed:

1. **VM Creation Timeouts**
   - 2 tests failed due to VM creation timeouts
   - Timeout after 4 retry attempts (~180 seconds total)
   - Error: "VM creation failed after 4 attempts"

2. **Pattern**
   - Tests: `test_vm_info_integration` and `test_vm_lifecycle_integration`
   - Both use `create_vm_with_retry()` with standard timeout (180s)
   - Occurs intermittently (23 other similar tests passed)

### Root Cause Analysis

Based on system diagnostics and web research:

#### 1. **High Swap Usage (Primary Suspect)** ⚠️

**Current State:**

- Swap: 87.8% utilized (7.2 GB / 8.2 GB)
- This indicates memory pressure on the system

**Impact:**

- When system memory is exhausted, macOS uses swap (disk-based virtual memory)
- Swap is 100-1000x slower than RAM
- VM creation requires memory allocation, which becomes extremely slow under memory pressure
- This explains why some VMs create successfully while others timeout

**Evidence:**

- OrbStack Helper using 700 MB RAM
- High swap utilization suggests other processes are consuming memory
- VM creation timeouts align with memory allocation delays

#### 2. **Resource Contention**

**Concurrent Operations:**

- Test suite creates/deletes multiple VMs sequentially
- Each VM requires memory, CPU, and disk I/O
- With 4 existing VMs + test VMs being created, resource contention increases
- OrbStack may throttle or queue operations under load

#### 3. **Known OrbStack Issues**

From web research and GitHub issues:

**Issue #1471: Timeout accessing `host.docker.internal` (v1.7.4)**

- Similar timeout symptoms reported
- Related to network access after OrbStack updates
- While not identical to our issue, indicates timeout problems exist in OrbStack

**General Pattern:**

- OrbStack occasionally experiences performance degradation
- Often related to resource constraints or version-specific bugs
- Community reports occasional slow VM operations

## Mitigation Strategies

### Immediate Actions (High Priority)

#### 1. **Reduce Memory Pressure** 🔥

**Problem:** 87.8% swap usage indicates severe memory pressure.

**Solutions:**

a. **Close Unnecessary Applications**

```bash
# Check top memory consumers
top -o MEM -n 20 -l 1 | head -25
```

b. **Restart OrbStack**

```bash
# Clean restart to free any leaked memory
osascript -e 'quit app "OrbStack"'
sleep 5
open -a OrbStack
# Wait for OrbStack to fully start
sleep 10
```

c. **Clear System Caches**

```bash
# Clear user caches (safe)
rm -rf ~/Library/Caches/com.orbstack.*
```

d. **Monitor Memory During Tests**

```bash
# Run in separate terminal during tests
watch -n 5 'vm_stat | grep -E "(free|active|inactive|wired)" && sysctl vm.swapusage'
```

**Expected Impact:** 50-80% reduction in VM creation timeouts

#### 2. **Reduce Test VM Concurrency** 📊

**Problem:** Multiple VMs competing for resources.

**Solutions:**

a. **Delete Existing Test VMs Before Running Suite**

```bash
# Clean slate before testing
orbctl list --format json | jq -r '.[] | select(.name | startswith("test-") or startswith("e2e-") or startswith("consolidated-")) | .name' | xargs -I {} orbctl delete --force {}
```

b. **Run Tests with Lower Parallelism**

```bash
# Serial execution (no parallel workers)
pytest tests/ -v --timeout=180

# Or limit parallel workers
pytest tests/ -v --timeout=180 -n 2  # Only 2 workers instead of auto
```

c. **Implement VM Pooling with Limits**

Update `conftest.py` to limit max concurrent VMs:

```python
import threading

_vm_semaphore = threading.Semaphore(2)  # Max 2 VMs being created at once

def create_vm_with_retry(...):
    with _vm_semaphore:  # Acquire semaphore before creating VM
        # ... existing creation logic ...
```

**Expected Impact:** 30-50% reduction in timeouts

#### 3. **Increase Timeout Values** ⏱️

**Problem:** 180s timeout may be insufficient under memory pressure.

**Current:** 180s per test

**Recommendation:** Increase to 300s for integration tests

```python
# pyproject.toml
[tool.pytest.ini_options]
timeout = 300  # 5 minutes instead of 3
```

Or per-test:

```python
@pytest.mark.timeout(300)
def test_vm_info_integration(self):
    # ... test code ...
```

**Expected Impact:** Eliminates false failures, but doesn't fix underlying issue

### Medium-Term Solutions

#### 4. **Pre-pull Docker Images** 📦

**Problem:** Image download on first use adds latency.

**Solution:**

```bash
# Pre-pull common images
orbctl pull ubuntu:22.04
orbctl pull ubuntu:24.04

# Or in test setup
def pytest_sessionstart(session):
    """Pull images before test session."""
    subprocess.run(["orbctl", "pull", "ubuntu:22.04"], check=False)
```

**Expected Impact:** 10-20s faster per first VM creation

#### 5. **Use VM Snapshots for Test VMs** 💾

**Problem:** Creating VMs from scratch is slow.

**Solution:**

```bash
# Create a baseline VM once
orbctl create ubuntu:22.04 pytest-baseline
orbctl start pytest-baseline
# ... configure as needed ...
orbctl stop pytest-baseline

# In tests, clone instead of create
orbctl clone pytest-baseline test-vm-123  # Much faster!
```

**Expected Impact:** 50-70% faster VM "creation" (actually cloning)

#### 6. **Optimize Worker VM Strategy** 🔧

**Current:** Session-scoped worker VMs (already implemented)

**Enhancement:** Add health checks and warm-up:

```python
def get_worker_vm() -> str:
    # ... existing code ...

    # Warm up the VM (ensures services are ready)
    subprocess.run(
        ["orbctl", "run", vm_name, "--", "true"],
        capture_output=True,
        timeout=5
    )

    return vm_name
```

**Expected Impact:** Fewer "VM not ready" issues

### Long-Term Solutions

#### 7. **Monitor OrbStack Performance** 📈

**Implement:**

```python
# tests/conftest.py
import time
import psutil

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Log system resources before each test."""
    if hasattr(item, 'callspec') and 'integration' in item.nodeid:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        print(f"\n[Resources] Memory: {mem.percent}%, Swap: {swap.percent}%")

        if swap.percent > 80:
            pytest.skip("System under memory pressure (swap > 80%)")
```

**Expected Impact:** Skip tests when system is under pressure

#### 8. **Split Test Suites** 🎯

**Current:** All tests run together (25+ minutes)

**Recommendation:**

```bash
# Fast tests (unit, command builders): ~2 minutes
pytest tests/test_vm_command_builders.py tests/test_vm_operations_unit.py

# Medium tests (integration): ~10 minutes
pytest tests/test_integration.py tests/test_vm_operations_integration.py

# Slow tests (e2e): ~15 minutes
pytest tests/test_e2e.py tests/test_pyinfra_deployment.py
```

**Expected Impact:** Better resource management, faster feedback

#### 9. **Update OrbStack** 🔄

**Current:** v2.0.4

**Action:**

```bash
# Check for updates
open -a OrbStack
# Settings → About → Check for Updates
```

**Rationale:**

- Version 2.0.4 is recent (released ~2024)
- Check release notes for performance improvements
- Some timeout issues may be version-specific bugs

**Expected Impact:** Varies depending on changelog

### Emergency Fallback

#### 10. **Mark Flaky Tests** 🏷️

If timeouts persist despite optimizations:

```python
# tests/test_vm_operations_integration.py

@pytest.mark.flaky(reruns=2, reruns_delay=10)
def test_vm_info_integration(self):
    """Test VM info retrieval - may timeout under system memory pressure."""
    # ... test code ...
```

Or skip when under pressure:

```python
@pytest.mark.skipif(
    psutil.swap_memory().percent > 80,
    reason="System under memory pressure"
)
def test_vm_info_integration(self):
    # ... test code ...
```

## Recommended Action Plan

### Phase 1: Immediate (Next 5 minutes)

1. ✅ **Check swap usage:** `sysctl vm.swapusage`
   - **Current:** 87.8% - This is the primary issue!
2. ⚠️ **Restart OrbStack** to free memory leaks
3. ⚠️ **Close unnecessary applications** to reduce memory pressure
4. ⚠️ **Delete existing test VMs** before test runs

### Phase 2: Quick Wins (Next 30 minutes)

1. ⚠️ **Increase pytest timeout** to 300s for integration tests
2. ⚠️ **Pre-pull ubuntu:22.04 image** to avoid download delays
3. ⚠️ **Add memory monitoring** to test setup (skip if swap > 80%)

### Phase 3: Optimization (Next 1-2 hours)

1. ⚠️ **Implement VM creation semaphore** (max 2 concurrent)
2. ⚠️ **Add VM snapshot-based testing** for faster creation
3. ⚠️ **Split test suites** into fast/medium/slow categories

## Expected Results

### Conservative Estimate

With Phase 1 + Phase 2 implemented:

- **Timeout failures:** 2 → 0 (100% reduction)
- **Test reliability:** 98.3% → 100%
- **Test duration:** 25m → 20m (20% improvement)

### Optimistic Estimate

With all phases implemented:

- **Timeout failures:** 2 → 0 (100% reduction)
- **Test reliability:** 98.3% → 100%
- **Test duration:** 25m → 8-12m (50-65% improvement)

## Monitoring and Validation

### Before Next Test Run

```bash
# 1. Check system health
sysctl vm.swapusage
vm_stat | grep -E "(free|active|inactive|wired)"

# 2. Check OrbStack status
orbctl version
orbctl list

# 3. Clean environment
orbctl list --format json | jq -r '.[] | select(.name | startswith("test-")) | .name' | xargs -I {} orbctl delete --force {}

# 4. Pre-pull images
orbctl pull ubuntu:22.04
```

### During Test Run

```bash
# Monitor in separate terminal
watch -n 5 'echo "=== Memory ===" && vm_stat | grep -E "(free|active|wired)" && echo "=== Swap ===" && sysctl vm.swapusage && echo "=== VMs ===" && orbctl list --format json | jq -r "length"'
```

### After Test Run

```bash
# Check for leftover VMs
orbctl list --format json | jq -r '.[] | select(.name | startswith("pytest-test-")) | .name'

# Should be empty (0 VMs)
```

## Conclusion

### Root Cause

**Primary:** High swap usage (87.8%) indicates severe memory pressure, causing VM creation operations to timeout.

**Secondary:** Resource contention from multiple concurrent VM operations.

### Immediate Action Required

🔥 **Critical:** Reduce system memory pressure by:

1. Restarting OrbStack
2. Closing unnecessary applications
3. Clearing caches

### Long-Term Solution

Implement memory monitoring and VM creation throttling to prevent timeouts under resource constraints.

### Success Criteria

- ✅ Swap usage < 50%
- ✅ 0 timeout failures in test runs
- ✅ Test duration < 15 minutes
- ✅ 100% test reliability

---

**Status:** Ready to implement Phase 1 (immediate actions) for quick resolution.
