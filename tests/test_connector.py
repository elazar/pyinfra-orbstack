"""
Tests for the OrbStackConnector class.
"""

import json
import subprocess
from unittest import TestCase
from unittest.mock import Mock, patch

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
        """Test command execution with non-string command."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "test\n"
            mock_result.stderr = ""
            mock_execute.return_value = mock_result

            success, output = self.connector.run_shell_command(["echo", "test"])

            assert success
            assert "test" in str(output)

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

    def test_run_shell_command_unexpected_exception(self):
        """Test handling of unexpected exceptions in run_shell_command."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            # Mock _execute_with_retry to raise an unexpected exception
            mock_execute.side_effect = RuntimeError("Unexpected runtime error")

            success, output = self.connector.run_shell_command("echo hello")

            assert not success
            assert "Unexpected error" in str(output)
            assert "Unexpected runtime error" in str(output)
