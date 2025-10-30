# Operation Timing Guide

**Date:** 2025-10-28

This guide explains how to use the timing utility to monitor operation performance in pyinfra-orbstack.

## Overview

The timing utility provides a simple, consistent way to time operations using Python's standard logging infrastructure. No additional dependencies are required.

## Features

- **Context manager** for timing code blocks
- **Decorator** for timing functions
- **Standard logging** integration
- **Error handling** - logs timing even on failures
- **Zero dependencies** - uses only Python stdlib

## Quick Start

### Enable Timing Logs

```python
import logging

# Enable INFO level to see timing logs
logging.basicConfig(level=logging.INFO)
```

### Using the Context Manager

```python
from pyinfra_orbstack.timing import timed_operation

with timed_operation("vm_create"):
    # Your operation code here
    create_vm("my-vm")
```

**Output:**
```
INFO - Starting vm_create
INFO - Completed vm_create in 2.34s
```

### Using the Decorator

```python
from pyinfra_orbstack.timing import timed

@timed("vm_create")
def create_vm(name: str) -> bool:
    # Implementation
    return True

# Or use function name automatically
@timed
def another_operation():
    pass
```

## Detailed Usage

### Context Manager: `timed_operation()`

Best for timing specific code blocks:

```python
from pyinfra_orbstack.timing import timed_operation

def deploy_application():
    with timed_operation("package_installation"):
        install_packages()

    with timed_operation("configuration"):
        configure_services()

    with timed_operation("service_startup"):
        start_services()
```

### Decorator: `@timed`

Best for timing entire functions:

```python
from pyinfra_orbstack.timing import timed

@timed("database_backup")
def backup_database(db_name: str) -> str:
    """Backup database and return backup path."""
    # Implementation
    return f"/backups/{db_name}.sql"

# Call normally
backup_path = backup_database("production")
```

### Error Handling

Both timing utilities log timing even when operations fail:

```python
@timed("risky_operation")
def might_fail():
    raise ValueError("Something went wrong")

try:
    might_fail()
except ValueError:
    pass
```

**Output:**
```
INFO - Starting risky_operation
ERROR - Failed risky_operation after 0.05s: Something went wrong
```

## Logging Configuration

### Basic Configuration

```python
import logging

# Show all timing logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### File Logging

```python
import logging

# Log to file
logging.basicConfig(
    filename='operations.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Filtering Timing Logs

```python
import logging

# Only show timing logs from pyinfra_orbstack
logger = logging.getLogger('pyinfra_orbstack.timing')
logger.setLevel(logging.INFO)

# Add custom handler
handler = logging.FileHandler('timing.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(handler)
```

## Advanced Usage

### Nested Operations

```python
from pyinfra_orbstack.timing import timed_operation

with timed_operation("full_deployment"):
    with timed_operation("vm_setup"):
        create_vm()
        configure_vm()

    with timed_operation("application_deployment"):
        deploy_app()
```

**Output:**
```
INFO - Starting full_deployment
INFO - Starting vm_setup
INFO - Completed vm_setup in 5.23s
INFO - Starting application_deployment
INFO - Completed application_deployment in 3.45s
INFO - Completed full_deployment in 8.68s
```

### Custom Logging Levels

```python
import logging
from pyinfra_orbstack.timing import timed

# Use DEBUG level for detailed timing
logger = logging.getLogger('pyinfra_orbstack.timing')
logger.setLevel(logging.DEBUG)

@timed("debug_operation")
def debug_operation():
    pass
```

### Integration with PyInfra Deployments

```python
# deploy.py
import logging
from pyinfra import host
from pyinfra.operations import server
from pyinfra_orbstack.timing import timed_operation

# Enable timing logs
logging.basicConfig(level=logging.INFO)

# Time specific deployment phases
with timed_operation("package_installation"):
    server.packages(
        name="Install packages",
        packages=["nginx", "postgresql"],
    )

with timed_operation("service_configuration"):
    server.service(
        name="Start nginx",
        service="nginx",
        running=True,
    )
```

## Performance Analysis

### Analyzing Logs

Once you have timing logs, you can analyze them:

```bash
# Show all operation timings
grep "Completed" operations.log

# Find slow operations (>5 seconds)
grep "Completed" operations.log | awk '$NF > 5.0'

# Calculate average timing for an operation
grep "Completed vm_create" operations.log | \
  awk '{print $(NF-1)}' | awk '{s+=$1; n++} END {print s/n}'
```

### JSON Log Format

For structured logging analysis:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
        })

handler = logging.FileHandler('timing.json')
handler.setFormatter(JSONFormatter())

logger = logging.getLogger('pyinfra_orbstack.timing')
logger.addHandler(handler)
```

## Best Practices

### DO

- ✅ Enable timing logs during development and debugging
- ✅ Use context managers for granular timing
- ✅ Use decorators for reusable function timing
- ✅ Log to files for historical analysis
- ✅ Use descriptive operation names

### DON'T

- ❌ Time every trivial operation (adds noise)
- ❌ Leave timing enabled in performance-critical code
- ❌ Use timing as a replacement for proper monitoring
- ❌ Time operations that run in microseconds

## Examples

### Example 1: VM Lifecycle Timing

```python
from pyinfra_orbstack.timing import timed

@timed("vm_full_lifecycle")
def test_vm_lifecycle():
    with timed_operation("vm_create"):
        create_vm("test-vm")

    with timed_operation("vm_configure"):
        configure_vm("test-vm")

    with timed_operation("vm_destroy"):
        delete_vm("test-vm")
```

### Example 2: Deployment Performance

```python
import logging
from pyinfra_orbstack.timing import timed_operation

logging.basicConfig(level=logging.INFO)

phases = ["setup", "install", "configure", "verify"]

for phase in phases:
    with timed_operation(f"phase_{phase}"):
        run_deployment_phase(phase)
```

### Example 3: Comparing Operation Performance

```python
# Run same operation multiple times to compare
for i in range(5):
    with timed_operation(f"vm_create_run_{i}"):
        create_vm(f"test-vm-{i}")
        delete_vm(f"test-vm-{i}")
```

## Comparison with pytest-benchmark

**Use timing utility when:**
- Running production deployments
- Debugging performance issues
- Tracking real-world operation timing
- Logging for later analysis

**Use pytest-benchmark when:**
- Writing performance tests
- Comparing implementations
- Generating detailed performance reports
- CI/CD performance regression testing

See also: [Benchmark Guide](20251025-benchmark-guide.md)

## Troubleshooting

### Not Seeing Timing Logs

**Problem:** No timing output appears

**Solution:** Check logging configuration
```python
import logging

# Ensure INFO level is enabled
logging.basicConfig(level=logging.INFO)

# Check specific logger
logger = logging.getLogger('pyinfra_orbstack.timing')
logger.setLevel(logging.INFO)
```

### Timing Shows 0.00s

**Problem:** Very fast operations show as 0.00s

**Solution:** This is normal for sub-10ms operations. The timer rounds to 2 decimal places.

### Multiple Log Entries

**Problem:** Seeing duplicate log entries

**Solution:** Check for multiple handlers configured on the same logger
```python
# Clear existing handlers
logger = logging.getLogger('pyinfra_orbstack.timing')
logger.handlers.clear()

# Add single handler
handler = logging.StreamHandler()
logger.addHandler(handler)
```

## Related Documentation

- [Benchmark Guide](20251025-benchmark-guide.md) - Detailed performance benchmarking
- [Testing Standards](@testing-standards) - Test organization and practices
- [Python Logging Docs](https://docs.python.org/3/library/logging.html)

---

**Implementation:** Simple timing utility using Python's standard logging
**Dependencies:** None (stdlib only)
**Performance Impact:** Negligible (<0.1ms per timed operation)
