"""
VM Lifecycle Operations for PyInfra OrbStack Connector

Provides operations for managing OrbStack VMs including creation, deletion,
start/stop, cloning, export/import, and information retrieval.

This module separates command construction logic from operation definitions
to enable better test coverage and maintainability.
"""

from typing import Optional

from pyinfra import host
from pyinfra.api import operation


# Command construction functions (testable without decorator)
def build_vm_create_command(
    name: str, image: str, arch: Optional[str] = None, user: Optional[str] = None
) -> str:
    """
    Build the orbctl create command.

    Args:
        name: VM name
        image: VM image/distro
        arch: Architecture (arm64, amd64)
        user: Default username

    Returns:
        str: The complete orbctl create command
    """
    cmd = ["orbctl", "create", image, name]

    if arch:
        cmd.extend(["--arch", arch])

    if user:
        cmd.extend(["--user", user])

    return " ".join(cmd)


def build_vm_clone_command(source_name: str, new_name: str) -> str:
    """Build the orbctl clone command."""
    return f"orbctl clone {source_name} {new_name}"


def build_vm_export_command(name: str, output_path: str) -> str:
    """Build the orbctl export command."""
    return f"orbctl export {name} {output_path}"


def build_vm_import_command(input_path: str, name: str) -> str:
    """Build the orbctl import command."""
    return f"orbctl import -n {name} {input_path}"


def build_vm_rename_command(old_name: str, new_name: str) -> str:
    """Build the orbctl rename command."""
    return f"orbctl rename {old_name} {new_name}"


def build_vm_delete_command(name: str, force: bool = False) -> str:
    """Build the orbctl delete command."""
    force_flag = "-f" if force else ""
    return f"orbctl delete {force_flag} {name}".strip()


def build_vm_start_command(name: str) -> str:
    """Build the orbctl start command."""
    return f"orbctl start {name}"


def build_vm_stop_command(name: str, force: bool = False) -> str:
    """Build the orbctl stop command."""
    force_flag = "-f" if force else ""
    return f"orbctl stop {force_flag} {name}".strip()


def build_vm_restart_command(name: str) -> str:
    """Build the orbctl restart command."""
    return f"orbctl restart {name}"


def build_vm_info_command(vm_name: str) -> str:
    """Build the orbctl info command."""
    return f"orbctl info {vm_name} --format json"


def build_vm_list_command() -> str:
    """Build the orbctl list command."""
    return "orbctl list -f json"


def build_ssh_info_command(machine: Optional[str] = None) -> str:
    """Build the SSH info command."""
    if machine:
        return f"orbctl info {machine} --format json"
    return "orbctl ssh"


# PyInfra Operations (use command builders)


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

    yield build_vm_create_command(name, image, arch, user)


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
    yield build_vm_clone_command(source_name, new_name)


@operation()
def vm_export(name: str, output_path: str):
    """
    Export an OrbStack VM to a file.

    The VM will be paused during export to prevent data corruption.

    Args:
        name: VM name to export
        output_path: Path where the exported file will be saved (e.g., "backup.tar.zst")
    """
    yield build_vm_export_command(name, output_path)


@operation()
def vm_import(input_path: str, name: str):
    """
    Import an OrbStack VM from a file.

    Creates a new VM from a previously exported VM file.

    Args:
        input_path: Path to the exported VM file (e.g., "backup.tar.zst")
        name: Name for the imported VM
    """
    yield build_vm_import_command(input_path, name)


@operation()
def vm_rename(old_name: str, new_name: str):
    """
    Rename an OrbStack VM.

    Args:
        old_name: Current VM name
        new_name: New VM name
    """
    yield build_vm_rename_command(old_name, new_name)


@operation()
def vm_delete(name: str, force: bool = False):
    """
    Delete OrbStack VM.

    Args:
        name: VM name
        force: Force deletion without confirmation
    """
    yield build_vm_delete_command(name, force)


@operation()
def vm_start(name: str):
    """
    Start OrbStack VM.

    Args:
        name: VM name
    """
    yield build_vm_start_command(name)


@operation()
def vm_stop(name: str, force: bool = False):
    """
    Stop OrbStack VM.

    Args:
        name: VM name
        force: Force stop
    """
    yield build_vm_stop_command(name, force)


@operation()
def vm_restart(name: str):
    """
    Restart OrbStack VM.

    Args:
        name: VM name
    """
    yield build_vm_restart_command(name)


@operation()
def vm_info():
    """
    Get detailed VM information for current host.

    Returns:
        dict: VM information
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return {}

    yield build_vm_info_command(vm_name)


@operation()
def vm_list():
    """
    List all VMs with status.

    Returns:
        list: List of VM information dictionaries
    """
    yield build_vm_list_command()


@operation()
def vm_status():
    """
    Get VM status (running, stopped, etc.) for current host.

    Returns:
        str: VM status
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return "unknown"

    yield build_vm_info_command(vm_name)


@operation()
def vm_ip():
    """
    Get VM IP address for current host.

    Returns:
        str: VM IP address
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return ""

    yield build_vm_info_command(vm_name)


@operation()
def vm_network_info():
    """
    Get VM network information from VM info command for current host.

    Returns:
        dict: Network information
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return {}

    yield build_vm_info_command(vm_name)


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
    if machine is None:
        machine = host.data.get("vm_name", "")

    yield build_ssh_info_command(machine)


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
    if machine is None:
        machine = host.data.get("vm_name", "")

    if not machine:
        return "Error: No machine specified"

    yield build_ssh_info_command(machine)
