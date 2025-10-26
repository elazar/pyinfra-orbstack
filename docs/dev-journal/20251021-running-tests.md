# Running Tests

Quick reference for running tests in the PyInfra OrbStack project.

## Quick Start

```bash
# Fast unit tests (~19 seconds)
pytest -c .pytest-fast.ini

# All tests except expensive VM creation (~3-5 minutes)
pytest -m "not expensive"

# Full test suite with coverage (~8-21 minutes)
pytest

# Specific test file
pytest tests/test_connector.py

# Specific test
pytest tests/test_connector.py::TestOrbStackConnector::test_connect_success
```

## Test Categories

### Unit Tests (< 1 minute)
Tests that use mocks and don't require real VMs:
```bash
pytest -c .pytest-fast.ini
# or
pytest -m "unit"
```

**Includes**:
- `test_connector.py` - Connector unit tests with mocks
- `test_operations.py` - Operations structure tests
- `test_orbstack_cli_mocks.py` - CLI mock tests
- `test_vm_operations_unit.py` - Command construction tests

### Integration Tests (~5-10 minutes)
Tests using shared session VMs (minimal VM creation):
```bash
pytest -m "integration and not expensive"
```

**Includes**:
- `test_integration.py` - Component interaction tests
- `test_vm_operations_integration.py` - VM operations with real VMs
- `test_pyinfra_deployment.py` - PyInfra deployment tests

**Note**: These tests reuse session-scoped VMs (`shared_vm_basic`, `shared_vm_with_user`, `shared_vm_with_arch`) created once per test run.

### E2E Tests (~10-15 minutes)
Full end-to-end workflow tests:
```bash
pytest -m "e2e"
```

**Includes**:
- `test_e2e.py` - Full workflow tests
- `test_pyinfra_operations_e2e.py` - Operations E2E
- `test_connector_coverage_e2e.py` - Connector edge cases

### Expensive Tests (creates VMs)
Tests that create new VMs:
```bash
pytest -m "expensive"  # Run only expensive tests
pytest -m "not expensive"  # Skip expensive tests
```

## Coverage Reports

```bash
# Generate coverage report
pytest --cov=src/pyinfra_orbstack --cov-report=html

# View in browser
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=src/pyinfra_orbstack --cov-report=term-missing
```

## Common Workflows

### Development (fast feedback)
```bash
# Run unit tests after code changes
pytest -c .pytest-fast.ini

# Or skip expensive tests
pytest -m "not expensive"
```

### Pre-commit
```bash
# Run integration tests with shared VMs
pytest -m "not expensive"
```

### CI/CD

**Pull Request**:
```bash
pytest -m "not expensive"  # ~3-5 minutes
```

**Main Branch / Release**:
```bash
pytest  # Full suite ~8-21 minutes
```

## Test Fixtures

### Shared Session VMs

Tests can use session-scoped VMs to avoid creation overhead:

```python
def test_with_shared_vm(shared_vm_basic):
    """Uses shared VM created once per session."""
    result = run_command(shared_vm_basic, "echo test")
    assert result.success
```

**Available Fixtures**:
- `shared_vm_basic` - Basic Ubuntu 22.04 VM
- `shared_vm_with_user` - VM with custom user
- `shared_vm_with_arch` - VM with arm64 architecture

### Manual VM Tracking

```python
def test_with_new_vm(track_test_vm):
    """Creates new VM with automatic cleanup."""
    vm_name = "my-test-vm"
    track_test_vm(vm_name)  # Auto-cleanup on exit
    create_vm_with_retry("ubuntu:22.04", vm_name)
    # ... test logic ...
    # VM cleaned up automatically
```

## Troubleshooting

### Disk Space Issues

If tests fail with "No space left on device":

```bash
# Check current VMs
orbctl list

# Clean up test VMs
python scripts/cleanup_test_vms.py

# Or manually
orbctl delete --force <vm-name>
```

### Stuck VMs

```bash
# List all VMs
orbctl list

# Delete specific VM
orbctl delete --force <vm-name>

# Clean up all test VMs
python scripts/cleanup_test_vms.py
```

### Test Isolation

If tests interfere with each other:

1. Check if test properly uses `track_test_vm` or shared fixtures
2. Ensure cleanup is working (check `conftest.py`)
3. Run tests individually to isolate issues:
   ```bash
   pytest tests/test_file.py::test_name -v
   ```

## Performance Tips

1. **Use shared VMs** when possible (automatic via fixtures)
2. **Mark expensive tests** with `@pytest.mark.expensive`
3. **Run fast tests during development** (`pytest -c .pytest-fast.ini`)
4. **Use parameterized tests** to reduce duplication
5. **Clean up regularly** (`python scripts/cleanup_test_vms.py`)

## Test Markers Reference

| Marker | Description | Usage |
|--------|-------------|-------|
| `unit` | Unit tests, no VMs needed | `-m "unit"` |
| `integration` | Integration tests, uses shared VMs | `-m "integration"` |
| `e2e` | End-to-end tests | `-m "e2e"` |
| `slow` | Slow running tests | `-m "slow"` or `-m "not slow"` |
| `expensive` | Creates new VMs | `-m "expensive"` or `-m "not expensive"` |

## Example Test Run Output

```bash
$ pytest -m "not expensive"
============================= test session starts ==============================
platform darwin -- Python 3.12.10, pytest-8.4.1, pluggy-1.6.0

Cleaning up orphaned test VMs...
Found 0 orphaned VMs

collected 161 items / 12 deselected / 149 selected

tests/test_connector.py ..........................              [ 17%]
tests/test_operations.py .......                                [ 22%]
...

Cleaning up 3 test VMs...
============================= 149 passed in 180.32s ============================
```
