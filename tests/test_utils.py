"""
Test utilities for resilient VM operations.
"""

import subprocess
import time
from typing import Optional

# Import cleanup tracking from conftest
try:
    from tests.conftest import _test_vms_created
except ImportError:
    # Fallback if running outside pytest
    _test_vms_created = set()


def register_test_vm_for_cleanup(vm_name: str) -> None:
    """
    Register a test VM for automatic cleanup.

    This ensures the VM will be cleaned up even if the test fails or
    the test process is interrupted.

    Args:
        vm_name: Name of the VM to register for cleanup
    """
    _test_vms_created.add(vm_name)


def execute_orbctl_with_retry(
    cmd: list,
    max_retries: int = 3,
    base_delay: float = 2.0,
    timeout: int = 180,
    operation_name: str = "orbctl command",
) -> tuple[int, str, str]:
    """
    Execute orbctl command with retry logic for network resilience.

    Args:
        cmd: Command to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (will be exponential)
        timeout: Command timeout in seconds
        operation_name: Name of operation for logging

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    for attempt in range(max_retries + 1):
        try:
            print(
                f"Executing {operation_name} (attempt {attempt + 1}/{max_retries + 1})"
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                print(f"{operation_name} completed successfully")
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
                print(f"Network error in {operation_name}, retrying in {delay}s")
                time.sleep(delay)
                continue
            else:
                print(f"{operation_name} failed after {attempt + 1} attempts")
                return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired as e:
            if attempt < max_retries:
                delay = base_delay * (2**attempt)
                print(f"{operation_name} timed out, retrying in {delay}s")
                time.sleep(delay)
                continue
            else:
                print(f"{operation_name} timed out after {max_retries + 1} attempts")
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
    max_retries: int = 3,
    auto_cleanup: bool = True,
) -> bool:
    """
    Create VM with retry logic for network resilience.

    Args:
        image: VM image
        vm_name: VM name
        arch: Architecture
        user: Default user
        max_retries: Maximum retry attempts
        auto_cleanup: If True, register VM for automatic cleanup (default: True)

    Returns:
        True if successful, False otherwise
    """
    # Register for cleanup before creating (handles failures/interrupts)
    if auto_cleanup:
        register_test_vm_for_cleanup(vm_name)

    cmd = ["orbctl", "create", image, vm_name]

    if arch:
        cmd.extend(["--arch", arch])

    if user:
        cmd.extend(["--user", user])

    return_code, stdout, stderr = execute_orbctl_with_retry(
        cmd,
        max_retries=max_retries,
        timeout=180,  # Longer timeout for VM creation
        operation_name=f"VM creation ({vm_name})",
    )

    return return_code == 0


def delete_vm_with_retry(
    vm_name: str, force: bool = True, max_retries: int = 2
) -> bool:
    """
    Delete VM with retry logic.

    Args:
        vm_name: VM name
        force: Force deletion
        max_retries: Maximum retry attempts

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

    return_code, stdout, stderr = execute_orbctl_with_retry(
        cmd,
        max_retries=max_retries,
        timeout=60,
        operation_name=f"VM deletion ({vm_name})",
    )

    return return_code == 0


def start_vm_with_retry(vm_name: str, max_retries: int = 2) -> bool:
    """
    Start VM with retry logic.

    Args:
        vm_name: VM name
        max_retries: Maximum retry attempts

    Returns:
        True if successful, False otherwise
    """
    cmd = ["orbctl", "start", vm_name]

    return_code, stdout, stderr = execute_orbctl_with_retry(
        cmd, max_retries=max_retries, timeout=60, operation_name=f"VM start ({vm_name})"
    )

    return return_code == 0


def stop_vm_with_retry(vm_name: str, force: bool = False, max_retries: int = 2) -> bool:
    """
    Stop VM with retry logic.

    Args:
        vm_name: VM name
        force: Force stop
        max_retries: Maximum retry attempts

    Returns:
        True if successful, False otherwise
    """
    cmd = ["orbctl", "stop", vm_name]
    if force:
        cmd.append("-f")

    return_code, stdout, stderr = execute_orbctl_with_retry(
        cmd, max_retries=max_retries, timeout=60, operation_name=f"VM stop ({vm_name})"
    )

    return return_code == 0
