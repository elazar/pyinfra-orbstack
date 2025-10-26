# Test Timing Guide

This document explains how to view test timing information in the pyinfra-orbstack project.

## Built-in Timing Features

### 1. Show Slowest Tests (--durations)

pytest's built-in `--durations` flag shows the slowest tests after the run completes:

```bash
# Show 10 slowest tests
uv run pytest --durations=10

# Show all test durations
uv run pytest --durations=0

# Show durations with minimum threshold (e.g., only tests > 1 second)
uv run pytest --durations=0 --durations-min=1.0
```

**Output Example:**

```text
================================================= slowest 10 durations ==================================================
2.01s call     tests/test_connector.py::TestOrbStackConnector::test_execute_with_retry_max_retries_exceeded
2.01s call     tests/test_connector.py::TestOrbStackConnector::test_execute_with_retry_max_retries_exceeded
0.52s call     tests/test_integration.py::TestOrbStackIntegration::test_connector_run_shell_command
```

### 2. pytest-timer Plugin

The `pytest-timer` plugin shows timing percentages for each test:

```bash
# Show top 10 tests with timing percentages
uv run pytest --timer-top-n=10

# Show top 20 tests
uv run pytest --timer-top-n=20

# Show all tests with timing
uv run pytest --timer-top-n=0
```

**Output Example:**

```text
===================================================== pytest-timer ======================================================
[success] 99.85% tests/test_connector.py::TestOrbStackConnector::test_execute_with_retry_max_retries_exceeded: 2.0061s
[success] 0.13% tests/test_connector.py::TestOrbStackConnector::test_connect_success: 0.0026s
[success] 0.02% tests/test_connector.py::TestOrbStackConnector::test_run_shell_command_success: 0.0005s
```

### 3. Verbose Output (-v)

Use `-v` or `-vv` for more detailed output including test names as they run:

```bash
# Show test names as they run
uv run pytest -v

# Show even more detail
uv run pytest -vv
```

## Default Configuration

The project's `pyproject.toml` is configured to automatically show timing information:

```toml
[tool.pytest.ini_options]
addopts = [
    "--durations=10",      # Show 10 slowest tests
    "--timer-top-n=10",    # Show top 10 tests with timing percentages
]
```

This means every test run will show timing information by default.

## Useful Combinations

### Quick Test with Timing

```bash
# Run specific test file with timing
uv run pytest tests/test_connector.py -v

# Run specific test with timing
uv run pytest tests/test_connector.py::TestOrbStackConnector::test_connect_success -v
```

### Integration Tests with Timing

```bash
# Run only integration tests with timing
uv run pytest -m integration -v

# Run integration tests and show all durations
uv run pytest -m integration --durations=0
```

### Find Slow Tests

```bash
# Show only tests that take more than 1 second
uv run pytest --durations=0 --durations-min=1.0

# Show only tests that take more than 5 seconds
uv run pytest --durations=0 --durations-min=5.0
```

### Performance Regression Detection

```bash
# Run tests and save timing data
uv run pytest --durations=0 > test_timings_$(date +%Y%m%d).txt

# Compare with previous run to detect regressions
```

## Test Execution Time Breakdown

### Typical Test Times

**Unit Tests** (fast, < 0.1s each):

- Command builder tests: ~0.001s
- Mock-based connector tests: ~0.001-0.01s
- Operation tests: ~0.001s

**Integration Tests** (moderate, 0.1s - 5s each):

- VM lifecycle tests: ~0.5-2s
- File transfer tests: ~1-3s
- Network tests: ~0.5-1s

**E2E Tests** (slow, 5s - 30s each):

- Full VM creation/deletion: ~10-20s
- PyInfra deployment tests: ~5-15s
- Cross-VM communication: ~2-5s

**Retry/Timeout Tests** (slowest, > 2s each):

- Retry logic tests: ~2s (intentional delays)
- Timeout tests: ~1-5s (intentional timeouts)

### Total Test Suite Time

- **All tests**: ~18 minutes (276 tests)
- **Unit tests only**: ~5 seconds (200+ tests)
- **Integration tests only**: ~15 minutes (70+ tests)

## Historical Timing Data

pytest caches test results in `.pytest_cache/`. You can use this for:

1. **Rerun failed tests**: `pytest --lf` (last failed)
2. **Rerun failed tests first**: `pytest --ff` (failed first)
3. **Skip slow tests**: Use markers like `-m "not slow"`

## Tips for Faster Test Runs

1. **Run unit tests first** during development:

   ```bash
   uv run pytest tests/test_vm_command_builders.py tests/test_connector.py
   ```

2. **Skip integration tests** when not needed:

   ```bash
   uv run pytest -m "not integration"
   ```

3. **Run tests in parallel** (requires pytest-xdist):

   ```bash
   uv add --dev pytest-xdist
   uv run pytest -n auto  # Use all CPU cores
   ```

4. **Use test markers** to categorize tests:

   ```bash
   # Run only fast tests
   uv run pytest -m "not slow"

   # Run only expensive tests (VM creation)
   uv run pytest -m expensive
   ```

## Monitoring Test Performance

### Create a Performance Baseline

```bash
# Run all tests and save timing
uv run pytest --durations=0 --tb=no -q > baseline_timings.txt

# Later, compare new run
uv run pytest --durations=0 --tb=no -q > current_timings.txt
diff baseline_timings.txt current_timings.txt
```

### Watch for Regressions

Tests that suddenly take longer may indicate:

- Performance regressions in code
- Network/OrbStack issues
- Resource contention
- Flaky tests

## Performance Benchmarking

For detailed performance tracking and regression detection, see the [Benchmark Guide](20251025-benchmark-guide.md).

pytest-benchmark provides:

- Historical performance tracking
- Regression detection
- Statistical analysis (min/max/mean/stddev)
- Performance comparison between runs
- Automatic baseline comparisons

Quick benchmark example:

```bash
# Run benchmarks
uv run pytest tests/test_benchmarks.py --benchmark-only

# Save baseline
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-save=baseline

# Compare with baseline
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline
```

## Summary

- **Default**: Timing is shown automatically for top 10 slowest tests
- **Quick check**: Use `-v` to see test names as they run
- **Detailed analysis**: Use `--durations=0` to see all test times
- **Percentage view**: Use `--timer-top-n=0` to see timing percentages
- **Find slow tests**: Use `--durations-min=N` to filter by duration
- **Performance tracking**: Use `pytest-benchmark` for historical analysis (see [Benchmark Guide](20251025-benchmark-guide.md))

All timing features are configured by default in `pyproject.toml`, so you get timing information on every test run!
