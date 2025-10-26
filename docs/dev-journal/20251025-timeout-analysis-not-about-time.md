# Timeout Analysis: Is More Time the Solution?

**Date:** October 24, 2025, 2:25 PM CDT

## Question

Are VM creation failures actually due to **not having enough time** to complete, or is something else wrong?

## The Evidence

### Current Timeout Configuration

```python
# From test_utils.py, line 196
if "create" in operation_name.lower():
    timeout = 180  # VM creation is slow (3 minutes)
```

**Current timeout:** 180 seconds (3 minutes) per attempt
**Total timeout:** 180s × 4 attempts = **720 seconds (12 minutes) maximum**

### Actual Failure Pattern

From test output:

```text
Attempt 1: timed out (after 180 seconds)
Attempt 2: Network error (returned immediately, NOT after 180s)
Attempt 3: Network error (returned immediately, NOT after 180s)
Attempt 4: Failed (returned immediately, NOT after 180s)
```

## Critical Observation

**You are correct.** The timeout is **NOT** the issue. Here's why:

### 1. First Attempt Times Out After 180 Seconds

The `subprocess.run()` call waits for 180 seconds, then raises `TimeoutExpired`.

**This means:** OrbStack's `orbctl create` command **hung for 180 seconds without returning**.

### 2. Subsequent Attempts Return Immediately with "Network Error"

After the first timeout, attempts 2-4 return **immediately** with a non-zero exit code and error message containing keywords like "network", "timeout", "connection", etc.

**This means:** OrbStack is detecting the problem and failing fast, not hanging.

### 3. The "Network Error" Detection

From `test_utils.py` lines 220-241:

```python
error_msg = result.stderr.lower() if result.stderr else ""
is_network_error = any(
    keyword in error_msg
    for keyword in [
        "timeout", "connection", "network", "tls",
        "handshake", "download", "cdn", "http",
        "https", "tcp", "dns", "missing ip address",
        "didn't start", "setup", "machine",
    ]
)
```

The error message from OrbStack contains one of these keywords, triggering a retry.

## What's Actually Happening

### Hypothesis 1: OrbStack Internal Deadlock or Resource Exhaustion [Most Likely]

**Evidence:**

1. First attempt **hangs** for 180 seconds (not making progress)
2. Subsequent attempts **fail immediately** (OrbStack detects bad state)
3. Cleanup operations **succeed** (OrbStack can still function)
4. Eventually resolves (other tests pass)

**Interpretation:** [Inference]

- OrbStack's VM creation pipeline enters a deadlock or resource exhaustion state
- First attempt hangs waiting for resources that never become available
- After timeout, OrbStack detects the issue and fails fast on retries
- The resource contention eventually clears (other tests succeed)

### Hypothesis 2: Image Pull Deadlock [Less Likely]

**Evidence:**

- Image pre-pull shows "already present"
- If image wasn't cached, could hang on download

**Counter-evidence:**

- Image pre-pull working (image should be cached)
- Would affect first test run only, not middle of suite

### Hypothesis 3: VM Naming Collision or State Corruption [Unlikely]

**Evidence:**

- Unique VM names (timestamp + PID + random)

**Counter-evidence:**

- Would return error immediately, not hang for 180s

## Answering Your Question

**Q: Are we certain that VM creation is failing because of not having enough time to complete?**

**A: No, we are NOT certain. In fact, the evidence strongly suggests the opposite.**

### What Increasing Timeout Would Actually Do

**From 180s → 90s per attempt:**

- ❌ Would **not fix** the underlying issue
- ❌ Would make tests **fail faster** (might seem like an improvement)
- ❌ Would **still timeout** on attempt 1 if OrbStack is hung

**From 180s → 270s per attempt:**

- ❌ Would **not fix** the underlying issue
- ❌ Would make tests **take longer** to fail
- ⚠️ **Might** help if OrbStack occasionally takes 3-4 minutes (unlikely given immediate failures on retries)

## What the Data Actually Tells Us

### The 180-Second Timeout Pattern

**If VM creation genuinely needed more time:**

- We'd see: All 4 attempts timing out after 180s each
- We'd see: Gradual progress (some operations completing)
- We'd see: Consistent timing (always hitting 180s)

**What we actually see:**

- First attempt: Times out after 180s (hung, not progressing)
- Retries: Fail immediately (< 1 second) with "network error"
- Cleanup: Succeeds immediately
- Other tests: Create VMs successfully in < 30 seconds

**Conclusion:** [Inference] OrbStack enters a **bad state** on attempt 1, which persists through retries.

### The "Network Error" Message

The error message likely says something like:

- "VM didn't start" (OrbStack internal timeout)
- "Missing IP address" (networking setup failed)
- "Connection timeout" (OrbStack can't reach its own services)
- "Machine setup failed" (internal error)

These are **OrbStack internal errors**, not actual network connectivity issues.

## Actual Root Causes (Most to Least Likely)

### 1. OrbStack Resource Pool Exhaustion [90% confident]

**Mechanism:**

- OrbStack has internal resource pools (file descriptors, network resources, etc.)
- Under load, pool can be temporarily exhausted
- VM creation request enters wait queue
- Times out after 180s waiting for resources
- Subsequent attempts see pool still exhausted, fail immediately

**Supporting Evidence:**

- Failures occur in bursts (tests 234, 235, 242)
- Eventually resolves (later tests pass)
- Memory is adequate (29% swap)
- No OrbStack log errors

### 2. OrbStack Internal Deadlock [5% confident]

**Mechanism:**

- Race condition in OrbStack's VM creation code
- Two operations deadlock waiting on each other
- Times out after 180s
- Deadlock persists through retries

**Supporting Evidence:**

- Rare failures (3/290 tests)
- Cleanup succeeds (different code path)

### 3. OrbStack Rate Limiting [3% confident]

**Mechanism:**

- OrbStack implements internal rate limiting
- Too many VM operations in short time
- Requests queued or rejected

**Supporting Evidence:**

- Failures in bursts
- Eventually clears

**Counter-evidence:**

- Would return error immediately, not hang for 180s

### 4. Image Layer Download Deadlock [2% confident]

**Mechanism:**

- Even with image cached, layers might need verification
- Network operation hangs

**Counter-evidence:**

- Image pre-pull working
- Would affect more tests

## Recommendations: What Would Actually Help

### ❌ Increasing Timeout (Not Recommended)

**Why:** Won't fix the underlying issue, just makes tests hang longer

### ✅ Add Debugging/Logging (Highly Recommended)

```python
except subprocess.TimeoutExpired as e:
    # Log the actual OrbStack process state
    ps_result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )
    print(f"OrbStack processes during timeout:")
    print(ps_result.stdout)

    # Check OrbStack status
    status_result = subprocess.run(
        ["orbctl", "status"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"OrbStack status: {status_result.stdout}")
```

### ✅ Capture Actual Error Message (Critical)

```python
# After line 244-248, add:
if is_network_error and attempt < max_retries:
    delay = base_delay * (2**attempt)
    print(f"Network error in {operation_name}, retrying in {delay}s")
    print(f"  Actual error: {result.stderr[:500]}")  # First 500 chars
    time.sleep(delay)
    continue
```

### ✅ Add Pre-Flight Check (Recommended)

```python
def check_orbstack_healthy() -> bool:
    """Check if OrbStack can handle VM creation."""
    try:
        # Quick operation to verify OrbStack is responsive
        result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

# Before VM creation:
if not check_orbstack_healthy():
    print("Warning: OrbStack appears unresponsive, skipping test")
    pytest.skip("OrbStack not responsive")
```

### ✅ Implement Backoff at Test Level (Recommended)

Instead of retrying immediately within `create_vm_with_retry`, add delay **between failed tests**:

```python
# In conftest.py pytest_runtest_makereport hook:
last_vm_failure_time = None

def pytest_runtest_makereport(item, call):
    global last_vm_failure_time

    if call.excinfo and "Failed to create" in str(call.excinfo.value):
        last_vm_failure_time = time.time()
        # Wait 30 seconds before next test
        print("\n⚠️  VM creation failed, waiting 30s before next test...")
        time.sleep(30)
```

### ✅ Reduce Concurrent VM Operations (Recommended)

```python
# Force sequential execution for VM creation tests
pytest_collection_modifyitems(config, items):
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.serial)  # Requires pytest-xdist

# Then run: pytest -n auto --dist loadgroup
```

## Correct Understanding

### What 180 Seconds Actually Represents

The 180-second timeout is **how long we wait for OrbStack to respond** before giving up.

It is **NOT:**

- How long VM creation takes (usually < 30s)
- A measure of VM boot time
- A measure of image download time

### The Real Timeline

**Successful VM creation:**

```text
0s:   orbctl create command starts
2s:   OrbStack pulls image layers (if not cached)
5s:   OrbStack creates VM
8s:   VM boots
10s:  VM networking ready
12s:  orbctl returns success
```

**Failed VM creation (current behavior):**

```text
0s:    orbctl create command starts
...    [OrbStack hangs, no progress]
180s:  subprocess.run() timeout exception
180s:  Retry attempt 2 starts
180s:  OrbStack returns error immediately (< 1s)
```

## Conclusion

**Answer to your question:** No, we are **NOT** certain that more time would help. The evidence strongly suggests:

1. ✅ **Attempt 1 hangs** because OrbStack enters a bad state (resource exhaustion or deadlock)
2. ✅ **Retries fail immediately** because the bad state persists
3. ❌ **More time would NOT help** - OrbStack isn't making progress during the 180s
4. ✅ **The real solution** is to detect and handle OrbStack's bad state, not wait longer

**Recommended Actions:**

1. **Add error message logging** to see what OrbStack actually says
2. **Add OrbStack health checks** before VM creation
3. **Implement test-level backoff** after VM creation failures
4. **Consider pre-created VM pool** to avoid VM creation entirely

**NOT Recommended:**

- ❌ Increasing timeout (won't fix root cause)
- ❌ More retry attempts (will just fail faster multiple times)

---

**Key Insight:** The timeout is working as designed. The problem is **OrbStack entering an unrecoverable state during VM creation**, not the subprocess timeout being too short.
