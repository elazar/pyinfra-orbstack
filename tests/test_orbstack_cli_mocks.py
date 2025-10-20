"""
Comprehensive unit tests with accurate OrbStack CLI mocks.

These tests use detailed mocks that accurately mimic the behavior of the actual
OrbStack CLI, including command formats, JSON responses, and error conditions.
"""

import json
import subprocess
from unittest.mock import Mock, patch

from pyinfra_orbstack.connector import OrbStackConnector


class TestOrbStackCLIMocks:
    """Test cases with accurate OrbStack CLI mocks."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock state and host for connector tests
        self.mock_state = Mock()
        self.mock_host = Mock()
        self.mock_host.data = {"vm_name": "test-vm"}

    @patch("subprocess.run")
    def test_make_names_data_realistic_vm_list(self, mock_run):
        """Test VM listing with realistic OrbStack JSON response."""
        # Mock realistic OrbStack VM list response
        mock_result = Mock()
        mock_result.stdout = json.dumps(
            [
                {
                    "id": "01K2G8TY5GM9C3CN95KCB4ZG8B",
                    "name": "web-server",
                    "image": {
                        "distro": "ubuntu",
                        "version": "jammy",
                        "arch": "arm64",
                        "variant": "default",
                    },
                    "config": {"isolated": False, "default_username": "ubuntu"},
                    "builtin": False,
                    "state": "running",
                },
                {
                    "id": "01K2G8VMTK5YKJRYVRT367C4B9",
                    "name": "db-server",
                    "image": {
                        "distro": "ubuntu",
                        "version": "jammy",
                        "arch": "amd64",
                        "variant": "default",
                    },
                    "config": {"isolated": False, "default_username": "postgres"},
                    "builtin": False,
                    "state": "stopped",
                },
                {
                    "id": "01K2G8VMTK5YKJRYVRT367C4B9",
                    "name": "router-vm",
                    "image": {
                        "distro": "voidlinux",
                        "version": "current",
                        "arch": "arm64",
                        "variant": "default",
                    },
                    "config": {"isolated": False, "default_username": "root"},
                    "builtin": False,
                    "state": "running",
                },
            ]
        )
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Test the method
        vms = list(OrbStackConnector.make_names_data())

        assert len(vms) == 3

        # Check web-server VM
        vm_name, vm_data, groups = vms[0]
        assert vm_name == "web-server"
        assert vm_data["vm_name"] == "web-server"
        assert vm_data["vm_id"] == "01K2G8TY5GM9C3CN95KCB4ZG8B"
        assert vm_data["vm_status"] == "running"
        assert vm_data["vm_distro"] == "ubuntu"
        assert vm_data["vm_version"] == "jammy"
        assert vm_data["vm_arch"] == "arm64"
        assert vm_data["vm_username"] == "ubuntu"
        assert "orbstack" in groups
        assert "orbstack_running" in groups
        assert "orbstack_arm64" in groups
        assert "orbstack_ubuntu" in groups

        # Check db-server VM
        vm_name, vm_data, groups = vms[1]
        assert vm_name == "db-server"
        assert vm_data["vm_status"] == "stopped"
        assert vm_data["vm_arch"] == "amd64"
        assert vm_data["vm_username"] == "postgres"
        assert "orbstack_stopped" in groups
        assert "orbstack_amd64" in groups

        # Check router-vm
        vm_name, vm_data, groups = vms[2]
        assert vm_name == "router-vm"
        assert vm_data["vm_distro"] == "voidlinux"
        assert vm_data["vm_version"] == "current"
        assert vm_data["vm_username"] == "root"
        assert "orbstack_voidlinux" in groups

        # Verify orbctl command was called correctly
        mock_run.assert_called_once_with(
            ["orbctl", "list", "-f", "json"], capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    def test_make_names_data_filter_by_name(self, mock_run):
        """Test VM listing with name filter (realistic behavior)."""
        # Mock response with multiple VMs
        mock_result = Mock()
        mock_result.stdout = json.dumps(
            [
                {
                    "id": "01K2G8TY5GM9C3CN95KCB4ZG8B",
                    "name": "web-server",
                    "image": {"distro": "ubuntu", "version": "jammy", "arch": "arm64"},
                    "config": {"default_username": "ubuntu"},
                    "state": "running",
                },
                {
                    "id": "01K2G8VMTK5YKJRYVRT367C4B9",
                    "name": "db-server",
                    "image": {"distro": "ubuntu", "version": "jammy", "arch": "amd64"},
                    "config": {"default_username": "postgres"},
                    "state": "stopped",
                },
            ]
        )
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Test filtering (note: OrbStack doesn't support name filtering in list command)
        # The filtering should happen in Python code
        vms = list(OrbStackConnector.make_names_data("web-server"))

        assert len(vms) == 1
        vm_name, vm_data, groups = vms[0]
        assert vm_name == "web-server"

    @patch("subprocess.run")
    def test_connect_vm_running(self, mock_run):
        """Test connection to running VM with realistic info response."""
        # Mock realistic orbctl info response for running VM
        mock_result = Mock()
        mock_result.stdout = json.dumps(
            {
                "record": {
                    "id": "01K2G8TY5GM9C3CN95KCB4ZG8B",
                    "name": "test-vm",
                    "image": {"distro": "ubuntu", "version": "jammy", "arch": "arm64"},
                    "config": {"isolated": False, "default_username": "ubuntu"},
                    "state": "running",
                },
                "disk_size": 962924544,
                "ip4": "198.19.249.76",
                "ip6": "fd07:b51a:cc66:0:b476:dbff:fe73:161e",
            }
        )
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.connect()

        assert result is True

        # Verify orbctl info was called correctly
        mock_run.assert_called_once_with(
            ["orbctl", "info", "test-vm", "-f", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_connect_vm_stopped_then_start(self, mock_run):
        """Test connection to stopped VM that gets started."""
        # Mock VM not running, then startup success
        mock_run.side_effect = [
            Mock(
                stdout=json.dumps(
                    {
                        "record": {
                            "id": "01K2G8TY5GM9C3CN95KCB4ZG8B",
                            "name": "test-vm",
                            "state": "stopped",
                        }
                    }
                ),
                returncode=0,
            ),
            Mock(returncode=0),  # orbctl start success
        ]

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.connect()

        assert result is True

        # Verify both commands were called
        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["orbctl", "info", "test-vm", "-f", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        mock_run.assert_any_call(["orbctl", "start", "test-vm"], check=True)

    @patch("subprocess.run")
    def test_run_shell_command_basic(self, mock_run):
        """Test basic command execution with realistic response."""
        # Mock successful command execution
        mock_result = Mock()
        mock_result.stdout = "Hello from Ubuntu 22.04.3 LTS\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("uname -a")

        assert success is True
        assert output.stdout == "Hello from Ubuntu 22.04.3 LTS"

        # Verify orbctl run was called correctly
        mock_run.assert_called_once_with(
            ["orbctl", "run", "-m", "test-vm", "uname", "-a"],
            capture_output=True,
            text=True,
            timeout=60,
        )

    @patch("subprocess.run")
    def test_run_shell_command_with_user_and_workdir(self, mock_run):
        """Test command execution with user and working directory."""
        # Mock successful command execution
        mock_result = Mock()
        mock_result.stdout = "/home/ubuntu/project\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command(
            "pwd", user="ubuntu", workdir="/home/ubuntu/project"
        )

        assert success is True
        assert output.stdout == "/home/ubuntu/project"

        # Verify orbctl run was called with correct flags
        mock_run.assert_called_once_with(
            [
                "orbctl",
                "run",
                "-m",
                "test-vm",
                "-u",
                "ubuntu",
                "-w",
                "/home/ubuntu/project",
                "pwd",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

    @patch("subprocess.run")
    def test_run_shell_command_with_stderr(self, mock_run):
        """Test command execution with stderr output."""
        # Mock command with stderr
        mock_result = Mock()
        mock_result.stdout = "package installed successfully\n"
        mock_result.stderr = "WARNING: This package is deprecated\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("apt install package")

        assert success is True
        assert output.stdout == "package installed successfully"
        assert output.stderr == "WARNING: This package is deprecated"

    @patch("subprocess.run")
    def test_run_shell_command_error(self, mock_run):
        """Test command execution error with realistic error response."""
        # Mock command failure
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "bash: commandnotfound: command not found\n"
        mock_result.returncode = 127
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("commandnotfound")

        assert success is False
        assert "command not found" in output.stderr

    @patch("subprocess.run")
    def test_run_shell_command_timeout(self, mock_run):
        """Test command execution timeout."""
        # Mock timeout error
        mock_run.side_effect = subprocess.TimeoutExpired("orbctl", 30)

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("sleep 60", timeout=30)

        assert success is False
        assert "Command timed out" in output.stderr

    @patch("subprocess.run")
    def test_put_file_success(self, mock_run):
        """Test successful file upload with realistic behavior."""
        # Mock successful file upload
        mock_run.return_value = Mock(returncode=0)

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.put_file("/local/config.txt", "/remote/config.txt")

        assert result is True

        # Verify orbctl push was called correctly
        mock_run.assert_called_once_with(
            [
                "orbctl",
                "push",
                "-m",
                "test-vm",
                "/local/config.txt",
                "/remote/config.txt",
            ],
            check=True,
        )

    @patch("subprocess.run")
    def test_put_file_to_home_directory(self, mock_run):
        """Test file upload to home directory (default behavior)."""
        # Mock successful file upload
        mock_run.return_value = Mock(returncode=0)

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.put_file("/local/script.sh", "script.sh")

        assert result is True

        # Verify orbctl push was called correctly
        mock_run.assert_called_once_with(
            ["orbctl", "push", "-m", "test-vm", "/local/script.sh", "script.sh"],
            check=True,
        )

    @patch("subprocess.run")
    def test_put_file_error(self, mock_run):
        """Test file upload error with realistic error response."""
        # Mock file upload failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "orbctl", "Error: No such file or directory"
        )

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.put_file("/nonexistent/file.txt", "/remote/file.txt")

        assert result is False

    @patch("subprocess.run")
    def test_get_file_success(self, mock_run):
        """Test successful file download with realistic behavior."""
        # Mock successful file download
        mock_run.return_value = Mock(returncode=0)

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.get_file("/remote/logs.txt", "/local/logs.txt")

        assert result is True

        # Verify orbctl pull was called correctly
        mock_run.assert_called_once_with(
            ["orbctl", "pull", "-m", "test-vm", "/remote/logs.txt", "/local/logs.txt"],
            check=True,
        )

    @patch("subprocess.run")
    def test_get_file_from_home_directory(self, mock_run):
        """Test file download from home directory."""
        # Mock successful file download
        mock_run.return_value = Mock(returncode=0)

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.get_file("config.txt", "/local/config.txt")

        assert result is True

        # Verify orbctl pull was called correctly
        mock_run.assert_called_once_with(
            ["orbctl", "pull", "-m", "test-vm", "config.txt", "/local/config.txt"],
            check=True,
        )

    @patch("subprocess.run")
    def test_get_file_error(self, mock_run):
        """Test file download error with realistic error response."""
        # Mock file download failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "orbctl", "Error: No such file or directory"
        )

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.get_file("/remote/nonexistent.txt", "/local/file.txt")

        assert result is False

    @patch("subprocess.run")
    def test_make_names_data_empty_list(self, mock_run):
        """Test VM listing with empty result (no VMs)."""
        # Mock empty VM list
        mock_result = Mock()
        mock_result.stdout = "[]"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        vms = list(OrbStackConnector.make_names_data())

        assert len(vms) == 0

    @patch("subprocess.run")
    def test_make_names_data_cli_error(self, mock_run):
        """Test VM listing with CLI error."""
        # Mock orbctl error
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "orbctl", "Error: OrbStack is not running"
        )

        vms = list(OrbStackConnector.make_names_data())

        assert len(vms) == 0

    @patch("subprocess.run")
    def test_make_names_data_json_error(self, mock_run):
        """Test VM listing with invalid JSON response."""
        # Mock successful subprocess but invalid JSON
        mock_result = Mock()
        mock_result.stdout = "invalid json response"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        vms = list(OrbStackConnector.make_names_data())

        assert len(vms) == 0

    @patch("subprocess.run")
    def test_connect_vm_not_found(self, mock_run):
        """Test connection to non-existent VM."""
        # Mock VM not found error
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "orbctl", "Error: Machine 'nonexistent-vm' not found"
        )

        self.mock_host.data = {"vm_name": "nonexistent-vm"}
        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.connect()

        assert result is False

    @patch("subprocess.run")
    def test_connect_start_failure(self, mock_run):
        """Test connection when VM start fails."""
        # Mock VM not running, then startup failure
        mock_run.side_effect = [
            Mock(
                stdout=json.dumps(
                    {
                        "record": {
                            "id": "01K2G8TY5GM9C3CN95KCB4ZG8B",
                            "name": "test-vm",
                            "state": "stopped",
                        }
                    }
                ),
                returncode=0,
            ),
            subprocess.CalledProcessError(1, "orbctl", "Error: Failed to start VM"),
        ]

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.connect()

        assert result is False

    def test_connect_no_vm_name(self):
        """Test connection with no VM name in host data."""
        self.mock_host.data = {}
        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.connect()

        assert result is False

    def test_run_shell_command_no_vm_name(self):
        """Test command execution with no VM name."""
        self.mock_host.data = {}
        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("echo hello")

        assert success is False
        assert "VM name not found" in output.stderr

    def test_put_file_no_vm_name(self):
        """Test file upload with no VM name."""
        self.mock_host.data = {}
        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.put_file("/local/file.txt", "/remote/file.txt")

        assert result is False

    def test_get_file_no_vm_name(self):
        """Test file download with no VM name."""
        self.mock_host.data = {}
        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.get_file("/remote/file.txt", "/local/file.txt")

        assert result is False

    def test_disconnect_no_op(self):
        """Test disconnect method (should be no-op)."""
        connector = OrbStackConnector(self.mock_state, self.mock_host)
        # Should not raise any exceptions
        connector.disconnect()


class TestOrbStackCLIEdgeCases:
    """Test edge cases and unusual OrbStack CLI scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_state = Mock()
        self.mock_host = Mock()
        self.mock_host.data = {"vm_name": "test-vm"}

    @patch("subprocess.run")
    def test_make_names_data_malformed_json(self, mock_run):
        """Test VM listing with malformed JSON response."""
        # Mock partially valid JSON
        mock_result = Mock()
        mock_result.stdout = '[{"name": "test-vm", "state": "running"}, {"incomplete":'
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        vms = list(OrbStackConnector.make_names_data())

        assert len(vms) == 0

    @patch("subprocess.run")
    def test_make_names_data_missing_fields(self, mock_run):
        """Test VM listing with missing fields in JSON response."""
        # Mock JSON with missing fields
        mock_result = Mock()
        mock_result.stdout = json.dumps(
            [
                {
                    "name": "test-vm",
                    # Missing id, image, config, state
                }
            ]
        )
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        vms = list(OrbStackConnector.make_names_data())

        assert len(vms) == 1
        vm_name, vm_data, groups = vms[0]
        assert vm_name == "test-vm"
        assert vm_data["vm_name"] == "test-vm"
        # Missing fields should have empty string values (not None)
        assert vm_data.get("vm_id") == ""
        assert vm_data.get("vm_status") == "unknown"

    @patch("subprocess.run")
    def test_run_shell_command_large_output(self, mock_run):
        """Test command execution with large output."""
        # Mock command with large output
        large_output = "line " + "\nline ".join(str(i) for i in range(1000))
        mock_result = Mock()
        mock_result.stdout = large_output
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("cat large_file.txt")

        assert success is True
        assert output.stdout == large_output

    @patch("subprocess.run")
    def test_run_shell_command_binary_output(self, mock_run):
        """Test command execution with binary output."""
        # Mock command with binary output
        mock_result = Mock()
        mock_result.stdout = b"binary data".decode("latin-1")
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("cat binary_file")

        assert success is True
        assert "binary data" in output.stdout

    @patch("subprocess.run")
    def test_run_shell_command_special_characters(self, mock_run):
        """Test command execution with special characters."""
        # Mock command with special characters
        mock_result = Mock()
        mock_result.stdout = "path/to/file with spaces\n"
        mock_result.stderr = "warning: 'special' \"quotes\"\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        success, output = connector.run_shell_command("ls 'path with spaces'")

        assert success is True
        assert "path/to/file with spaces" in output.stdout
        assert "warning: 'special' \"quotes\"" in output.stderr
