# End-to-End Testing for PyInfra OrbStack

**Date:** 2025-01-16
**Status:** Implemented

## Overview

This document describes the end-to-end testing approach implemented for the PyInfra OrbStack connector. The end-to-end tests verify the complete integration between PyInfra and OrbStack, including VM lifecycle management, command execution, and file operations.

## Test Structure

### Test File Location

- **File:** `tests/test_end_to_end.py`
- **Class:** `TestEndToEndIntegration`
- **Markers:** `@pytest.mark.integration`

### Prerequisites

The end-to-end tests require:

- macOS operating system
- OrbStack installed and running
- `orbctl` command available in PATH

Tests are automatically skipped if these conditions are not met.

## Test Coverage

### 1. VM Lifecycle Testing

- **Test:** `test_vm_lifecycle_end_to_end`
- **Purpose:** Verifies complete VM lifecycle (create, list, start, info, stop, delete)
- **Approach:** Uses direct `orbctl` commands to test the underlying functionality

### 2. Connector Command Execution

- **Test:** `test_connector_command_execution`
- **Purpose:** Tests command execution through the OrbStack connector
- **Features:**
  - Basic command execution
  - Working directory specification
  - Error handling for invalid commands

### 3. File Operations

- **Test:** `test_connector_file_operations`
- **Purpose:** Tests file upload and download functionality
- **Features:**
  - File upload to VM
  - File download from VM
  - Content verification

### 4. VM Operations with Parameters

- **Test:** `test_vm_operations_with_parameters`
- **Purpose:** Tests VM creation with various parameters
- **Features:**
  - Architecture specification (arm64)
  - User specification

### 5. VM Lifecycle Operations

- **Test:** `test_vm_lifecycle_operations`
- **Purpose:** Tests VM start, stop, restart operations
- **Features:**
  - Normal start/stop
  - Force stop
  - Restart functionality

### 6. Connector Data Generation

- **Test:** `test_connector_make_names_data`
- **Purpose:** Tests the connector's VM discovery functionality
- **Features:**
  - VM listing and data extraction
  - Group assignment
  - Data structure validation

### 7. Connection Management

- **Test:** `test_connector_connection_management`
- **Purpose:** Tests connector connection and disconnection
- **Features:**
  - Connection to running VMs
  - Graceful disconnection

### 8. Error Handling

- **Test:** `test_error_handling`
- **Purpose:** Tests error scenarios and edge cases
- **Features:**
  - Non-existent VM operations
  - Connector error handling

### 9. Network Functionality

- **Test:** `test_vm_network_functionality`
- **Purpose:** Tests VM network capabilities
- **Features:**
  - Network information retrieval
  - IP address detection

### 10. Performance Characteristics

- **Test:** `test_vm_performance_characteristics`
- **Purpose:** Tests VM operation performance
- **Features:**
  - VM creation time measurement
  - VM deletion time measurement
  - Performance thresholds

## Test Design Principles

### 1. Isolation

- Each test creates unique VM names using timestamps
- Proper cleanup in `teardown_method`
- No interference between tests

### 2. Realistic Testing

- Uses actual OrbStack CLI commands
- Tests real VM lifecycle operations
- Verifies actual file operations

### 3. Error Resilience

- Graceful handling of cleanup failures
- Timeout protection for long-running operations
- Proper error assertion for expected failures

### 4. Performance Awareness

- Reasonable timeouts for operations
- Performance measurement and validation
- Resource cleanup to prevent accumulation

## Running the Tests

### Individual Test

```bash
uv run python -m pytest tests/test_end_to_end.py::TestEndToEndIntegration::test_vm_lifecycle_end_to_end -v
```

### All End-to-End Tests

```bash
uv run python -m pytest tests/test_end_to_end.py -v
```

### With Coverage

```bash
uv run python -m pytest tests/test_end_to_end.py --cov=pyinfra_orbstack --cov-report=html
```

## Test Execution Time

The end-to-end tests are designed to be comprehensive but efficient:

- **Individual tests:** 30-60 seconds each
- **Full suite:** ~6 minutes
- **VM operations:** Include appropriate wait times for VM state changes

## Integration with Existing Tests

The end-to-end tests complement the existing test suite:

- **Unit tests:** Test individual components in isolation
- **Integration tests:** Test component interactions
- **End-to-end tests:** Test complete workflows with real infrastructure

## Future Enhancements

Potential improvements for the end-to-end tests:

1. **Parallel execution:** Run tests in parallel where possible
2. **Test data management:** Centralized test data and fixtures
3. **Performance baselines:** Establish performance benchmarks
4. **Multi-VM scenarios:** Test interactions between multiple VMs
5. **Network scenarios:** Test complex networking configurations

## Troubleshooting

### Common Issues

1. **OrbStack not running**
   - Ensure OrbStack is installed and running
   - Check `orbctl status` command

2. **VM creation failures**
   - Verify sufficient disk space
   - Check OrbStack resource limits

3. **Timeout errors**
   - Increase timeout values for slower systems
   - Check system performance

4. **Cleanup failures**
   - Tests include error handling for cleanup
   - Manual cleanup may be needed in rare cases

### Debug Mode

Run tests with verbose output for debugging:

```bash
uv run python -m pytest tests/test_end_to_end.py -v -s
```

## Conclusion

The end-to-end tests provide comprehensive validation of the PyInfra OrbStack integration, ensuring that all components work together correctly in real-world scenarios. These tests are essential for maintaining confidence in the connector's functionality and catching integration issues early in the development process.
