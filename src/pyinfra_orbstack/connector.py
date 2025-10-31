"""
PyInfra OrbStack Connector

Provides native integration with OrbStack CLI for VM lifecycle management,
command execution, and file transfer operations.
"""

import json
import subprocess
import time
from collections.abc import Generator
from typing import Any, Optional

from pyinfra.api import StringCommand
from pyinfra.connectors.base import BaseConnector
from pyinfra.connectors.util import CommandOutput, OutputLine


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
            **arguments: Additional command arguments

        Returns:
            tuple: (success, CommandOutput)
        """
        try:
            vm_name = self.host.data.get("vm_name")
            if not vm_name:
                return False, CommandOutput(
                    [OutputLine("stderr", "VM name not found in host data")]
                )

            # Build orbctl run command
            cmd = ["orbctl", "run", "-m", vm_name]

            # Add user if specified
            user = arguments.get("user")
            if user:
                cmd.extend(["-u", user])

            # Add working directory if specified
            workdir = arguments.get("workdir")
            if workdir:
                cmd.extend(["-w", workdir])

            # Add the actual command - handle str, StringCommand, and lists
            if isinstance(command, str):
                # Plain strings need to be wrapped in sh -c for shell interpretation
                cmd.extend(["sh", "-c", command])
            elif hasattr(command, "bits"):
                # StringCommand.bits contains individual arguments
                bits = [str(bit) for bit in command.bits]

                # If it's a single-bit command, wrap it in sh -c for shell features
                if len(bits) == 1:
                    cmd.extend(["sh", "-c", bits[0]])
                else:
                    # Multi-bit StringCommand (already has sh -c structure)
                    cmd.extend(bits)
            else:
                # Handle plain lists or other iterables
                cmd.extend([str(arg) for arg in command])

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

            # Create OutputLine objects for stdout and stderr
            combined_lines = []
            if result.stdout:
                for line in result.stdout.splitlines():
                    combined_lines.append(OutputLine("stdout", line))
            if result.stderr:
                for line in result.stderr.splitlines():
                    combined_lines.append(OutputLine("stderr", line))

            success = result.returncode == 0
            output = CommandOutput(combined_lines)

            return success, output

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
        Upload a file to OrbStack VM.

        Args:
            filename_or_io: Local file path or IO object
            remote_filename: Remote file path
            remote_temp_filename: Ignored for OrbStack
            print_output: Whether to print output
            print_input: Whether to print input
            **arguments: Additional arguments

        Returns:
            bool: Upload success status
        """
        try:
            vm_name = self.host.data.get("vm_name")
            if not vm_name:
                return False

            # Use orbctl push to upload file
            subprocess.run(
                ["orbctl", "push", "-m", vm_name, filename_or_io, remote_filename],
                check=True,
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error uploading file to VM {vm_name}: {e}")
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
        Download a file from OrbStack VM.

        Args:
            remote_filename: Remote file path
            filename_or_io: Local file path or IO object
            remote_temp_filename: Ignored for OrbStack
            print_output: Whether to print output
            print_input: Whether to print input
            **arguments: Additional arguments

        Returns:
            bool: Download success status
        """
        try:
            vm_name = self.host.data.get("vm_name")
            if not vm_name:
                return False

            # Use orbctl pull to download file
            subprocess.run(
                ["orbctl", "pull", "-m", vm_name, remote_filename, filename_or_io],
                check=True,
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error downloading file from VM {vm_name}: {e}")
            return False
