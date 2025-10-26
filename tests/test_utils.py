"""
Test utilities for resilient VM operations.
"""

import os
import subprocess
import time
import uuid
from typing import Optional

# Import cleanup tracking from conftest
try:
    from tests.conftest import _test_vms_created
except ImportError:
    # Fallback if running outside pytest
    _test_vms_created = set()


def check_orbstack_healthy() -> tuple[bool, str]:
    """
    Check if OrbStack is healthy and responsive.

    Returns:
        Tuple of (is_healthy, status_message)
    """
    try:
        # Quick list operation to verify OrbStack is responsive
        result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, "OrbStack is healthy"
        else:
            return False, f"OrbStack list failed: {result.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return False, "OrbStack is unresponsive (timeout)"
    except Exception as e:
        return False, f"OrbStack check failed: {str(e)[:100]}"


def register_test_vm_for_cleanup(vm_name: str) -> None:
    """
    Register a test VM for automatic cleanup.

    This ensures the VM will be cleaned up even if the test fails or
    the test process is interrupted.

    Args:
        vm_name: Name of the VM to register for cleanup
    """
    _test_vms_created.add(vm_name)


def wait_for_vm_ready(
    vm_name: str, timeout: int = 30, poll_interval: float = 0.5
) -> bool:
    """
    Wait for VM to be ready for use.

    A VM is considered ready when:
    - State is "running"
    - Has an IP address assigned

    This replaces static time.sleep() delays with adaptive polling.

    Args:
        vm_name: Name of the VM to check
        timeout: Maximum time to wait in seconds (default: 30)
        poll_interval: Time between status checks in seconds (default: 0.5)

    Returns:
        True if VM is ready, False if timeout

    Example:
        if not wait_for_vm_ready(vm_name, timeout=30):
            raise RuntimeError(f"VM {vm_name} did not become ready")
    """
    import json

    start_time = time.time()

    while (time.time() - start_time) < timeout:
        try:
            result = subprocess.run(
                ["orbctl", "info", vm_name, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                info = json.loads(result.stdout)
                record = info.get("record", {})
                state = record.get("state")
                ip4 = info.get("ip4")

                # VM is ready when it's running and has an IP
                if state == "running" and ip4:
                    elapsed = time.time() - start_time
                    print(
                        f"VM {vm_name} ready in {elapsed:.1f}s (state={state}, ip={ip4})"
                    )
                    return True

        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
            pass

        time.sleep(poll_interval)

    # Timeout
    elapsed = time.time() - start_time
    print(f"VM {vm_name} did not become ready after {elapsed:.1f}s")
    return False


def create_test_vm(reuse_worker_vm: bool = True) -> str:
    """
    Create or get a test VM.

    By default, returns the persistent worker VM for maximum performance.
    Set reuse_worker_vm=False for tests that need a fresh VM (e.g., lifecycle tests).

    This is the recommended way to create VMs in tests. The VM is:
    - Created with ubuntu:22.04 (used by 100% of tests)
    - Started automatically
    - Registered for automatic cleanup
    - Named uniquely for parallel test execution

    Thread-safe for parallel test execution. VM name includes:
    - Timestamp (for chronological ordering)
    - Process ID (for parallel worker isolation)
    - Random suffix (for sub-second collision prevention)

    Args:
        reuse_worker_vm: If True, return the persistent worker VM (default).
                        If False, create a new one-off VM.

    Returns:
        VM name (ready to use)

        Examples:
        - Worker VM: "pytest-test-worker-12345-1761248130"
        - One-off VM: "pytest-test-1761248130-12345-a3f2e1"

        Note: The exact format is an implementation detail and should not be relied upon.

    Raises:
        RuntimeError: If VM creation or start fails

    Examples:
        # Most tests - reuse worker VM (fast!)
        vm_name = create_test_vm()

        # Tests that need fresh VM (e.g., testing VM lifecycle)
        vm_name = create_test_vm(reuse_worker_vm=False)
    """
    if reuse_worker_vm:
        # Get the persistent worker VM
        from tests.conftest import get_worker_vm

        return get_worker_vm()

    # Create a one-off VM
    from tests.conftest import TEST_VM_PREFIX

    timestamp = int(time.time())
    pid = os.getpid()
    random_suffix = uuid.uuid4().hex[:6]
    vm_name = f"{TEST_VM_PREFIX}{timestamp}-{pid}-{random_suffix}"

    # Create VM
    if not create_vm_with_retry(
        image="ubuntu:22.04",  # Hardcoded - used by 100% of tests
        vm_name=vm_name,
        auto_cleanup=True,  # Registers for cleanup before creation
    ):
        raise RuntimeError(f"Failed to create VM: {vm_name}")

    # Start VM
    if not start_vm_with_retry(vm_name):
        delete_vm_with_retry(vm_name, force=True)
        raise RuntimeError(f"Failed to start VM: {vm_name}")

    # Wait for VM to be ready (adaptive!)
    if not wait_for_vm_ready(vm_name, timeout=30):
        delete_vm_with_retry(vm_name, force=True)
        raise RuntimeError(f"VM {vm_name} did not become ready")

    return vm_name


def execute_orbctl_with_retry(
    cmd: list,
    operation_name: str = "orbctl command",
) -> tuple[int, str, str]:
    """
    Execute orbctl command with retry logic for transient failures.

    Retries on rare failure conditions such as:
    - OrbStack service crashes or becomes unresponsive
    - Image download failures (first use of an image)
    - Transient command execution errors

    Note: Does NOT help with slow VM creation due to resource contention.
    For better performance, use session-scoped worker VMs (worker_vm fixture).

    Args:
        cmd: Command to execute
        operation_name: Name of operation for logging

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    # Configuration (not user-facing - moved inside function)
    max_retries = 3
    base_delay = 2.0

    # Determine timeout based on operation type
    operation_lower = operation_name.lower()
    if any(op in operation_lower for op in ["creat", "clone", "import"]):
        timeout = 180  # VM creation/clone/import operations are slow
    elif any(op in operation_lower for op in ["delete", "start", "stop", "restart"]):
        timeout = 60  # Other VM operations
    else:
        timeout = 30  # Default

    for attempt in range(max_retries + 1):
        try:
            if attempt == 0:
                # Log timeout on first attempt for debugging
                print(
                    f"Executing {operation_name} (attempt {attempt + 1}/{max_retries + 1}, timeout={timeout}s)"
                )
            else:
                print(
                    f"Executing {operation_name} (attempt {attempt + 1}/{max_retries + 1})"
                )

            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.time() - start_time

            if result.returncode == 0:
                print(f"{operation_name} completed successfully in {elapsed:.2f}s")
                return result.returncode, result.stdout, result.stderr

            # Check if it's a network-related error
            error_msg = result.stderr.lower() if result.stderr else ""
            is_network_error = any(
                keyword in error_msg
                for keyword in [
                    "timeout",
                    "connection",
                    "network",
                    "tls",
                    "handshake",
                    "download",
                    "cdn",
                    "http",
                    "https",
                    "tcp",
                    "dns",
                    "missing ip address",
                    "didn't start",
                    "setup",
                    "machine",
                ]
            )

            # Retry network errors
            if is_network_error and attempt < max_retries:
                delay = base_delay * (2**attempt)  # Exponential backoff
                print(
                    f"Network error in {operation_name} after {elapsed:.2f}s, retrying in {delay}s"
                )
                # Log actual error for debugging
                if result.stderr:
                    error_preview = result.stderr[:200].replace("\n", " ")
                    print(f"  Error details: {error_preview}")
                time.sleep(delay)
                continue
            else:
                print(
                    f"{operation_name} failed after {attempt + 1} attempts (took {elapsed:.2f}s)"
                )
                # Log final error for debugging
                if result.stderr:
                    error_preview = result.stderr[:500].replace("\n", " ")
                    print(f"  Final error: {error_preview}")
                return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired as e:
            if attempt < max_retries:
                delay = base_delay * (2**attempt)
                print(
                    f"{operation_name} timed out after {timeout}s, retrying in {delay}s"
                )
                print(f"  Command: {' '.join(cmd)}")
                # Check if OrbStack is still responsive
                try:
                    health_check = subprocess.run(
                        ["orbctl", "status"], capture_output=True, text=True, timeout=5
                    )
                    if health_check.returncode == 0:
                        print("  OrbStack is responsive (status OK)")
                    else:
                        print("  Warning: OrbStack status check failed")
                except Exception:  # Catch all exceptions during health check
                    print("  Warning: OrbStack appears unresponsive")
                time.sleep(delay)
                continue
            else:
                print(f"{operation_name} timed out after {max_retries + 1} attempts")
                print(f"  Total time waited: {timeout * (max_retries + 1)}s")
                raise e
        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2**attempt)
                print(f"{operation_name} failed: {str(e)}, retrying in {delay}s")
                time.sleep(delay)
                continue
            else:
                print(
                    f"{operation_name} failed after {max_retries + 1} attempts: {str(e)}"
                )
                raise e

    # This should never be reached
    return 1, "", f"{operation_name} failed after {max_retries + 1} attempts"


def create_vm_with_retry(
    image: str,
    vm_name: str,
    arch: Optional[str] = None,
    user: Optional[str] = None,
    auto_cleanup: bool = True,
) -> bool:
    """
    Create VM with retry logic for transient OrbStack failures.

    Retries on rare failure conditions such as:
    - OrbStack service crashes or becomes unresponsive
    - Image download failures (first use of an image)
    - Transient command execution errors

    Note: Does NOT help with slow VM creation under load.
    Use session-scoped worker VMs (worker_vm fixture) for better performance.

    Args:
        image: VM image
        vm_name: VM name
        arch: Architecture (optional - for feature tests)
        user: Default user (optional - for feature tests)
        auto_cleanup: If True, register VM for automatic cleanup (default: True)

    Returns:
        True if successful, False otherwise
    """
    # Check OrbStack health before attempting VM creation
    is_healthy, health_msg = check_orbstack_healthy()
    if not is_healthy:
        print(f"Warning: {health_msg}")
        print("  Proceeding with VM creation anyway...")

    # Register for cleanup before creating (handles failures/interrupts)
    if auto_cleanup:
        register_test_vm_for_cleanup(vm_name)

    cmd = ["orbctl", "create", image, vm_name]

    if arch:
        cmd.extend(["--arch", arch])

    if user:
        cmd.extend(["--user", user])

    return_code, _, stderr = execute_orbctl_with_retry(
        cmd,
        operation_name=f"VM creation ({vm_name})",
    )

    if return_code == 0:
        return True

    # Handle case where VM was created but command didn't return success
    # (common with OrbStack intermittent hangs)
    if "already exists" in stderr.lower():
        print(f"VM {vm_name} already exists (likely created but command hung)")
        print("  Verifying VM is usable...")

        # Check if VM exists and get its state
        try:
            check_result = subprocess.run(
                ["orbctl", "info", vm_name, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if check_result.returncode == 0:
                print(f"  VM {vm_name} verified - treating creation as successful")
                # Try to start it to ensure it's ready
                start_vm_with_retry(vm_name)
                return True
        except Exception as e:
            print(f"  Warning: Could not verify VM {vm_name}: {e}")

    return False


def delete_vm_with_retry(vm_name: str, force: bool = True) -> bool:
    """
    Delete VM with retry logic.

    Args:
        vm_name: VM name
        force: Force deletion (default: True)

    Returns:
        True if successful, False otherwise
    """
    # First check if VM exists
    check_result = subprocess.run(
        ["orbctl", "list", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if check_result.returncode == 0:
        import json

        try:
            vms = json.loads(check_result.stdout)
            vm_exists = any(vm.get("name") == vm_name for vm in vms)
            if not vm_exists:
                # VM doesn't exist, nothing to delete
                return True
        except (json.JSONDecodeError, KeyError):
            # If we can't parse, proceed with deletion attempt
            pass

    cmd = ["orbctl", "delete", vm_name]
    if force:
        cmd.append("-f")

    return_code, _, _ = execute_orbctl_with_retry(
        cmd,
        operation_name=f"VM deletion ({vm_name})",
    )

    return return_code == 0


def start_vm_with_retry(vm_name: str) -> bool:
    """
    Start VM with retry logic.

    Args:
        vm_name: VM name

    Returns:
        True if successful, False otherwise
    """
    cmd = ["orbctl", "start", vm_name]

    return_code, _, _ = execute_orbctl_with_retry(
        cmd, operation_name=f"VM start ({vm_name})"
    )

    return return_code == 0


def stop_vm_with_retry(vm_name: str, force: bool = False) -> bool:
    """
    Stop VM with retry logic.

    Args:
        vm_name: VM name
        force: Force stop (default: False)

    Returns:
        True if successful, False otherwise
    """
    cmd = ["orbctl", "stop", vm_name]
    if force:
        cmd.append("-f")

    return_code, _, _ = execute_orbctl_with_retry(
        cmd, operation_name=f"VM stop ({vm_name})"
    )

    return return_code == 0
