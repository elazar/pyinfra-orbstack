"""
Pytest configuration for PyInfra OrbStack tests.

This file provides configuration, fixtures, and utilities for testing.
"""

import platform
import subprocess

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring OrbStack"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (can run without OrbStack)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def check_orbstack_available():
    """Check if OrbStack is available and running."""
    try:
        # Check if we're on macOS
        if platform.system() != "Darwin":
            return False, "Not running on macOS"

        # Check if orbctl is available
        result = subprocess.run(
            ["which", "orbctl"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False, "orbctl not found in PATH"

        # Check if OrbStack is running
        result = subprocess.run(
            ["orbctl", "status"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return False, "OrbStack is not running"

        return True, "OrbStack is available"

    except subprocess.TimeoutExpired:
        return False, "Timeout checking OrbStack status"
    except Exception as e:
        return False, f"Error checking OrbStack: {e}"


@pytest.fixture(scope="session")
def orbstack_available():
    """Fixture to check if OrbStack is available."""
    available, reason = check_orbstack_available()
    return available, reason


@pytest.fixture(scope="session")
def orbstack_vms():
    """Fixture to get list of available VMs."""
    available, reason = check_orbstack_available()
    if not available:
        pytest.skip(f"OrbStack not available: {reason}")

    try:
        result = subprocess.run(
            ["orbctl", "list", "-f", "json"], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            import json

            vms = json.loads(result.stdout)
            return vms
        else:
            return []

    except Exception:
        return []


@pytest.fixture(scope="session")
def test_vm_name(orbstack_vms):
    """Fixture to get a test VM name."""
    if not orbstack_vms:
        pytest.skip("No VMs available for testing")

    # Return the first available VM name
    return orbstack_vms[0]["name"]


@pytest.fixture
def mock_state():
    """Fixture to provide a mock PyInfra state."""
    from unittest.mock import Mock

    return Mock()


@pytest.fixture
def mock_host():
    """Fixture to provide a mock PyInfra host."""
    from unittest.mock import Mock

    host = Mock()
    host.data = {}
    return host


@pytest.fixture
def mock_host_with_vm(mock_host, test_vm_name):
    """Fixture to provide a mock PyInfra host with VM name."""
    mock_host.data = {"vm_name": test_vm_name}
    return mock_host


def pytest_runtest_setup(item):
    """Setup for each test run."""
    # Skip integration tests if OrbStack is not available
    if item.get_closest_marker("integration"):
        available, reason = check_orbstack_available()
        if not available:
            pytest.skip(f"Integration test requires OrbStack: {reason}")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and handle command line options."""
    # Add markers based on test file names
    for item in items:
        # Mark tests in integration files as integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark tests in unit test files as unit tests
        elif any(
            x in item.nodeid
            for x in ["test_connector", "test_operations", "test_orbstack_cli_mocks"]
        ):
            item.add_marker(pytest.mark.unit)

    # Skip slow tests unless --run-slow is specified
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
