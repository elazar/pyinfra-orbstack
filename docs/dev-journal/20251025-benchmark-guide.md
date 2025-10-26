# Benchmark Guide

This guide explains how to use pytest-benchmark to track performance and detect regressions in the pyinfra-orbstack project.

## Quick Start

### Run Benchmarks

```bash
# Run all benchmarks
uv run pytest tests/test_benchmarks.py --benchmark-only

# Run specific benchmark
uv run pytest tests/test_benchmarks.py::TestCommandBuilderBenchmarks --benchmark-only

# Run benchmarks with comparison to previous runs
uv run pytest tests/test_benchmarks.py --benchmark-compare
```

## Understanding Benchmark Output

### Statistics Explained

```text
Name (time in ns)                         Min          Max         Mean      StdDev      Median
test_benchmark_vm_list_command        20.36ns    651.96ns     24.61ns     7.87ns     23.57ns
```

- **Min**: Fastest execution time
- **Max**: Slowest execution time
- **Mean**: Average execution time
- **StdDev**: Standard deviation (consistency indicator)
- **Median**: Middle value (less affected by outliers)
- **IQR**: Interquartile range (spread of middle 50%)
- **Outliers**: Number of unusual measurements
- **OPS**: Operations per second (higher is better)

### Performance Comparison

The numbers in parentheses show relative performance:

- `(1.0)` = baseline (fastest test)
- `(2.18)` = 2.18x slower than baseline
- `(0.46)` = 0.46x the operations/second of baseline

## Saving and Comparing Benchmarks

### Save Baseline

```bash
# Save current performance as baseline
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-save=baseline
```

### Compare Against Baseline

```bash
# Compare current performance to baseline
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline

# Show histogram comparison
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline --benchmark-histogram
```

### Autosave Results

```bash
# Automatically save each run with timestamp
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-autosave
```

## Benchmark Options

### Control Execution

```bash
# Run more rounds for better accuracy
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-min-rounds=10

# Set minimum time per test
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-min-time=0.001

# Disable garbage collection during benchmarks
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-disable-gc

# Warmup iterations before measuring
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-warmup=on
```

### Output Formats

```bash
# Generate histogram
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-histogram

# Export to JSON
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-json=results.json

# Verbose output
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-verbose
```

### Filtering

```bash
# Only run benchmarks (skip regular tests)
uv run pytest tests/test_benchmarks.py --benchmark-only

# Skip benchmarks (run regular tests only)
uv run pytest tests/test_benchmarks.py --benchmark-skip

# Run benchmarks in specific group
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-group-by=group
```

## Writing Benchmarks

### Basic Benchmark

```python
def test_benchmark_function(benchmark):
    """Benchmark a simple function."""
    result = benchmark(my_function, arg1, arg2)
    assert result == expected_value
```

### Benchmark with Setup

```python
def test_benchmark_with_setup(benchmark):
    """Benchmark with setup code."""
    # Setup (not timed)
    data = prepare_test_data()

    # Benchmark (timed)
    result = benchmark(process_data, data)

    # Assertions (not timed)
    assert result is not None
```

### Benchmark Lambda/Callable

```python
def test_benchmark_complex(benchmark):
    """Benchmark complex operation."""
    connector = OrbStackConnector(mock_state, mock_host)

    def operation():
        success, output = connector.run_shell_command("echo test")
        return success

    result = benchmark(operation)
    assert result is True
```

### Benchmark Groups

```python
@pytest.mark.benchmark(group="command-builders")
class TestCommandBuilderPerformance:
    """Compare performance of related functions."""

    def test_simple(self, benchmark):
        benchmark(simple_function)

    def test_complex(self, benchmark):
        benchmark(complex_function)
```

## Performance Targets

### Command Builders (Unit)

**Target**: < 1 microsecond (1,000 ns)

- Simple commands (list, info): ~20-60 ns
- Commands with args (start, stop): ~40-110 ns
- Complex commands (create): ~200-500 ns

### Connector Operations (Mocked)

**Target**: < 100 microseconds (100,000 ns)

- make_names_data: ~1-10 µs
- connect: ~1-10 µs
- run_shell_command: ~1-10 µs

### Integration Operations (Real)

**Target**: < 1 second

- VM list: ~50-200 ms
- VM info: ~50-200 ms
- Command execution: ~100-500 ms

## Detecting Regressions

### Automatic Regression Detection

```bash
# Fail if performance degrades by more than 10%
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline --benchmark-compare-fail=mean:10%

# Fail if min time increases by more than 20%
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline --benchmark-compare-fail=min:20%
```

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Run benchmarks
  run: |
    uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-autosave

- name: Compare with baseline
  run: |
    uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=0001 --benchmark-compare-fail=mean:15%
```

## Benchmark Storage

Benchmarks are saved in `.benchmarks/` directory:

```text
.benchmarks/
├── Darwin-CPython-3.12-64bit/
│   ├── 0001_baseline.json
│   ├── 0002_20251023_150000.json
│   └── 0003_20251023_160000.json
└── .benchmarks-history/
```

### Managing Benchmark History

```bash
# List saved benchmarks
uv run pytest-benchmark list

# Compare specific benchmarks
uv run pytest-benchmark compare 0001 0002

# Delete old benchmarks
rm -rf .benchmarks/
```

## Best Practices

### 1. Isolate What You're Measuring

```python
# Good: Only benchmark the operation
def test_benchmark_operation(benchmark):
    connector = OrbStackConnector(mock_state, mock_host)  # Setup
    result = benchmark(connector.connect)  # Benchmark
    assert result is True  # Assertion

# Bad: Benchmark includes setup
def test_benchmark_bad(benchmark):
    def everything():
        connector = OrbStackConnector(mock_state, mock_host)
        return connector.connect()
    result = benchmark(everything)
```

### 2. Use Appropriate Markers

```python
# Mark slow benchmarks
@pytest.mark.slow
@pytest.mark.integration
def test_benchmark_real_vm(benchmark):
    """Benchmark real VM operations."""
    pass
```

### 3. Consistent Test Environment

- Run benchmarks on the same machine
- Close unnecessary applications
- Use `--benchmark-disable-gc` for consistency
- Run multiple rounds: `--benchmark-min-rounds=10`

### 4. Meaningful Assertions

```python
def test_benchmark_with_validation(benchmark):
    """Benchmark and validate results."""
    result = benchmark(build_vm_create_command, "test", "ubuntu:22.04")

    # Validate the result is correct
    assert "orbctl create" in result
    assert "test" in result
    assert "ubuntu:22.04" in result
```

## Troubleshooting

### Benchmarks Too Fast

If benchmarks complete in nanoseconds, pytest-benchmark will run many iterations:

```python
# This is normal for simple functions
def test_fast_benchmark(benchmark):
    result = benchmark(lambda: "test")  # Runs 100,000+ times
```

### Benchmarks Too Slow

For slow operations, reduce rounds:

```python
@pytest.mark.benchmark(min_rounds=1, max_time=5.0)
def test_slow_benchmark(benchmark):
    result = benchmark(slow_operation)
```

### Inconsistent Results

High standard deviation indicates inconsistency:

```bash
# Use warmup and disable GC
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-warmup=on --benchmark-disable-gc
```

## Example Workflow

### 1. Establish Baseline

```bash
# Run benchmarks and save as baseline
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-save=baseline --benchmark-autosave
```

### 2. Make Changes

```bash
# Edit code, make improvements
vim src/pyinfra_orbstack/connector.py
```

### 3. Compare Performance

```bash
# Run benchmarks and compare
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline

# Generate histogram
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline --benchmark-histogram
```

### 4. Detect Regressions

```bash
# Fail if performance degrades
uv run pytest tests/test_benchmarks.py --benchmark-only --benchmark-compare=baseline --benchmark-compare-fail=mean:10%
```

## Summary

- **Run benchmarks**: `pytest tests/test_benchmarks.py --benchmark-only`
- **Save baseline**: `--benchmark-save=baseline`
- **Compare**: `--benchmark-compare=baseline`
- **Detect regressions**: `--benchmark-compare-fail=mean:10%`
- **Generate reports**: `--benchmark-histogram` or `--benchmark-json=results.json`

Benchmarks help track performance over time and catch regressions before they reach production!
