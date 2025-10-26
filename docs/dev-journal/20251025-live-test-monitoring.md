# Live Test Monitoring

This document explains how to monitor test execution in real-time using pytest's built-in features and plugins.

## The Challenge

Standard pytest only shows test results **after** tests complete. When running slow tests (e.g., VM creation taking 30+ seconds), you have limited visibility into:
- Whether tests are progressing or hung
- Overall progress through the test suite
- Which tests are taking the longest

## The Solution: Combine Existing Tools

While pytest doesn't natively show elapsed time **during** test execution, combining several tools provides effective monitoring:

## Monitoring Tools

### 1. pytest-progress (Progress Bar)

Shows a live progress bar with test counts:

```bash
# Enable progress bar
uv run pytest --show-progress

# With verbose output
uv run pytest --show-progress -v
```

**Output:**
```
Progress: 45/290 [15%] | ✓ 42 | ✗ 2 | ⊘ 1
```

### 2. pytest-monitor (Performance Metrics)

Collects detailed performance data for each test:

```bash
# Automatically enabled - data saved to .pymon SQLite database
uv run pytest tests/

# View collected data
sqlite3 .pymon "SELECT item, item_start_time, total_time, mem_usage FROM TEST_METRICS ORDER BY total_time DESC LIMIT 10;"
```

**Metrics collected:**
- Execution time
- CPU usage
- Memory usage (peak and average)
- System context switches

### 3. pytest-timeout (Prevent Hung Tests)

Automatically kills tests that exceed a time limit:

```bash
# Set global timeout (in pyproject.toml or command line)
uv run pytest --timeout=120  # Kill tests after 2 minutes

# Per-test timeout
@pytest.mark.timeout(60)
def test_slow_operation():
    pass
```

### 4. pytest-xdist (Parallel Execution)

Run tests in parallel for faster completion:

```bash
# Use all CPU cores
uv run pytest -n auto

# Use specific number of workers
uv run pytest -n 4

# With live timer
uv run pytest -n auto -v
```

**Output shows which worker is running which test:**
```
[gw0] PASSED tests/test_connector.py::test_connect
[gw1] PASSED tests/test_vm.py::test_create
[gw2] [ 45%] tests/test_integration.py::test_list
```

### 5. pytest-instafail (Immediate Failure Display)

Shows failures immediately instead of waiting until the end:

```bash
# Already enabled in pyproject.toml
uv run pytest tests/
```

## Recommended Combinations

### For Development (Fast Feedback)
```bash
# Progress bar + verbose + instant failures + parallel execution
uv run pytest --show-progress -v -n auto tests/test_connector.py
```

### For CI/CD (Comprehensive)
```bash
# Parallel execution + timeout protection + performance monitoring
uv run pytest -n auto --timeout=300 tests/
```

### For Performance Analysis
```bash
# Benchmarks + monitoring + detailed timing
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-save=baseline
```

### For Long-Running Integration Tests
```bash
# Progress bar + verbose + timeout protection
uv run pytest tests/test_integration.py -v --show-progress --timeout=600
```

### For Maximum Visibility
```bash
# All monitoring tools enabled
uv run pytest -v --show-progress --durations=20 --timer-top-n=20 tests/
```

## Monitoring Long-Running Tests

For tests that create VMs or perform slow operations:

### Option 1: Use Progress Bar + Parallel Execution (Recommended)
```bash
# See progress and speed up execution
uv run pytest tests/test_e2e.py -v --show-progress -n auto
```

### Option 2: Add Progress Logging
```python
def test_vm_lifecycle():
    print("Creating VM...")  # Use -s flag to see immediately
    create_vm()
    print("VM created, testing connectivity...")
    test_connectivity()
    print("Cleaning up...")
```

Run with:
```bash
uv run pytest tests/test_e2e.py -v -s  # -s shows print statements
```

### Option 3: Monitor System Activity
```bash
# Terminal 1: Run tests
uv run pytest tests/ -v

# Terminal 2: Monitor OrbStack
watch -n 1 'orbctl list'

# Terminal 3: Monitor pytest process
watch -n 1 'ps aux | grep pytest'
```

## Default Configuration

The project's `pyproject.toml` includes these defaults:

```toml
[tool.pytest.ini_options]
addopts = [
    "-v",              # Verbose output
    "--instafail",     # Show failures immediately
    "--durations=10",  # Show 10 slowest tests
    "--timer-top-n=10", # Show timing percentages
]
```

This means every test run automatically includes:
- Verbose output showing each test as it runs
- Immediate failure reporting
- Post-run timing analysis

## Troubleshooting

### Progress Bar Not Showing

**Problem:** No progress bar appears

**Solutions:**
1. Ensure pytest-progress is installed: `uv add --dev pytest-progress`
2. Use the `--show-progress` flag: `pytest --show-progress`
3. Progress bar may not work well with parallel execution (`-n`)

### Tests Seem Hung

**Problem:** Test appears to be stuck

**Solutions:**
1. Use timeout protection: `pytest --timeout=300`
2. Run in another terminal: `watch -n 1 'orbctl list'` to monitor OrbStack
3. Check system resources: `top` or Activity Monitor

### Too Much Output

**Problem:** Too much information displayed

**Solution:** Use selective flags:
```bash
# Minimal output
pytest -q tests/

# Only show failures
pytest --tb=short tests/

# Quiet with progress
pytest -q --show-progress tests/
```

## Summary

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **pytest-progress** | Progress bar with test counts | Want overall progress visibility |
| **pytest-monitor** | Performance metrics collection | Performance analysis, regression detection |
| **pytest-timeout** | Kill hung tests | Prevent infinite loops, CI/CD safety |
| **pytest-xdist** | Parallel execution | Speed up test suite |
| **pytest-instafail** | Immediate failure display | Quick feedback on failures |
| **pytest-timer** | Post-run timing percentages | Identify slow tests after completion |
| **--durations** | Post-run slowest tests | Find performance bottlenecks |

## Key Takeaway

While pytest doesn't show elapsed time **during** test execution, combining these tools provides effective monitoring:

- **Progress visibility**: `--show-progress` shows how far along you are
- **Faster execution**: `-n auto` reduces total wait time
- **Timeout protection**: `--timeout=N` prevents hung tests
- **Detailed analysis**: `--durations` and `--timer-top-n` show timing after completion

**Recommended command for maximum visibility:**
```bash
uv run pytest -v --show-progress -n auto --timeout=300 tests/
```
