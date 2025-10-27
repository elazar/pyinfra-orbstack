# ADR-0005: Intelligent Retry Logic for OrbStack Operations

**Date:** 2025-10-27
**Status:** Accepted
**Deciders:** Project Maintainers
**Type:** Architecture Decision Record

## Context

OrbStack CLI operations are network-dependent and inherently subject to transient failures:

### Observed Failure Modes

1. **Network Timeouts**: Image downloads from registries can timeout
2. **TLS Handshake Failures**: Intermittent TLS negotiation issues with image registries
3. **Connection Failures**: CDN or mirror availability issues
4. **VM Creation Hangs**: OrbStack CLI can hang without returning (requires timeout handling)
5. **"Already Exists" Errors**: VM created successfully but command hung, retry fails with "already exists"
6. **DNS Resolution Issues**: Temporary DNS failures affecting image pulls

### Initial Test Failures Without Retry Logic

Without retry logic, test suite had:
- **~10% failure rate** on clean runs
- **Network-related failures** causing false negatives
- **Inconsistent CI results** depending on network conditions
- **Developer frustration** with intermittent test failures

### The "Already Exists" Problem

A particularly tricky failure mode:

```
Attempt 1: orbctl create ubuntu:22.04 test-vm
           → Hangs for 180 seconds, times out
           → VM actually IS created (command just didn't return)

Attempt 2: orbctl create ubuntu:22.04 test-vm
           → Returns immediately: "VM already exists"
           → Test fails even though VM is usable
```

## Decision

We implemented an **intelligent retry strategy** with exponential backoff, error classification, and special handling for edge cases.

### Architecture

#### 1. Exponential Backoff Retry Logic

```python
def execute_orbctl_with_retry(
    cmd: List[str],
    operation_name: str,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> Tuple[int, str, str]:
    """
    Execute orbctl command with intelligent retry logic.

    Retries on:
    - Network errors (timeout, connection, TLS, DNS)
    - Transient OrbStack errors (missing IP, didn't start)
    - Command timeouts

    Does NOT retry on:
    - User errors (invalid parameters)
    - Permanent failures (VM already exists - handled separately)
    """
```

**Retry Schedule**:
- Attempt 1: Execute immediately
- Attempt 2: Wait 2 seconds (base_delay × 2^0)
- Attempt 3: Wait 4 seconds (base_delay × 2^1)
- Attempt 4: Wait 8 seconds (base_delay × 2^2)

#### 2. Intelligent Error Classification

Errors are classified as retriable or permanent based on keyword analysis:

```python
# Retriable error keywords
retriable_keywords = [
    # Network errors
    "timeout", "connection", "network", "dns",
    "tls", "handshake", "http", "https", "tcp",

    # Download/registry errors
    "download", "cdn", "registry", "pull",

    # OrbStack-specific transient errors
    "missing ip address",
    "didn't start",
    "machine setup",
]

error_msg = result.stderr.lower()
is_retriable = any(keyword in error_msg for keyword in retriable_keywords)

if is_retriable and attempt < max_retries:
    delay = base_delay * (2 ** attempt)
    time.sleep(delay)
    continue  # Retry
else:
    return result  # Permanent failure or max retries exceeded
```

#### 3. Differentiated Timeouts

Different operations have different timeout requirements:

```python
# Default timeout
timeout = 60

# VM creation and import operations need more time
operation_lower = operation_name.lower()
if any(op in operation_lower for op in ["creat", "clone", "import"]):
    timeout = 180  # 3 minutes for VM creation
```

**Rationale**:
- VM creation involves downloading images, which can be slow
- Other operations (start, stop, info) are local and should complete quickly
- Longer timeout for creation prevents false timeouts on slow networks

#### 4. "Already Exists" Handler

Special logic to handle VMs created but command hung:

```python
def create_vm_with_retry(vm_name: str, image: str, ...) -> bool:
    returncode, stdout, stderr = execute_orbctl_with_retry(
        cmd, operation_name=f"VM creation ({vm_name})"
    )

    if returncode == 0:
        return True

    # Check if failure is because VM already exists
    if "already exists" in stderr.lower():
        # VM was likely created but command hung
        # Verify VM exists and is usable
        check_result = subprocess.run(
            ["orbctl", "info", vm_name],
            capture_output=True, timeout=30
        )

        if check_result.returncode == 0:
            # VM exists and is usable - start it
            if start_vm_with_retry(vm_name):
                return True  # Success!

    return False  # Genuine failure
```

#### 5. Comprehensive Logging

Detailed logging for debugging transient issues:

```python
# On retry
print(f"Executing {operation_name} "
      f"(attempt {attempt + 1}/{max_retries + 1}, "
      f"timeout={timeout}s)")

# On retriable error
print(f"Transient error in {operation_name}, "
      f"retrying in {delay}s: {error_msg}")

# On timeout
print(f"{operation_name} timed out, "
      f"retrying in {delay}s")

# On final failure
print(f"{operation_name} failed after {max_retries + 1} attempts")
```

### Test Impact

**Before Retry Logic**:
- 10% test failure rate
- Manual re-runs required
- CI unreliable

**After Retry Logic**:
- <1% test failure rate
- Automatic recovery from transient issues
- Reliable CI results

**Test Suite Results**: 287 passed, 0 failed, 3 skipped (100% pass rate)

## Consequences

### Positive Consequences

1. **Reliable Test Suite**: 10% → <1% failure rate
2. **Automatic Recovery**: Transient failures resolved without manual intervention
3. **Better Developer Experience**: Fewer frustrating intermittent failures
4. **CI Stability**: Consistent CI results despite network variability
5. **Network Resilience**: Tests work across different network conditions
6. **Clear Diagnostics**: Comprehensive logging aids debugging when genuine failures occur
7. **Edge Case Handling**: "Already exists" handler prevents false failures

### Negative Consequences

1. **Slower Failure Detection**: Genuine failures take longer to surface (up to 4 retries)
2. **Increased Test Duration**: Retries add time when operations fail
3. **Complexity**: Retry logic adds code complexity
4. **Masked Problems**: Might hide underlying OrbStack stability issues
5. **Resource Usage**: Retries consume more OrbStack resources

### Trade-offs

- **Speed vs. Reliability**: Accept slower failure detection for reliable test results
- **Simplicity vs. Robustness**: More complex code for handling real-world network conditions
- **Immediate Feedback vs. Resilience**: Retry delays balanced against automatic recovery
- **Error Visibility vs. Noise**: Comprehensive logging balanced against log verbosity

## Alternatives Considered

### Alternative 1: No Retry Logic (Original Approach)

**Rejected** - 10% test failure rate was unacceptable. Required manual re-runs and caused CI unreliability.

### Alternative 2: Simple Retry Without Error Classification

```python
for attempt in range(max_retries):
    result = subprocess.run(cmd)
    if result.returncode == 0:
        return result
    time.sleep(2)  # Always retry
```

**Rejected** - Retries permanent errors (invalid parameters, VM already exists normally). Wastes time on unretriable failures.

### Alternative 3: Fixed Delay Instead of Exponential Backoff

```python
time.sleep(5)  # Always wait 5 seconds
```

**Rejected** - Wastes time on quickly-resolved transients. Exponential backoff gives network time to recover for persistent issues while being fast for transients.

### Alternative 4: Longer Timeouts Instead of Retries

```python
timeout = 600  # 10 minutes for everything
```

**Rejected** - Doesn't help with transient network issues that resolve on retry. Lengthens test duration unnecessarily. Timeout analysis showed timeouts weren't the root cause.

### Alternative 5: Fail Fast Without Recovery

**Rejected** - Network-dependent operations inherently experience transient failures. Failing fast would require developers to manually re-run tests constantly.

### Alternative 6: External Retry Wrapper (pytest plugin)

```python
@pytest.mark.flaky(reruns=3)
def test_vm_creation():
    ...
```

**Rejected** - Retries entire test (including test setup/teardown), not just the failing operation. Less granular and efficient than operation-level retries.

## Implementation Notes

### Files Modified

- `tests/test_utils.py`: Core retry logic in `execute_orbctl_with_retry()`
- `tests/test_utils.py`: "Already exists" handling in `create_vm_with_retry()`
- `tests/test_utils.py`: Applied to all OrbStack operations (create, delete, start, stop)

### Retry Parameters

Configurable but with sensible defaults:
- **max_retries**: 3 (total 4 attempts)
- **base_delay**: 2 seconds
- **timeout**: 60s default, 180s for creation/import

### Error Keyword Maintenance

The retriable error keyword list should be updated as new failure modes are discovered:

```python
# Add new keywords as OrbStack error messages evolve
retriable_keywords = [
    # ... existing keywords ...
    "new_error_pattern",  # Document what this catches
]
```

### Logging Configuration

Logging can be adjusted for debugging vs. production:
- **Development**: Verbose logging for debugging
- **CI**: Quieter logging to reduce log noise
- **Production**: Error logging only

## References

- [Bug Fix Complete Success](../dev-journal/20251025-bug-fix-complete-success.md) - Implementation of timeout fix and "already exists" handler
- [Timeout Analysis](../dev-journal/20251025-timeout-analysis-not-about-time.md) - Analysis showing timeouts weren't the root cause
- [Diagnostic Results Analysis](../dev-journal/20251025-diagnostic-results-analysis.md) - Analysis of failure modes leading to retry logic design
- [Test Implementation Analysis](../dev-journal/20250817-test-implementation-analysis.md) - Initial network resilience features

## Related ADRs

- [ADR-0004: Session-Scoped Test VM Management](0004-session-scoped-test-vms.md) - Test VM management that benefits from reliable VM creation with retry logic
- [ADR-0003: Multi-Level Testing Strategy](0003-multi-level-testing-strategy.md) - Testing strategy that relies on reliable test execution
