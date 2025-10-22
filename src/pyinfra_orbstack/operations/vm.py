"""
VM Lifecycle Operations for PyInfra OrbStack Connector

Provides operations for managing OrbStack VMs including creation, deletion,
start/stop, cloning, export/import, and information retrieval.
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
def vm_clone(source_name: str, new_name: str):
    """
    Clone an existing OrbStack VM.

    Creates a copy of an existing VM with all data and settings.
    The new VM will be in a stopped state and data is snapshotted
    and copied on demand (no double disk usage).

    Args:
        source_name: Name of the VM to clone
        new_name: Name for the new cloned VM
    """
    cmd = f"orbctl clone {source_name} {new_name}"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_export(name: str, output_path: str):
    """
    Export an OrbStack VM to a file.

    The VM will be paused during export to prevent data corruption.

    Args:
        name: VM name to export
        output_path: Path where the exported file will be saved (e.g., "backup.tar.zst")
    """
    cmd = f"orbctl export {name} {output_path}"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_import(input_path: str, name: str):
    """
    Import an OrbStack VM from a file.

    Creates a new VM from a previously exported VM file.

    Args:
        input_path: Path to the exported VM file (e.g., "backup.tar.zst")
        name: Name for the imported VM
    """
    cmd = f"orbctl import -n {name} {input_path}"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def vm_rename(old_name: str, new_name: str):
    """
    Rename an OrbStack VM.

    Args:
        old_name: Current VM name
        new_name: New VM name
    """
    cmd = f"orbctl rename {old_name} {new_name}"

    # Yield the command for PyInfra to execute
    yield cmd


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


@operation()
def ssh_info(machine: Optional[str] = None):
    """
    Get SSH connection information for OrbStack machines.

    Shows commands and instructions for connecting via SSH, useful for
    remote editing (e.g., Visual Studio Code) or connecting from another device.

    Args:
        machine: Optional machine name (defaults to current host or default machine)

    Returns:
        str: SSH connection information
    """
    # If machine is specified, use it; otherwise use current host's vm_name
    if machine is None:
        machine = host.data.get("vm_name", "")

    # orbctl ssh shows general SSH information
    # For specific machine, we can use orbctl info to get SSH details
    if machine:
        cmd = f"orbctl info {machine} --format json"
    else:
        cmd = "orbctl ssh"

    # Yield the command for PyInfra to execute
    yield cmd


@operation()
def ssh_connect_string(machine: Optional[str] = None):
    """
    Get SSH connection string for a machine.

    Generates the SSH connection string (e.g., "ssh machine@orb") for connecting
    to an OrbStack machine.

    Args:
        machine: Machine name (defaults to current host's vm_name)

    Returns:
        str: SSH connection string
    """
    # Get machine name from parameter or host data
    if machine is None:
        machine = host.data.get("vm_name", "")

    if not machine:
        return "Error: No machine specified"

    # OrbStack SSH format is: ssh <machine>@orb
    # But we'll get the actual info from orbctl
    cmd = f"orbctl info {machine} --format json"

    # Yield the command for PyInfra to execute
    yield cmd
