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


# Phase 3B: Configuration Management Command Builders


def build_config_get_command(key: str) -> str:
    """
    Build the orbctl config get command.

    Args:
        key: Configuration key to retrieve (e.g., 'cpu', 'memory_mib')

    Returns:
        str: The complete orbctl config get command
    """
    return f"orbctl config get {key}"


def build_config_set_command(key: str, value: str) -> str:
    """
    Build the orbctl config set command.

    Args:
        key: Configuration key to set
        value: Configuration value

    Returns:
        str: The complete orbctl config set command
    """
    return f"orbctl config set {key} {value}"


def build_config_show_command() -> str:
    """
    Build the orbctl config show command.

    Returns:
        str: The complete orbctl config show command
    """
    return "orbctl config show"


def build_vm_username_set_command(vm_name: str, username: str) -> str:
    """
    Build the command to set per-VM username.

    Args:
        vm_name: VM name
        username: Default username for the VM

    Returns:
        str: The complete orbctl config set command for per-VM username
    """
    return f"orbctl config set machine.{vm_name}.username {username}"


# Phase 3C: Logging and Diagnostics Command Builders


def build_vm_logs_command(vm_name: str, all_logs: bool = False) -> str:
    """
    Build the orbctl logs command.

    Args:
        vm_name: VM name
        all_logs: Whether to show all logs (useful for debugging)

    Returns:
        str: The complete orbctl logs command
    """
    cmd = f"orbctl logs {vm_name}"
    if all_logs:
        cmd += " --all"
    return cmd


# Phase 3A: VM Networking Information Command Builders


def build_vm_network_details_command(vm_name: str) -> str:
    """
    Build the command to get comprehensive network information for a VM.

    Args:
        vm_name: VM name

    Returns:
        str: The complete orbctl info command (returns network details)
    """
    return f"orbctl info {vm_name} --format json"


def build_vm_test_connectivity_command(
    target: str, method: str = "ping", count: int = 3
) -> str:
    """
    Build the command to test network connectivity.

    Args:
        target: Target hostname, IP, or machine-name.orb.local
        method: Test method (ping, curl, nc)
        count: Number of ping attempts (for ping method)

    Returns:
        str: The complete connectivity test command
    """
    if method == "ping":
        return f"ping -c {count} {target}"
    elif method == "curl":
        return f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 {target}"
    elif method == "nc":
        # Extract port if provided (e.g., "host:port"), default to 22
        if ":" in target:
            host, port = target.rsplit(":", 1)
            return f"nc -zv -w 5 {host} {port}"
        return f"nc -zv -w 5 {target} 22"
    else:
        raise ValueError(f"Unsupported connectivity test method: {method}")


def build_vm_dns_lookup_command(hostname: str, lookup_type: str = "A") -> str:
    """
    Build the command to perform DNS lookup.

    Args:
        hostname: Hostname to resolve
        lookup_type: DNS record type (A, AAAA, CNAME, MX, etc.)

    Returns:
        str: The complete DNS lookup command using 'host'
    """
    if lookup_type == "A":
        return f"host -t A {hostname}"
    else:
        return f"host -t {lookup_type} {hostname}"


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


# Phase 3A: VM Networking Information Operations


@operation()
def vm_network_details():
    """
    Get comprehensive network information for current VM.

    Returns:
        dict: Network configuration including:
            - IP addresses (IPv4, IPv6)
            - .orb.local domain name
            - Subnet information
            - Gateway address

    Example:
        >>> vm_network_details()
        {
            "ip4": "198.19.249.2",
            "ip6": "fd39:4e14:6769:1::2",
            "hostname": "my-vm.orb.local"
        }
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return {}

    yield build_vm_network_details_command(vm_name)


@operation()
def vm_test_connectivity(target: str, method: str = "ping", count: int = 3):
    """
    Test network connectivity from current VM to target.

    Uses standard Linux networking tools (ping, curl, nc) to test connectivity.
    Supports OrbStack's .orb.local domain names for inter-VM communication.

    Args:
        target: Target hostname, IP, or machine-name.orb.local
        method: Test method - "ping", "curl", or "nc" (default: "ping")
        count: Number of ping attempts for ping method (default: 3)

    Returns:
        str: Command output showing connectivity status

    Example:
        >>> vm_test_connectivity("other-vm.orb.local")
        "PING other-vm.orb.local (198.19.249.3): 56 data bytes..."

        >>> vm_test_connectivity("http://other-vm.orb.local:8080", method="curl")
        "200"

        >>> vm_test_connectivity("other-vm.orb.local:22", method="nc")
        "Connection to other-vm.orb.local 22 port [tcp/ssh] succeeded!"
    """
    yield build_vm_test_connectivity_command(target, method, count)


@operation()
def vm_dns_lookup(hostname: str, lookup_type: str = "A"):
    """
    Resolve hostname from current VM.

    Performs DNS lookup using the 'host' command. Supports OrbStack's
    .orb.local domain names and standard DNS lookups.

    Args:
        hostname: Hostname to resolve (e.g., "example.com" or "vm-name.orb.local")
        lookup_type: DNS record type - A, AAAA, CNAME, MX, etc. (default: "A")

    Returns:
        str: DNS lookup results

    Example:
        >>> vm_dns_lookup("other-vm.orb.local")
        "other-vm.orb.local has address 198.19.249.3"

        >>> vm_dns_lookup("example.com", lookup_type="AAAA")
        "example.com has IPv6 address 2606:2800:220:1:248:1893:25c8:1946"
    """
    yield build_vm_dns_lookup_command(hostname, lookup_type)


# Phase 3B: Configuration Management Operations


@operation()
def orbstack_config_get(key: str):
    """
    Get OrbStack configuration value.

    Retrieves a global OrbStack configuration setting. Common keys include:
    - cpu: Number of CPU cores allocated to OrbStack
    - memory_mib: Memory in MiB allocated to OrbStack
    - network.subnet4: IPv4 subnet for OrbStack network
    - rosetta: Whether Rosetta translation is enabled

    Note: These are OrbStack-wide settings, not per-VM settings.

    Args:
        key: Configuration key (e.g., 'cpu', 'memory_mib', 'network.subnet4')

    Returns:
        str: Configuration value

    Example:
        >>> orbstack_config_get("cpu")
        # Returns: "11"
        >>> orbstack_config_get("memory_mib")
        # Returns: "16384"
    """
    yield build_config_get_command(key)


@operation()
def orbstack_config_set(key: str, value: str):
    """
    Set OrbStack configuration value.

    Modifies a global OrbStack configuration setting. Changes may require
    restarting OrbStack to take effect.

    Note: These are OrbStack-wide settings, not per-VM settings. Modifying
    resource allocations affects all VMs collectively.

    Args:
        key: Configuration key to set
        value: New configuration value

    Returns:
        bool: Success status

    Example:
        >>> orbstack_config_set("memory_mib", "24576")
        # Sets maximum memory to 24GB
        >>> orbstack_config_set("cpu", "8")
        # Sets CPU cores to 8
    """
    yield build_config_set_command(key, value)


@operation()
def orbstack_config_show():
    """
    Show all OrbStack configuration settings.

    Displays all current OrbStack configuration settings including:
    - Resource allocations (CPU, memory)
    - Network settings
    - Per-machine usernames
    - Feature flags

    Returns:
        str: All configuration settings in key: value format

    Example:
        >>> orbstack_config_show()
        # Returns multi-line output:
        # cpu: 11
        # memory_mib: 16384
        # machine.test-vm.username: ubuntu
        # network.subnet4: 192.168.138.0/23
        # ...
    """
    yield build_config_show_command()


@operation()
def vm_username_set(vm_name: str, username: str):
    """
    Set default username for a specific VM.

    Configures the default username used when connecting to a VM via SSH
    or executing commands. This is the ONLY per-VM configuration setting
    available in OrbStack.

    Note: This is a per-VM setting (unlike CPU/memory which are global).

    Args:
        vm_name: VM name to configure
        username: Default username for the VM

    Returns:
        bool: Success status

    Example:
        >>> vm_username_set("web-server", "ubuntu")
        # Sets default username for web-server VM to ubuntu
        >>> vm_username_set("db-server", "postgres")
        # Sets default username for db-server VM to postgres
    """
    yield build_vm_username_set_command(vm_name, username)


# Phase 3C: Logging and Diagnostics Operations


@operation()
def vm_logs(all_logs: bool = False):
    """
    Get VM system logs for current host.

    Retrieves the unified system logs for the VM. Useful for debugging
    VM startup issues, system errors, or general troubleshooting.

    Args:
        all_logs: Show all logs including debug information (default: False)

    Returns:
        str: VM log output

    Example:
        >>> vm_logs()
        # Returns recent VM logs
        >>> vm_logs(all_logs=True)
        # Returns all logs including debug information

    Note:
        This retrieves OrbStack's unified logs for the VM, not logs from
        inside the VM. To get logs from services running inside the VM,
        use standard PyInfra operations like server.shell().
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return "Error: No VM name specified"

    yield build_vm_logs_command(vm_name, all_logs)


@operation()
def vm_status_detailed():
    """
    Get detailed status information for current VM.

    Provides comprehensive status including:
    - Running state (running, stopped, etc.)
    - Resource usage information
    - Network configuration
    - Recent activity

    Returns:
        dict: Detailed VM status information

    Example:
        >>> vm_status_detailed()
        # Returns: {
        #   'name': 'my-vm',
        #   'state': 'running',
        #   'ip4': '192.168.138.2',
        #   'image': 'ubuntu:22.04',
        #   ...
        # }

    Note:
        This uses the same orbctl info command as vm_info() but is
        intended for status checking and monitoring purposes.
    """
    vm_name = host.data.get("vm_name")
    if not vm_name:
        return {}

    yield build_vm_info_command(vm_name)
