"""
PyInfra OrbStack Connector

Provides native integration with OrbStack CLI for VM lifecycle management,
command execution, and file transfer operations.
"""

import json
import shlex
import subprocess
import time
from collections.abc import Generator
from typing import Any, Optional

from pyinfra.api import StringCommand
from pyinfra.connectors.base import BaseConnector
from pyinfra.connectors.util import (
    CommandOutput,
    OutputLine,
    make_unix_command_for_host,
)


class OrbStackConnector(BaseConnector):
    """
    PyInfra connector for OrbStack VM management.

    Provides native integration with OrbStack CLI for VM lifecycle management,
    command execution, and file transfer operations.
    """

    handles_execution = True

    def __init__(self, state: Any, host: Any) -> None:
        """Initialize the OrbStack connector."""
        super().__init__(state, host)

        # Initialize connector_data if not present (needed for make_unix_command_for_host)
        if not hasattr(host, "connector_data") or not isinstance(
            host.connector_data, dict
        ):
            host.connector_data = {}

    def _execute_with_retry(
        self,
        cmd: list[str],
        max_retries: int = 3,
        base_delay: float = 2.0,
        timeout: Optional[int] = None,
        is_network_operation: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Execute a command with retry logic for network resilience.

        Args:
            cmd: Command to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries (will be exponential)
            timeout: Command timeout in seconds
            is_network_operation: Whether this is a network-heavy operation

        Returns:
            CompletedProcess result
        """
        for attempt in range(max_retries + 1):
            try:
                # Use longer timeout for network operations
                cmd_timeout = timeout or (180 if is_network_operation else 60)

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=cmd_timeout,
                )

                if result.returncode == 0:
                    return result

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

                # Retry network errors or if this is a network operation
                if (is_network_error or is_network_operation) and attempt < max_retries:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    print(
                        f"Network error, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    return result

            except subprocess.TimeoutExpired as e:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    print(
                        f"Command timed out, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise e
            except Exception as e:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    print(
                        f"Command failed: {str(e)}, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise e

        # This should never be reached, but just in case
        return subprocess.CompletedProcess(
            cmd, 1, "", "Max retries exceeded"
        )  # pragma: no cover

    @staticmethod
    def make_names_data(
        hostname: Optional[str] = None,
    ) -> Generator[tuple[str, dict, list[str]], None, None]:
        """
        Generate list of hosts from OrbStack VMs.

        Args:
            hostname: Optional VM name filter

        Yields:
            tuple: (name, data, group_names)
        """
        try:
            # Get list of VMs from OrbStack
            result = subprocess.run(
                ["orbctl", "list", "-f", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            vms = json.loads(result.stdout)

            for vm in vms:
                vm_name = vm.get("name", "")
                if hostname and vm_name != hostname:
                    continue

                # Extract VM data for PyInfra
                vm_data = {
                    "orbstack_vm": True,
                    "vm_name": vm_name,
                    "vm_id": vm.get("id", ""),
                    "vm_status": vm.get("state", "unknown"),
                    "vm_distro": vm.get("image", {}).get("distro", ""),
                    "vm_version": vm.get("image", {}).get("version", ""),
                    "vm_arch": vm.get("image", {}).get("arch", ""),
                    "vm_username": vm.get("config", {}).get("default_username", ""),
                }

                # Determine groups based on VM characteristics
                groups = ["orbstack"]
                if vm.get("state") == "running":
                    groups.append("orbstack_running")
                elif vm.get("state") == "stopped":
                    groups.append("orbstack_stopped")

                if vm.get("image", {}).get("arch") == "arm64":
                    groups.append("orbstack_arm64")
                elif vm.get("image", {}).get("arch") == "amd64":
                    groups.append("orbstack_amd64")

                # Add distro-based groups
                distro = vm.get("image", {}).get("distro", "")
                if distro:
                    groups.append(f"orbstack_{distro}")

                yield vm_name, vm_data, groups

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            # Handle errors gracefully
            print(f"Error listing OrbStack VMs: {e}")
            return

    def connect(self) -> bool:
        """
        Establish connection to OrbStack VM.

        Returns:
            bool: Connection success status

        Note:
            Overrides BaseConnector.connect() to return bool for status checking.
            Base class returns None, but returning bool is more useful.
        """
        try:
            vm_name = self.host.data.get("vm_name")
            if not vm_name:
                return False

            # Verify VM exists and is accessible
            result = subprocess.run(
                ["orbctl", "info", vm_name, "-f", "json"],
                capture_output=True,
                text=True,
                check=True,
            )

            vm_info = json.loads(result.stdout)
            if vm_info.get("record", {}).get("state") == "running":
                return True

            # Try to start the VM if it's not running
            subprocess.run(
                ["orbctl", "start", vm_name],
                check=True,
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error connecting to VM {vm_name}: {e}")
            return False

    def disconnect(self) -> None:
        """
        Clean up connection resources.
        """
        # No persistent connections to clean up for OrbStack CLI
        pass

    def run_shell_command(
        self,
        command: StringCommand,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Any,
    ) -> tuple[bool, CommandOutput]:
        """
        Execute a shell command in OrbStack VM.

        Args:
            command: Command to execute
            print_output: Whether to print command output
            print_input: Whether to print command input
            **arguments: Additional command arguments (sudo, sudo_user, etc.)

        Returns:
            tuple: (success, CommandOutput)
        """
        try:
            vm_name = self.host.data.get("vm_name")
            if not vm_name:
                return False, CommandOutput(
                    [OutputLine("stderr", "VM name not found in host data")]
                )

            # Check if command is already wrapped (multi-bit StringCommand starting with shell)
            # Operations send pre-wrapped commands like: StringCommand("sh", "-c", "command")
            # Facts send unwrapped commands like: "! test -e /path || ..."
            is_prewrapped = False
            if hasattr(command, "bits") and len(command.bits) >= 2:
                # Multi-bit command like ('sh', '-c', 'actual command')
                first_bit = str(command.bits[0])
                if first_bit in ("sh", "bash"):
                    is_prewrapped = True

            if is_prewrapped:
                # Pre-wrapped command from operations - use directly
                # But still need to handle sudo
                sudo = arguments.get("sudo", arguments.get("_sudo", False))
                sudo_user = arguments.get("sudo_user", arguments.get("_sudo_user"))

                bits = [str(bit) for bit in command.bits]

                if sudo:
                    if sudo_user:
                        bits = ["sudo", "-H", "-u", sudo_user] + bits
                    else:
                        bits = ["sudo", "-H"] + bits

                command_args = bits
            else:
                # Unwrapped command from facts - let PyInfra handle wrapping
                # Convert legacy argument names to underscore-prefixed versions
                # and filter out OrbStack-specific arguments that PyInfra doesn't understand
                pyinfra_arguments = {}
                orbstack_specific_args = {"user", "workdir", "max_retries", "timeout"}

                for key, value in arguments.items():
                    if key in orbstack_specific_args:
                        # Skip OrbStack-specific arguments
                        continue
                    elif key == "sudo":
                        pyinfra_arguments["_sudo"] = value
                    elif key == "sudo_user":
                        pyinfra_arguments["_sudo_user"] = value
                    elif not key.startswith("_"):
                        # Pass through other non-sudo arguments
                        pyinfra_arguments[key] = value
                    else:
                        # Already has underscore prefix
                        pyinfra_arguments[key] = value

                unix_command = make_unix_command_for_host(
                    self.state,
                    self.host,
                    command,
                    **pyinfra_arguments,
                )
                actual_command = unix_command.get_raw_value()

                # Parse the command into arguments using shlex
                command_args = shlex.split(actual_command)

            # Build orbctl run command with parsed arguments
            cmd = ["orbctl", "run", "-m", vm_name]

            # Add OrbStack-specific flags if provided
            user = arguments.get("user")
            if user:
                cmd.extend(["-u", user])

            workdir = arguments.get("workdir")
            if workdir:
                cmd.extend(["-w", workdir])

            cmd.extend(command_args)

            if print_input:
                command_str = " ".join(command_args)
                print(
                    f"{self.host.print_prefix}>>> {command_str}",
                    file=None,
                )

            # Determine if this is a network-heavy operation
            command_str = str(command).lower()
            is_network_operation = any(
                keyword in command_str
                for keyword in [
                    "create",
                    "download",
                    "pull",
                    "fetch",
                    "wget",
                    "curl",
                    "apt",
                    "yum",
                    "dnf",
                ]
            )

            # Execute command with retry logic
            result = self._execute_with_retry(
                cmd,
                max_retries=arguments.get("max_retries", 3),
                timeout=arguments.get("timeout"),
                is_network_operation=is_network_operation,
            )

            # Parse output into CommandOutput format
            output_lines = []
            if result.stdout:
                for line in result.stdout.splitlines():
                    output_lines.append(OutputLine("stdout", line))
            if result.stderr:
                for line in result.stderr.splitlines():
                    output_lines.append(OutputLine("stderr", line))

            if print_output:
                for line in output_lines:
                    prefix = self.host.print_prefix
                    print(
                        f"{prefix}{line.line}",
                        file=None if line.stream == "stdout" else None,
                    )

            success = result.returncode == 0
            return success, CommandOutput(output_lines)

        except subprocess.TimeoutExpired:
            return False, CommandOutput([OutputLine("stderr", "Command timed out")])
        except subprocess.CalledProcessError as e:
            return False, CommandOutput([OutputLine("stderr", str(e))])
        except Exception as e:
            return False, CommandOutput(
                [OutputLine("stderr", f"Unexpected error: {str(e)}")]
            )

    def put_file(
        self,
        filename_or_io: Any,
        remote_filename: str,
        remote_temp_filename: Any = None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Any,
    ) -> bool:
        """
        Upload a file to OrbStack VM with sudo support.

        Args:
            filename_or_io: Local file path or IO object
            remote_filename: Remote file path
            remote_temp_filename: Ignored for OrbStack
            print_output: Whether to print output
            print_input: Whether to print input
            **arguments: Additional arguments (sudo, sudo_user, mode)

        Returns:
            bool: Upload success status
        """
        try:
            vm_name = self.host.data.get("vm_name")
            if not vm_name:
                print("Error: VM name not found in host data")
                return False

            sudo = arguments.get("sudo", arguments.get("_sudo", False))
            sudo_user = arguments.get("sudo_user", arguments.get("_sudo_user"))
            mode = arguments.get("mode")  # Custom file permissions (e.g., "644", "755")

            if sudo:
                import os

                # Generate unique temp filename
                temp_remote = f"/tmp/pyinfra_orbstack_{os.urandom(8).hex()}"

                if print_output:
                    print(f"Uploading file to temp location: {temp_remote}")

                # Upload to temp location (user-accessible)
                try:
                    subprocess.run(
                        ["orbctl", "push", "-m", vm_name, filename_or_io, temp_remote],
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Error uploading file to temp location: {e}")
                    return False

                # Build sudo mv command
                if sudo_user:
                    mv_cmd = f"sudo -H -u {sudo_user} mv {shlex.quote(temp_remote)} {shlex.quote(remote_filename)}"
                else:
                    mv_cmd = f"sudo -H mv {shlex.quote(temp_remote)} {shlex.quote(remote_filename)}"

                if print_output:
                    print(
                        f"Moving file to final destination with sudo: {remote_filename}"
                    )

                # Execute move with sudo
                success, output = self.run_shell_command(mv_cmd)

                if not success:
                    print(f"Error moving file to {remote_filename}: {output.stderr}")
                    # Try to clean up temp file
                    cleanup_cmd = f"rm -f {shlex.quote(temp_remote)}"
                    self.run_shell_command(cleanup_cmd)
                    return False

                # Set custom permissions if specified
                if mode:
                    if sudo_user:
                        chmod_cmd = f"sudo -H -u {sudo_user} chmod {mode} {shlex.quote(remote_filename)}"
                    else:
                        chmod_cmd = (
                            f"sudo -H chmod {mode} {shlex.quote(remote_filename)}"
                        )

                    if print_output:
                        print(f"Setting permissions: {mode}")

                    perm_success, perm_output = self.run_shell_command(chmod_cmd)
                    if not perm_success:
                        print(
                            f"Warning: Failed to set permissions {mode}: {perm_output.stderr}"
                        )
                        # Don't fail the overall operation if permissions fail

                return True
            else:
                # Normal upload without sudo
                subprocess.run(
                    ["orbctl", "push", "-m", vm_name, filename_or_io, remote_filename],
                    check=True,
                )
                return True

        except subprocess.CalledProcessError as e:
            print(f"Error uploading file to VM {vm_name}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error uploading file: {e}")
            return False

    def get_file(
        self,
        remote_filename: str,
        filename_or_io: Any,
        remote_temp_filename: Any = None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Any,
    ) -> bool:
        """
        Download a file from OrbStack VM with sudo support.

        Args:
            remote_filename: Remote file path
            filename_or_io: Local file path or IO object
            remote_temp_filename: Ignored for OrbStack
            print_output: Whether to print output
            print_input: Whether to print input
            **arguments: Additional arguments (sudo, sudo_user)

        Returns:
            bool: Download success status
        """
        try:
            vm_name = self.host.data.get("vm_name")
            if not vm_name:
                print("Error: VM name not found in host data")
                return False

            sudo = arguments.get("sudo", arguments.get("_sudo", False))
            sudo_user = arguments.get("sudo_user", arguments.get("_sudo_user"))

            if sudo:
                import os

                # Generate unique temp filename
                temp_remote = f"/tmp/pyinfra_orbstack_{os.urandom(8).hex()}"

                if print_output:
                    print(f"Copying file to temp location with sudo: {temp_remote}")

                # Copy to temp location with sudo
                if sudo_user:
                    cp_cmd = f"sudo -H -u {sudo_user} cp {shlex.quote(remote_filename)} {shlex.quote(temp_remote)}"
                else:
                    cp_cmd = f"sudo -H cp {shlex.quote(remote_filename)} {shlex.quote(temp_remote)}"

                success, output = self.run_shell_command(cp_cmd)
                if not success:
                    print(f"Error copying file from {remote_filename}: {output.stderr}")
                    return False

                # Make temp file readable (in case source had restrictive permissions)
                chmod_cmd = f"sudo -H chmod 644 {shlex.quote(temp_remote)}"
                if print_output:
                    print("Making temp file readable")

                chmod_success, chmod_output = self.run_shell_command(chmod_cmd)
                if not chmod_success:
                    print(
                        f"Warning: Failed to make temp file readable: {chmod_output.stderr}"
                    )
                    # Try to continue anyway

                if print_output:
                    print(f"Downloading from temp location: {temp_remote}")

                # Download from temp location
                try:
                    subprocess.run(
                        ["orbctl", "pull", "-m", vm_name, temp_remote, filename_or_io],
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Error downloading file from temp location: {e}")
                    # Clean up temp file before returning
                    rm_cmd = f"sudo -H rm -f {shlex.quote(temp_remote)}"
                    self.run_shell_command(rm_cmd)
                    return False

                # Clean up temp file
                if print_output:
                    print("Cleaning up temp file")

                rm_cmd = f"sudo -H rm -f {shlex.quote(temp_remote)}"
                rm_success, rm_output = self.run_shell_command(rm_cmd)
                if not rm_success:
                    print(
                        f"Warning: Failed to clean up temp file {temp_remote}: {rm_output.stderr}"
                    )
                    # Don't fail the overall operation if cleanup fails

                return True
            else:
                # Normal download without sudo
                subprocess.run(
                    ["orbctl", "pull", "-m", vm_name, remote_filename, filename_or_io],
                    check=True,
                )
                return True

        except subprocess.CalledProcessError as e:
            print(f"Error downloading file from VM {vm_name}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error downloading file: {e}")
            return False
