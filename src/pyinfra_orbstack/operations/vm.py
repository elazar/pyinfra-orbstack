"""
VM Lifecycle Operations for PyInfra OrbStack Connector

Provides operations for managing OrbStack VMs including creation, deletion,
start/stop, and information retrieval.
"""

from typing import Optional

from pyinfra import host
from pyinfra.api import operation


@operation()
def vm_create(
    name: str,
    image: str,
    arch: Optional[str] = None,
    user: Optional[str] = None,
    present: bool = True,
):
    """
    Create or ensure OrbStack VM exists.

    Args:
        name: VM name
        image: VM image/distro (e.g., "ubuntu:22.04", "alpine")
        arch: Architecture (arm64, amd64)
        user: Default username
        present: Whether VM should exist
    """
    if not present:
        yield from vm_delete(name, force=True)
        return

    # Build orbctl create command
    cmd = ["orbctl", "create", image, name]

    if arch:
        cmd.extend(["--arch", arch])

    if user:
        cmd.extend(["--user", user])

    # Yield the command for PyInfra to execute
    yield " ".join(cmd)


@operation()
def vm_delete(name: str, force: bool = False):
    """
    Delete OrbStack VM.

    Args:
        name: VM name
        force: Force deletion without confirmation
    """
    force_flag = "-f" if force else ""
    cmd = f"orbctl delete {force_flag} {name}"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_start(name: str):
    """
    Start OrbStack VM.

    Args:
        name: VM name
    """
    cmd = f"orbctl start {name}"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_stop(name: str, force: bool = False):
    """
    Stop OrbStack VM.

    Args:
        name: VM name
        force: Force stop
    """
    force_flag = "-f" if force else ""
    cmd = f"orbctl stop {force_flag} {name}"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_restart(name: str):
    """
    Restart OrbStack VM.

    Args:
        name: VM name
    """
    cmd = f"orbctl restart {name}"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_info():
    """
    Get detailed VM information for current host.

    Returns:
        dict: VM information
    """
    # VM name is inferred from host context
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return {}

    cmd = f"orbctl info {vm_name} --format json"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_list():
    """
    List all VMs with status.

    Returns:
        list: List of VM information dictionaries
    """
    cmd = "orbctl list -f json"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_status():
    """
    Get VM status (running, stopped, etc.) for current host.

    Returns:
        str: VM status
    """
    # This operation depends on vm_info, so we need to get the info first
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return "unknown"

    cmd = f"orbctl info {vm_name} --format json"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_ip():
    """
    Get VM IP address for current host.

    Returns:
        str: VM IP address
    """
    # This operation depends on vm_info, so we need to get the info first
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return ""

    cmd = f"orbctl info {vm_name} --format json"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_network_info():
    """
    Get VM network information from VM info command for current host.

    Returns:
        dict: Network information
    """
    # This operation depends on vm_info, so we need to get the info first
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return {}

    cmd = f"orbctl info {vm_name} --format json"

    # Yield the command for PyInfra to execute
    yield cmd
