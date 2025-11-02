"""
Tests for the OrbStackConnector class.
"""

import json
import subprocess
from unittest import TestCase
from unittest.mock import Mock, patch

from pyinfra.api import StringCommand

from pyinfra_orbstack.connector import OrbStackConnector


class TestOrbStackConnector(TestCase):
    """Test cases for OrbStackConnector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_state = Mock()
        self.mock_host = Mock()
        self.mock_host.data = {"vm_name": "test-vm"}
        self.connector = OrbStackConnector(self.mock_state, self.mock_host)

    def test_handles_execution(self):
        """Test that the connector handles execution."""
        assert OrbStackConnector.handles_execution is True

    def test_make_names_data_success(self):
        """Test successful VM listing."""
        mock_vms = [
            {
                "name": "test-vm-1",
                "id": "vm-1",
                "state": "running",
                "image": {"distro": "ubuntu", "version": "22.04", "arch": "arm64"},
                "config": {"default_username": "ubuntu"},
            }
        ]

        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.stdout = json.dumps(mock_vms)
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = list(OrbStackConnector.make_names_data())

            assert len(result) == 1
            name, data, groups = result[0]
            assert name == "test-vm-1"
            assert data["vm_name"] == "test-vm-1"
            assert "orbstack" in groups
            assert "orbstack_running" in groups
            assert "orbstack_arm64" in groups
            assert "orbstack_ubuntu" in groups

    def test_make_names_data_filter(self):
        """Test VM listing with hostname filter."""
        mock_vms = [
            {
                "name": "test-vm-1",
                "id": "vm-1",
                "state": "running",
                "image": {},
                "config": {},
            },
            {
                "name": "test-vm-2",
                "id": "vm-2",
                "state": "stopped",
                "image": {},
                "config": {},
            },
        ]

        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.stdout = json.dumps(mock_vms)
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = list(OrbStackConnector.make_names_data("test-vm-1"))

            assert len(result) == 1
            name, data, groups = result[0]
            assert name == "test-vm-1"

    def test_make_names_data_error(self):
        """Test error handling in make_names_data."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["orbctl", "list"])

            result = list(OrbStackConnector.make_names_data())
            assert result == []

    def test_make_names_data_json_error(self):
        """Test JSON decode error handling in make_names_data."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.stdout = "invalid json"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = list(OrbStackConnector.make_names_data())
            assert result == []

    def test_connect_no_vm_name(self):
        """Test connection attempt without VM name."""
        self.mock_host.data = {}
        assert not self.connector.connect()

    def test_connect_success(self):
        """Test successful connection."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({"record": {"state": "running"}})

            assert self.connector.connect()

    def test_connect_vm_startup(self):
        """Test connection with VM startup."""
        with patch("subprocess.run") as mock_run:
            # First call: VM not running
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps({"record": {"state": "stopped"}})

            assert self.connector.connect()

    def test_connect_error(self):
        """Test connection error handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["orbctl", "info"])

            assert not self.connector.connect()

    def test_disconnect(self):
        """Test disconnection (should not raise errors)."""
        self.connector.disconnect()  # Should not raise any exceptions

    def test_run_shell_command_no_vm_name(self):
        """Test command execution without VM name."""
        self.mock_host.data = {}
        success, output = self.connector.run_shell_command("echo hello")
        assert not success
        assert "VM name not found" in str(output)

    def test_run_shell_command_success(self):
        """Test successful command execution."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Hello World\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            success, output = self.connector.run_shell_command("echo hello")

            assert success
            assert "Hello World" in str(output)

    def test_run_shell_command_with_user_and_workdir(self):
        """Test command execution with user and working directory."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "/home/ubuntu/project\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            success, output = self.connector.run_shell_command(
                "pwd", user="ubuntu", workdir="/home/ubuntu/project"
            )

            assert success
            assert "/home/ubuntu/project" in str(output)

            # Verify user and workdir are passed as orbctl flags
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "-u",
                "ubuntu",
                "-w",
                "/home/ubuntu/project",
                "sh",
                "-c",
                "pwd",
            ]

    def test_run_shell_command_timeout(self):
        """Test command execution timeout."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_execute.side_effect = subprocess.TimeoutExpired(["orbctl", "run"], 60)

            success, output = self.connector.run_shell_command("sleep 100")

            assert not success
            assert "timed out" in str(output)

    def test_run_shell_command_error(self):
        """Test command execution error."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_execute.side_effect = subprocess.CalledProcessError(
                1, ["orbctl", "run"]
            )

            success, output = self.connector.run_shell_command("invalid-command")

            assert not success
            assert "returned non-zero exit status" in str(output)

    def test_run_shell_command_with_stderr(self):
        """Test command execution with stderr output."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Command not found\n"
            mock_execute.return_value = mock_result

            success, output = self.connector.run_shell_command("invalid-command")

            assert not success
            assert "Command not found" in str(output)

    def test_run_shell_command_non_string_command(self):
        """Test command execution with non-string command (list)."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "test\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            success, output = self.connector.run_shell_command(["echo", "test"])

            assert success
            assert "test" in str(output)

    def test_run_shell_command_string_command_multibit(self):
        """Test command execution with multi-bit StringCommand object."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "/usr/bin/vtysh\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # PyInfra wraps commands like: StringCommand("sh", "-c", "command -v vtysh || true")
            cmd = StringCommand("sh", "-c", "command -v vtysh || true")
            success, output = self.connector.run_shell_command(cmd)

            assert success
            assert "vtysh" in str(output)

            # Verify that the command was passed as separate arguments
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                "command -v vtysh || true",
            ]

    def test_run_shell_command_plain_string_with_shell_features(self):
        """Test plain string commands get wrapped with sh -c for shell feature support."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Plain string from PyInfra facts - should be wrapped in sh -c
            success, output = self.connector.run_shell_command(
                "command -v vtysh || true"
            )

            assert success

            # Verify command was wrapped with sh -c
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                "command -v vtysh || true",
            ]

    def test_run_shell_command_plain_string_with_pipes(self):
        """Test plain string with pipes gets wrapped with sh -c."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "test\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command with pipe - needs shell interpretation
            success, output = self.connector.run_shell_command("echo test | grep test")

            assert success
            assert "test" in str(output)

            # Verify command was wrapped with sh -c
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                "echo test | grep test",
            ]

    def test_run_shell_command_single_bit_string_command(self):
        """Test single-bit StringCommand gets wrapped with sh -c."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Single-bit StringCommand - should be wrapped in sh -c
            cmd = StringCommand(
                "timeout 60 bash -c 'while fuser /var/lib/dpkg/lock; do sleep 1; done' || true"
            )
            success, output = self.connector.run_shell_command(cmd)

            assert success

            # Verify single-bit command was wrapped with sh -c
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                "timeout 60 bash -c 'while fuser /var/lib/dpkg/lock; do sleep 1; done' || true",
            ]

    def test_run_shell_command_complex_nested_command(self):
        """Test complex nested command with timeout and boolean operators."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Complex command with nested bash -c and boolean operators
            complex_cmd = "timeout 60 bash -c 'while fuser /var/lib/dpkg/lock; do sleep 1; done' || true"
            success, output = self.connector.run_shell_command(complex_cmd)

            assert success

            # Verify command was wrapped with sh -c
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                complex_cmd,
            ]

    def test_run_shell_command_with_redirections(self):
        """Test command with redirections gets proper shell wrapping."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command with output redirection
            success, output = self.connector.run_shell_command(
                "echo test > /tmp/output.txt"
            )

            assert success

            # Verify command was wrapped with sh -c
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                "echo test > /tmp/output.txt",
            ]

    def test_run_shell_command_with_logical_and(self):
        """Test command with logical AND operator (&&) gets proper shell wrapping."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "success\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command with logical AND
            success, output = self.connector.run_shell_command("cd /tmp && pwd")

            assert success

            # Verify command was wrapped with sh -c
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                "cd /tmp && pwd",
            ]

    def test_run_shell_command_with_sudo_string_command(self):
        """Test command execution with sudo flag (string command)."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # String command with sudo
            success, output = self.connector.run_shell_command(
                "rm -f /var/lib/dpkg/lock", sudo=True
            )

            assert success

            # Verify sudo was applied using PyInfra's make_unix_command_for_host
            # Format: sudo -H -n sh -c 'command'
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "sh",
                "-c",
                "rm -f /var/lib/dpkg/lock",
            ]

    def test_run_shell_command_with_sudo_and_sudo_user_string_command(self):
        """Test command execution with sudo and sudo_user (string command)."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "postgres\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # String command with sudo and sudo_user
            success, output = self.connector.run_shell_command(
                "whoami", sudo=True, sudo_user="postgres"
            )

            assert success

            # Verify sudo with user using PyInfra's make_unix_command_for_host
            # Format: sudo -H -n -u postgres sh -c 'command'
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "-u",
                "postgres",
                "sh",
                "-c",
                "whoami",
            ]

    def test_run_shell_command_with_sudo_stringcommand_multibit(self):
        """Test multi-bit StringCommand with sudo."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Multi-bit StringCommand with sudo
            cmd = StringCommand("sh", "-c", "apt-get update")
            success, output = self.connector.run_shell_command(cmd, sudo=True)

            assert success

            # Verify sudo was prepended to the bits
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "sh",
                "-c",
                "apt-get update",
            ]

    def test_run_shell_command_with_sudo_stringcommand_singlebit(self):
        """Test single-bit StringCommand with sudo."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Single-bit StringCommand with sudo
            cmd = StringCommand("apt-get update")
            success, output = self.connector.run_shell_command(cmd, sudo=True)

            assert success

            # Verify single-bit command uses PyInfra's make_unix_command_for_host
            # Format: sudo -H -n sh -c 'command'
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "sh",
                "-c",
                "apt-get update",
            ]

    def test_run_shell_command_with_sudo_and_sudo_user_stringcommand(self):
        """Test StringCommand with sudo and sudo_user."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Multi-bit StringCommand with sudo and sudo_user
            cmd = StringCommand("sh", "-c", "psql -c 'SELECT version()'")
            success, output = self.connector.run_shell_command(
                cmd, sudo=True, sudo_user="postgres"
            )

            assert success

            # Verify sudo with user was prepended
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-u",
                "postgres",
                "sh",
                "-c",
                "psql -c 'SELECT version()'",
            ]

    def test_run_shell_command_with_sudo_list_command(self):
        """Test list command with sudo."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # List command with sudo
            success, output = self.connector.run_shell_command(
                ["apt-get", "update"], sudo=True
            )

            assert success

            # Verify list commands are now wrapped in sh -c by make_unix_command_for_host
            # Format: sudo -H -n sh -c "['apt-get', 'update']"
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "sh",
                "-c",
                "['apt-get', 'update']",
            ]

    def test_run_shell_command_with_sudo_and_sudo_user_list_command(self):
        """Test list command with sudo and sudo_user."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # List command with sudo and sudo_user
            success, output = self.connector.run_shell_command(
                ["systemctl", "restart", "nginx"], sudo=True, sudo_user="root"
            )

            assert success

            # Verify list commands are wrapped in sh -c by make_unix_command_for_host
            # Format: sudo -H -n -u root sh -c "['systemctl', 'restart', 'nginx']"
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "-u",
                "root",
                "sh",
                "-c",
                "['systemctl', 'restart', 'nginx']",
            ]

    def test_run_shell_command_with_sudo_special_characters(self):
        """Test sudo with command containing special characters."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command with special characters and sudo
            success, output = self.connector.run_shell_command(
                "echo 'test with spaces' > /etc/config", sudo=True
            )

            assert success

            # Verify make_unix_command_for_host handles special characters
            # Format: sudo -H -n sh -c "command with special chars"
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "sh",
                "-c",
                "echo 'test with spaces' > /etc/config",
            ]

    def test_run_shell_command_with_sudo_logical_negation(self):
        """Test sudo with command containing logical negation (!)."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "MISSING\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command with logical negation - this was the bug that's now fixed!
            # PyInfra's make_unix_command_for_host properly wraps in sh -c
            success, output = self.connector.run_shell_command(
                "! test -e /etc/netplan/01-netcfg.yaml && echo MISSING", sudo=True
            )

            assert success
            assert "MISSING" in str(output)

            # Verify sh -c is used (shell operators work correctly in sh)
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "sh",
                "-c",
                "! test -e /etc/netplan/01-netcfg.yaml && echo MISSING",
            ]

    def test_run_shell_command_with_sudo_exclamation_in_string(self):
        """Test sudo with command containing exclamation mark in a string."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Previous command: !\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command with exclamation in string
            success, output = self.connector.run_shell_command(
                "echo 'Previous command: !' && echo done", sudo=True
            )

            assert success

            # Verify sh -c is used (works correctly with exclamation marks in strings)
            call_args = mock_execute.call_args[0][0]
            assert "sh" in call_args and "-c" in call_args

    def test_run_shell_command_with_sudo_complex_timeout_command(self):
        """Test sudo with complex timeout command from the actual failure."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Complex timeout command that might contain !
            success, output = self.connector.run_shell_command(
                "timeout 60 bash -c 'while fuser /var/lib/dpkg/lock >/dev/null 2>&1; do echo Waiting; sleep 2; done' || true",
                sudo=True,
            )

            assert success

            # Verify sh -c is used (works correctly with complex commands)
            call_args = mock_execute.call_args[0][0]
            assert "sh" in call_args and "-c" in call_args

    def test_run_shell_command_with_sudo_stringcommand_logical_negation(self):
        """Test single-bit StringCommand with sudo and logical negation."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "MISSING\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Single-bit StringCommand with logical negation
            cmd = StringCommand("! test -e /path/to/file && echo MISSING")
            success, output = self.connector.run_shell_command(cmd, sudo=True)

            assert success

            # Verify PyInfra's make_unix_command_for_host is used
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "sh",
                "-c",
                "! test -e /path/to/file && echo MISSING",
            ]

    def test_run_shell_command_with_sudo_and_user_logical_negation(self):
        """Test sudo with sudo_user and logical negation."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command with logical negation and sudo_user
            success, output = self.connector.run_shell_command(
                "! test -e /home/postgres/.profile && echo MISSING",
                sudo=True,
                sudo_user="postgres",
            )

            assert success

            # Verify PyInfra's make_unix_command_for_host handles sudo with user
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sudo",
                "-H",
                "-n",
                "-u",
                "postgres",
                "sh",
                "-c",
                "! test -e /home/postgres/.profile && echo MISSING",
            ]

    def test_run_shell_command_without_sudo(self):
        """Test that commands without sudo flag work normally."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "test\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Command without sudo (default behavior)
            success, output = self.connector.run_shell_command("echo test")

            assert success

            # Verify no sudo was applied
            call_args = mock_execute.call_args[0][0]
            assert call_args == [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "sh",
                "-c",
                "echo test",
            ]

    def test_run_shell_command_with_print_input(self):
        """Test command execution with print_input flag."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "test\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Capture print output
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                success, output = self.connector.run_shell_command(
                    "echo test", print_input=True
                )

            assert success

            # Should print the command being executed
            printed = f.getvalue()
            assert "sh" in printed and "-c" in printed and "echo test" in printed

    def test_run_shell_command_with_underscore_prefixed_arguments(self):
        """Test that underscore-prefixed PyInfra arguments are passed through."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "/tmp\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            # Arguments like _env, _chdir should be passed through to make_unix_command_for_host
            success, output = self.connector.run_shell_command(
                "pwd",
                _env={"TEST_VAR": "value"},
                _chdir="/tmp",
            )

            assert success
            # These underscore-prefixed arguments are handled by make_unix_command_for_host
            # The test verifies they don't cause errors and the command executes
            call_args = mock_execute.call_args[0][0]
            assert "sudo" not in call_args

    def test_put_file_success(self):
        """Test successful file upload."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            success = self.connector.put_file("local.txt", "/remote/path.txt")

            assert success
            mock_run.assert_called_once()

    def test_put_file_no_vm_name(self):
        """Test file upload without VM name."""
        self.mock_host.data = {}
        success = self.connector.put_file("local.txt", "/remote/path.txt")
        assert not success

    def test_put_file_error(self):
        """Test file upload error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["orbctl", "push"])

            success = self.connector.put_file("local.txt", "/remote/path.txt")

            assert not success

    def test_put_file_with_sudo(self):
        """Test file upload with sudo."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful upload to temp location
            mock_run.return_value.returncode = 0

            # Mock successful sudo mv
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_shell.return_value = (True, mock_result)

            success = self.connector.put_file("local.txt", "/etc/config.txt", sudo=True)

            assert success

            # Verify upload to temp location
            assert mock_run.call_count == 1
            push_call = mock_run.call_args[0][0]
            assert push_call[0:4] == ["orbctl", "push", "-m", "test-vm"]
            assert push_call[4] == "local.txt"
            assert push_call[5].startswith("/tmp/pyinfra_orbstack_")

            # Verify sudo mv was called
            assert mock_shell.call_count == 1
            mv_cmd = mock_shell.call_args[0][0]
            assert "sudo -H mv" in mv_cmd
            assert "/etc/config.txt" in mv_cmd

    def test_put_file_with_sudo_and_user(self):
        """Test file upload with sudo and sudo_user."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful upload to temp location
            mock_run.return_value.returncode = 0

            # Mock successful sudo mv
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_shell.return_value = (True, mock_result)

            success = self.connector.put_file(
                "local.txt",
                "/home/postgres/config.txt",
                sudo=True,
                sudo_user="postgres",
            )

            assert success

            # Verify sudo -u was used
            mv_cmd = mock_shell.call_args_list[0][0][0]
            assert "sudo -H -u postgres mv" in mv_cmd

    def test_put_file_with_sudo_and_mode(self):
        """Test file upload with sudo and custom permissions."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful upload
            mock_run.return_value.returncode = 0

            # Mock successful sudo mv and chmod
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_shell.return_value = (True, mock_result)

            success = self.connector.put_file(
                "script.sh", "/usr/local/bin/script.sh", sudo=True, mode="755"
            )

            assert success

            # Verify both mv and chmod were called
            assert mock_shell.call_count == 2
            mv_cmd = mock_shell.call_args_list[0][0][0]
            chmod_cmd = mock_shell.call_args_list[1][0][0]

            assert "sudo -H mv" in mv_cmd
            assert "sudo -H chmod 755" in chmod_cmd

    def test_put_file_with_sudo_mv_fails(self):
        """Test file upload when sudo mv fails."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful upload to temp
            mock_run.return_value.returncode = 0

            # Mock failed sudo mv, then successful cleanup
            mock_shell.side_effect = [
                (False, Mock(stderr="Permission denied")),  # mv fails
                (True, Mock(stderr="")),  # cleanup succeeds
            ]

            success = self.connector.put_file("local.txt", "/etc/config.txt", sudo=True)

            assert not success

            # Verify cleanup was called
            assert mock_shell.call_count == 2
            cleanup_cmd = mock_shell.call_args_list[1][0][0]
            assert "rm -f" in cleanup_cmd

    def test_get_file_with_sudo(self):
        """Test file download with sudo."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful sudo cp and chmod
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_shell.side_effect = [
                (True, mock_result),  # cp
                (True, mock_result),  # chmod
                (True, mock_result),  # rm
            ]

            # Mock successful pull
            mock_run.return_value.returncode = 0

            success = self.connector.get_file("/etc/shadow", "local_shadow", sudo=True)

            assert success

            # Verify sudo cp was called
            cp_cmd = mock_shell.call_args_list[0][0][0]
            assert "sudo -H cp" in cp_cmd
            assert "/etc/shadow" in cp_cmd

            # Verify pull from temp location
            assert mock_run.call_count == 1
            pull_call = mock_run.call_args[0][0]
            assert pull_call[0:4] == ["orbctl", "pull", "-m", "test-vm"]
            assert pull_call[4].startswith("/tmp/pyinfra_orbstack_")
            assert pull_call[5] == "local_shadow"

            # Verify cleanup
            rm_cmd = mock_shell.call_args_list[2][0][0]
            assert "sudo -H rm -f" in rm_cmd

    def test_get_file_with_sudo_and_user(self):
        """Test file download with sudo and sudo_user."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful operations
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_shell.return_value = (True, mock_result)

            # Mock successful pull
            mock_run.return_value.returncode = 0

            success = self.connector.get_file(
                "/var/lib/postgresql/data/pg_hba.conf",
                "pg_hba.conf",
                sudo=True,
                sudo_user="postgres",
            )

            assert success

            # Verify sudo -u was used
            cp_cmd = mock_shell.call_args_list[0][0][0]
            assert "sudo -H -u postgres cp" in cp_cmd

    def test_get_file_with_sudo_cp_fails(self):
        """Test file download when sudo cp fails."""
        with patch.object(self.connector, "run_shell_command") as mock_shell:
            # Mock failed sudo cp
            mock_shell.return_value = (False, Mock(stderr="No such file"))

            success = self.connector.get_file(
                "/etc/nonexistent", "local_file", sudo=True
            )

            assert not success

            # Verify only cp was attempted (no pull or cleanup)
            assert mock_shell.call_count == 1

    def test_get_file_with_sudo_pull_fails(self):
        """Test file download when pull from temp fails."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful sudo cp and chmod
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_shell.return_value = (True, mock_result)

            # Mock failed pull
            mock_run.side_effect = subprocess.CalledProcessError(1, ["orbctl", "pull"])

            success = self.connector.get_file("/etc/config", "local_config", sudo=True)

            assert not success

            # Verify cleanup was still attempted
            assert mock_shell.call_count == 3  # cp, chmod, rm
            rm_cmd = mock_shell.call_args_list[2][0][0]
            assert "sudo -H rm -f" in rm_cmd

    def test_get_file_success(self):
        """Test successful file download."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            success = self.connector.get_file("/remote/path.txt", "local.txt")

            assert success
            mock_run.assert_called_once()

    def test_get_file_no_vm_name(self):
        """Test file download without VM name."""
        self.mock_host.data = {}
        success = self.connector.get_file("/remote/path.txt", "local.txt")
        assert not success

    def test_get_file_error(self):
        """Test file download error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["orbctl", "pull"])

            success = self.connector.get_file("/remote/path.txt", "local.txt")

            assert not success

    def test_execute_with_retry_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        with patch("subprocess.run") as mock_run:
            # Mock subprocess.run to always fail with network error
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "network timeout"
            mock_run.return_value = mock_result

            # Test with max_retries=1 to trigger the max retries exceeded path
            result = self.connector._execute_with_retry(
                ["orbctl", "create", "ubuntu:22.04", "test-vm"],
                max_retries=1,
                is_network_operation=True,
            )

            # Should return the failed result after max retries
            assert result.returncode == 1
            assert "network timeout" in result.stderr

    def test_execute_with_retry_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        with patch("subprocess.run") as mock_run:
            # Mock subprocess.run to raise an unexpected exception
            mock_run.side_effect = ValueError("Unexpected error")

            # This should raise the exception after max retries
            with self.assertRaises(ValueError):
                self.connector._execute_with_retry(
                    ["orbctl", "create", "ubuntu:22.04", "test-vm"], max_retries=1
                )

    def test_execute_with_retry_success_first_attempt(self):
        """Test successful execution on first attempt (no retries needed)."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = self.connector._execute_with_retry(
                ["orbctl", "exec", "-m", "test-vm", "echo", "test"], max_retries=3
            )

            assert result.returncode == 0
            assert result.stdout == "success"
            assert mock_run.call_count == 1  # Only called once

    def test_execute_with_retry_timeout_then_success(self):
        """Test retry logic when command times out first, then succeeds."""
        with patch("subprocess.run") as mock_run, patch("time.sleep"):
            # First call times out, second call succeeds
            mock_success = Mock()
            mock_success.returncode = 0
            mock_success.stdout = "success"
            mock_success.stderr = ""

            mock_run.side_effect = [
                subprocess.TimeoutExpired(["cmd"], 30),
                mock_success,
            ]

            result = self.connector._execute_with_retry(
                ["orbctl", "exec", "-m", "test-vm", "slow-command"],
                max_retries=2,
                timeout=30,
            )

            assert result.returncode == 0
            assert mock_run.call_count == 2

    def test_execute_with_retry_exception_then_success(self):
        """Test retry logic when command raises exception first, then succeeds."""
        with patch("subprocess.run") as mock_run, patch("time.sleep"):
            # First call raises exception, second call succeeds
            mock_success = Mock()
            mock_success.returncode = 0
            mock_success.stdout = "success"
            mock_success.stderr = ""

            mock_run.side_effect = [
                Exception("Temporary error"),
                mock_success,
            ]

            result = self.connector._execute_with_retry(
                ["orbctl", "exec", "-m", "test-vm", "flaky-command"], max_retries=2
            )

            assert result.returncode == 0
            assert mock_run.call_count == 2

    def test_make_names_data_arm64_architecture(self):
        """Test VM with ARM64 architecture gets correct group."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(
                [
                    {
                        "name": "test-vm-arm",
                        "state": "running",
                        "image": {
                            "arch": "arm64",
                            "distro": "ubuntu",
                            "version": "22.04",
                        },
                    }
                ]
            )

            result = list(self.connector.make_names_data())

            assert len(result) == 1
            name, data, groups = result[0]
            assert name == "test-vm-arm"
            assert "orbstack_arm64" in groups
            assert "orbstack_amd64" not in groups

    def test_make_names_data_amd64_architecture(self):
        """Test VM with AMD64 architecture gets correct group."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(
                [
                    {
                        "name": "test-vm-amd",
                        "state": "running",
                        "image": {"arch": "amd64", "distro": "debian", "version": "11"},
                    }
                ]
            )

            result = list(self.connector.make_names_data())

            assert len(result) == 1
            name, data, groups = result[0]
            assert name == "test-vm-amd"
            assert "orbstack_amd64" in groups
            assert "orbstack_arm64" not in groups

    def test_make_names_data_unknown_distro(self):
        """Test VM with unknown distro falls through to else clause."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = json.dumps(
                [
                    {
                        "name": "test-vm-other",
                        "state": "running",
                        "image": {
                            "arch": "arm64",
                            "distro": "some-other-distro",
                            "version": "1.0",
                        },
                    }
                ]
            )

            result = list(self.connector.make_names_data())

            assert len(result) == 1
            name, data, groups = result[0]
            assert name == "test-vm-other"
            # Should still get base groups even with unknown distro
            assert "orbstack" in groups
            assert "orbstack_running" in groups

    def test_put_file_upload_to_temp_fails(self):
        """Test handling of upload failure to temp location with sudo."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["orbctl", "push"])

            success = self.connector.put_file("local.txt", "/etc/config.txt", sudo=True)

            assert not success

    def test_put_file_chmod_fails_warning(self):
        """Test that chmod failure doesn't fail the overall operation."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful upload and mv
            mock_run.return_value.returncode = 0

            # Mock successful mv, failed chmod
            mock_shell.side_effect = [
                (True, Mock(stderr="")),  # mv succeeds
                (False, Mock(stderr="chmod: permission denied")),  # chmod fails
            ]

            success = self.connector.put_file(
                "script.sh", "/usr/local/bin/script.sh", sudo=True, mode="755"
            )

            # Should still succeed even though chmod failed
            assert success
            assert mock_shell.call_count == 2

    def test_get_file_chmod_temp_fails_warning(self):
        """Test that chmod failure on temp file doesn't fail the operation."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful cp, failed chmod, successful pull and rm
            mock_shell.side_effect = [
                (True, Mock(stderr="")),  # cp succeeds
                (False, Mock(stderr="chmod failed")),  # chmod fails
                (True, Mock(stderr="")),  # rm succeeds
            ]

            # Mock successful pull
            mock_run.return_value.returncode = 0

            success = self.connector.get_file("/etc/shadow", "local_shadow", sudo=True)

            # Should still succeed even though chmod failed
            assert success

    def test_get_file_cleanup_fails_warning(self):
        """Test that cleanup failure is logged but doesn't fail the operation."""
        with (
            patch("subprocess.run") as mock_run,
            patch.object(self.connector, "run_shell_command") as mock_shell,
        ):
            # Mock successful operations except cleanup
            mock_shell.side_effect = [
                (True, Mock(stderr="")),  # cp succeeds
                (True, Mock(stderr="")),  # chmod succeeds
                (False, Mock(stderr="rm failed")),  # rm fails
            ]

            # Mock successful pull
            mock_run.return_value.returncode = 0

            success = self.connector.get_file("/etc/config", "local_config", sudo=True)

            # Should still succeed even though cleanup failed
            assert success

    def test_run_shell_command_unexpected_exception(self):
        """Test handling of unexpected exceptions in run_shell_command."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            # Mock _execute_with_retry to raise an unexpected exception
            mock_execute.side_effect = RuntimeError("Unexpected runtime error")

            success, output = self.connector.run_shell_command("echo hello")

            assert not success
            assert "Unexpected error" in str(output)
            assert "Unexpected runtime error" in str(output)
