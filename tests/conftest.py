"""
Pytest configuration for PyInfra OrbStack tests.

This file provides configuration, fixtures, and utilities for testing.
"""

import atexit
import json
import platform
import subprocess
import time

import pytest

# Track test VMs created during this session
_test_vms_created = set()

# Track worker VMs (one per pytest worker)
_worker_vms = {}

# Single prefix for ALL test VMs
TEST_VM_PREFIX = "pytest-test-"


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

        # Single prefix - simple!
        test_vms = [vm["name"] for vm in vms if vm["name"].startswith(TEST_VM_PREFIX)]

        if test_vms:
            print(f"\nCleaning up {len(test_vms)} orphaned test VMs...")
            for vm_name in test_vms:
                try:
                    subprocess.run(
                        ["orbctl", "delete", "--force", vm_name],
                        capture_output=True,
                        timeout=30,  # Increased from 10s
                    )
                except subprocess.TimeoutExpired:
                    print(f"  Warning: Timeout deleting {vm_name}")
                except Exception as e:
                    print(f"  Warning: Error deleting {vm_name}: {e}")
    except Exception as e:
        print(f"Warning: Error during orphan cleanup: {e}")


# Register cleanup to run at exit (handles crashes/interrupts)
atexit.register(cleanup_test_vms)


def get_worker_vm() -> str:
    """
    Get or create a VM for the current pytest worker.

    Each worker gets one persistent VM for the entire test session.
    VMs are reused across all tests in that worker and cleaned up
    when the test runner terminates.

    This significantly improves performance by eliminating repetitive
    VM create/delete cycles.

    Returns:
        VM name for this worker (e.g., "pytest-test-worker-12345-1761248130")
    """
    import os

    from tests.test_utils import (
        create_vm_with_retry,
        delete_vm_with_retry,
        start_vm_with_retry,
        wait_for_vm_ready,
    )

    worker_pid = os.getpid()

    # Check if this worker already has a VM
    if worker_pid in _worker_vms:
        return _worker_vms[worker_pid]

    # Create a new VM for this worker
    timestamp = int(time.time())
    vm_name = f"{TEST_VM_PREFIX}worker-{worker_pid}-{timestamp}"

    print(f"\n[Worker {worker_pid}] Creating session VM: {vm_name}")

    if not create_vm_with_retry(
        image="ubuntu:22.04",
        vm_name=vm_name,
        auto_cleanup=True,
    ):
        raise RuntimeError(f"Failed to create worker VM: {vm_name}")

    if not start_vm_with_retry(vm_name):
        delete_vm_with_retry(vm_name, force=True)
        raise RuntimeError(f"Failed to start worker VM: {vm_name}")

    # Wait for VM to be ready (adaptive!)
    if not wait_for_vm_ready(vm_name, timeout=30):
        delete_vm_with_retry(vm_name, force=True)
        raise RuntimeError(f"Worker VM {vm_name} did not become ready")

    # Cache for this worker
    _worker_vms[worker_pid] = vm_name

    print(f"[Worker {worker_pid}] Session VM ready: {vm_name}")
    return vm_name


def cleanup_worker_vms():
    """Clean up worker VMs at session end."""
    if not _worker_vms:
        return

    print(f"\n\nCleaning up {len(_worker_vms)} worker VMs...")
    for worker_pid, vm_name in _worker_vms.items():
        print(f"[Worker {worker_pid}] Deleting {vm_name}")
        try:
            subprocess.run(
                ["orbctl", "delete", "--force", vm_name],
                capture_output=True,
                timeout=30,
            )
        except Exception as e:
            print(f"  Error: {e}")
    _worker_vms.clear()


# Register worker VM cleanup at session end
atexit.register(cleanup_worker_vms)


@pytest.fixture(scope="session")
def worker_vm():
    """
    Fixture providing a persistent VM for the current pytest worker.

    The VM is created once per worker and reused across all tests
    in that worker. Cleaned up when the test session ends.

    Benefits:
    - 80-90% faster test execution (no repetitive create/delete)
    - Lower resource usage (fewer concurrent VMs)
    - Better OrbStack stability (less contention)

    Example:
        def test_something(worker_vm):
            # worker_vm is ready to use (e.g., "pytest-test-worker-12345-1761248130")
            result = subprocess.run(
                ["orbctl", "info", worker_vm, "--format", "json"],
                capture_output=True,
                text=True,
            )
    """
    vm_name = get_worker_vm()
    yield vm_name
    # Cleanup handled by session cleanup


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

    # Pre-pull required images to avoid download delays during tests
    _prepull_test_images()

    # Clean up orphaned test VMs from previous runs at session start
    cleanup_orphaned_test_vms()


def _prepull_test_images():
    """Pre-pull commonly used images to avoid download delays during tests."""
    images = ["ubuntu:22.04"]

    print("\n\nPre-pulling test images...")
    for image in images:
        try:
            result = subprocess.run(
                ["orbctl", "pull", image],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max per image
            )
            if result.returncode == 0:
                print(f"  ✓ {image}")
            else:
                print(f"  ⚠ {image} (already present or error)")
        except subprocess.TimeoutExpired:
            print(f"  ⚠ {image} (timeout)")
        except Exception as e:
            print(f"  ⚠ {image} (error: {e})")
    print("Image pre-pull complete.\n")


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


@pytest.fixture(autouse=True)
def auto_cleanup_test_vm(request):
    """Automatically track and clean up VMs created by test classes.

    This fixture automatically:
    1. Tracks VMs from test_vm_name attribute (if present)
    2. Cleans up the VM and any variants after the test completes
    3. Handles failures and timeouts gracefully
    """
    # Before test: track VM if test_vm_name attribute exists
    if hasattr(request.instance, "test_vm_name"):
        vm_name = request.instance.test_vm_name
        _test_vms_created.add(vm_name)

    yield

    # After test: clean up VMs created during the test
    if hasattr(request.instance, "test_vm_name"):
        base_vm_name = request.instance.test_vm_name

        try:
            # Get list of all VMs
            result = subprocess.run(
                ["orbctl", "list", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                vms = json.loads(result.stdout)
                # Find VMs that match the base name or have suffixes
                test_vms = [
                    vm["name"]
                    for vm in vms
                    if vm["name"] == base_vm_name
                    or vm["name"].startswith(f"{base_vm_name}-")
                ]

                # Clean up all matching VMs
                for vm_name in test_vms:
                    try:
                        subprocess.run(
                            ["orbctl", "delete", "--force", vm_name],
                            capture_output=True,
                            timeout=30,
                        )
                    except Exception:
                        pass  # Will be cleaned up by session cleanup if this fails
        except Exception:
            pass  # Best effort cleanup


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
    success = create_vm_with_retry("ubuntu:22.04", vm_name, auto_cleanup=False)
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
        "ubuntu:22.04", vm_name, user="testuser", auto_cleanup=False
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
        "ubuntu:22.04", vm_name, arch="arm64", auto_cleanup=False
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
