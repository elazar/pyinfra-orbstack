"""
Pytest configuration for PyInfra OrbStack tests.

This file provides configuration, fixtures, and utilities for testing.
"""

import atexit
import json
import platform
import subprocess

import pytest

# Track test VMs created during this session
_test_vms_created = set()


def cleanup_test_vms():
    """Clean up all test VMs created during this session."""
    if not _test_vms_created:
        return

    print(f"\n\nCleaning up {len(_test_vms_created)} test VMs...")
    for vm_name in _test_vms_created:
        try:
            subprocess.run(
                ["orbctl", "delete", "--force", vm_name],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass  # Best effort cleanup
    _test_vms_created.clear()


def cleanup_orphaned_test_vms():
    """Clean up any orphaned test VMs from previous runs."""
    try:
        result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return

        vms = json.loads(result.stdout)
        test_prefixes = [
            "test-vm-",
            "e2e-ops-vm-",
            "deploy-test-vm-",
            "consolidated-test-vm-",
            "e2e-test-vm-",
        ]
        orphaned_vms = [
            vm["name"]
            for vm in vms
            if any(prefix in vm["name"] for prefix in test_prefixes)
        ]

        if orphaned_vms:
            print(f"\nCleaning up {len(orphaned_vms)} orphaned test VMs...")
            for vm_name in orphaned_vms:
                try:
                    subprocess.run(
                        ["orbctl", "delete", "--force", vm_name],
                        capture_output=True,
                        timeout=10,
                    )
                except Exception:
                    pass
    except Exception:
        pass  # Best effort cleanup


# Register cleanup to run at exit (handles crashes/interrupts)
atexit.register(cleanup_test_vms)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring OrbStack"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (can run without OrbStack)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")

    # Clean up orphaned test VMs from previous runs at session start
    cleanup_orphaned_test_vms()


def pytest_sessionfinish(session, exitstatus):
    """Clean up test VMs at the end of the test session."""
    cleanup_test_vms()


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


@pytest.fixture
def track_test_vm():
    """Fixture to track test VMs for automatic cleanup.

    Usage in tests:
        def test_something(track_test_vm):
            vm_name = "my-test-vm"
            track_test_vm(vm_name)
            # Create VM...
            # VM will be automatically cleaned up even if test fails
    """

    def _track(vm_name):
        _test_vms_created.add(vm_name)

    return _track


@pytest.fixture(scope="session")
def shared_vm_basic():
    """
    Session-scoped VM for basic tests.

    Creates a single VM that is shared across all tests in the session.
    This significantly reduces test runtime by avoiding repeated VM creation.
    """
    from tests.test_utils import create_vm_with_retry

    vm_name = "pytest-shared-basic"
    _test_vms_created.add(vm_name)

    # Create VM
    success = create_vm_with_retry(
        "ubuntu:22.04", vm_name, max_retries=3, auto_cleanup=False
    )
    if not success:
        pytest.skip(f"Could not create shared VM: {vm_name}")

    # Start VM
    subprocess.run(["orbctl", "start", vm_name], capture_output=True, timeout=30)

    yield vm_name

    # Cleanup happens via _test_vms_created tracking


@pytest.fixture(scope="session")
def shared_vm_with_user():
    """
    Session-scoped VM with custom user for user-specific tests.
    """
    from tests.test_utils import create_vm_with_retry

    vm_name = "pytest-shared-user"
    _test_vms_created.add(vm_name)

    success = create_vm_with_retry(
        "ubuntu:22.04", vm_name, user="testuser", max_retries=3, auto_cleanup=False
    )
    if not success:
        pytest.skip(f"Could not create shared VM with user: {vm_name}")

    subprocess.run(["orbctl", "start", vm_name], capture_output=True, timeout=30)

    yield vm_name


@pytest.fixture(scope="session")
def shared_vm_with_arch():
    """
    Session-scoped VM with specific architecture for arch tests.
    """
    from tests.test_utils import create_vm_with_retry

    vm_name = "pytest-shared-arch"
    _test_vms_created.add(vm_name)

    success = create_vm_with_retry(
        "ubuntu:22.04", vm_name, arch="arm64", max_retries=3, auto_cleanup=False
    )
    if not success:
        pytest.skip(f"Could not create shared VM with arch: {vm_name}")

    subprocess.run(["orbctl", "start", vm_name], capture_output=True, timeout=30)

    yield vm_name


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
