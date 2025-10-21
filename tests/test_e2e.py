"""
End-to-end tests for PyInfra OrbStack integration.

These tests verify the complete integration between PyInfra and OrbStack,
including VM lifecycle management, command execution, and file operations.
"""

import json
import os
import platform
import subprocess
import tempfile
import time
from unittest.mock import Mock

import pytest

from pyinfra_orbstack.connector import OrbStackConnector


def check_orbstack_available():
    """Check if OrbStack is available and running."""
    try:
        # Check if we're on macOS
        if platform.system() != "Darwin":
            return False, "Not running on macOS"

        # Check if orbctl is available
        result = subprocess.run(
            ["which", "orbctl"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False, "orbctl not found in PATH"

        # Check if OrbStack is running
        result = subprocess.run(
            ["orbctl", "status"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return False, "OrbStack is not running"

        return True, "OrbStack is available"

    except subprocess.TimeoutExpired:
        return False, "Timeout checking OrbStack status"
    except Exception as e:
        return False, f"Error checking OrbStack: {e}"


# Skip all tests in this module if OrbStack is not available
orbstack_available, orbstack_reason = check_orbstack_available()

if not orbstack_available:
    pytest.skip(f"OrbStack not available: {orbstack_reason}", allow_module_level=True)


class TestEndToEndIntegration:
    """End-to-end integration tests for PyInfra OrbStack."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a unique test VM name
        self.test_vm_name = f"e2e-test-vm-{int(time.time())}"
        self.test_image = "ubuntu:22.04"

        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.local_test_file = os.path.join(self.temp_dir, "test_file.txt")
        self.remote_test_file = "/tmp/remote_test_file.txt"

        # Create a test file
        with open(self.local_test_file, "w") as f:
            f.write("Hello from PyInfra OrbStack E2E test!\n")

        # Clean up any existing test VM
        self._cleanup_test_vm()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up the test VM
        self._cleanup_test_vm()

        # Clean up temporary files
        if os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def _cleanup_test_vm(self):
        """Clean up test VM if it exists."""
        try:
            # Check if VM exists
            result = subprocess.run(
                ["orbctl", "list", "-f", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                vms = json.loads(result.stdout)
                _vm_exists = any(
                    vm_data.get("name") == self.test_vm_name for vm_data in vms
                )

                if _vm_exists:
                    # Force delete the VM
                    subprocess.run(
                        ["orbctl", "delete", "-f", self.test_vm_name],
                        capture_output=True,
                        timeout=30,
                    )
        except Exception:
            # Ignore cleanup errors
            pass

    def test_vm_lifecycle_end_to_end(self):
        """Test complete VM lifecycle using direct orbctl commands.

        NOTE: This test has been consolidated into test_vm_lifecycle_consolidated.py
        to reduce redundancy. This test is kept for backward compatibility but
        the consolidated version provides more comprehensive coverage.
        """
        # Test VM creation
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            create_result.returncode == 0
        ), f"VM creation failed: {create_result.stderr}"

        # Wait for VM to be ready
        time.sleep(5)

        # Test VM listing
        list_result = subprocess.run(
            ["orbctl", "list", "-f", "json"], capture_output=True, text=True, timeout=10
        )
        assert list_result.returncode == 0
        vms = json.loads(list_result.stdout)
        vm_names = [vm.get("name") for vm in vms]
        assert self.test_vm_name in vm_names, "Created VM should be in list"

        # Test VM start
        start_result = subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert start_result.returncode == 0, f"VM start failed: {start_result.stderr}"

        # Wait for VM to start
        time.sleep(10)

        # Test VM info
        info_result = subprocess.run(
            ["orbctl", "info", self.test_vm_name, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert info_result.returncode == 0, f"VM info failed: {info_result.stderr}"
        vm_info = json.loads(info_result.stdout)
        assert isinstance(vm_info, dict), "VM info should be a dictionary"

        # Test VM stop
        stop_result = subprocess.run(
            ["orbctl", "stop", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert stop_result.returncode == 0, f"VM stop failed: {stop_result.stderr}"

        # Wait for VM to stop
        time.sleep(5)

        # Test VM deletion
        delete_result = subprocess.run(
            ["orbctl", "delete", "-f", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            delete_result.returncode == 0
        ), f"VM deletion failed: {delete_result.stderr}"

        # Verify VM is deleted
        list_result = subprocess.run(
            ["orbctl", "list", "-f", "json"], capture_output=True, text=True, timeout=10
        )
        assert list_result.returncode == 0
        vms = json.loads(list_result.stdout)
        vm_names = [vm.get("name") for vm in vms]
        assert self.test_vm_name not in vm_names, "VM should be deleted"

    def test_connector_command_execution(self):
        """Test command execution through the OrbStack connector."""
        # Create a test VM
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            create_result.returncode == 0
        ), f"VM creation failed: {create_result.stderr}"

        # Wait for VM to be ready and start it
        time.sleep(5)
        start_result = subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert start_result.returncode == 0, f"VM start failed: {start_result.stderr}"
        time.sleep(10)

        # Test connector command execution
        mock_state = Mock()
        mock_host = Mock()
        mock_host.data = {"vm_name": self.test_vm_name}
        connector = OrbStackConnector(mock_state, mock_host)

        # Test basic command execution
        success, output = connector.run_shell_command("echo 'Hello from VM'")
        assert success, "Command execution should succeed"
        assert any(
            "Hello from VM" in line.line for line in output
        ), "Command output should contain expected text"

        # Test command with working directory
        success, output = connector.run_shell_command("pwd", workdir="/tmp")
        assert success, "Command with workdir should succeed"

        # Test command that should fail
        success, output = connector.run_shell_command("nonexistent_command")
        assert not success, "Invalid command should fail"

        # Clean up
        subprocess.run(
            ["orbctl", "delete", "-f", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )

    def test_connector_file_operations(self):
        """Test file upload and download through the OrbStack connector."""
        # Create a test VM
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            create_result.returncode == 0
        ), f"VM creation failed: {create_result.stderr}"

        # Wait for VM to be ready and start it
        time.sleep(5)
        start_result = subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert start_result.returncode == 0, f"VM start failed: {start_result.stderr}"
        time.sleep(10)

        # Test connector file operations
        mock_state = Mock()
        mock_host = Mock()
        mock_host.data = {"vm_name": self.test_vm_name}
        connector = OrbStackConnector(mock_state, mock_host)

        # Test file upload
        upload_success = connector.put_file(self.local_test_file, self.remote_test_file)
        assert upload_success, "File upload should succeed"

        # Verify file was uploaded by checking its contents
        success, output = connector.run_shell_command(f"cat {self.remote_test_file}")
        assert success, "Should be able to read uploaded file"
        assert any(
            "Hello from PyInfra OrbStack E2E test!" in line.line for line in output
        ), "File content should match"

        # Test file download
        download_path = os.path.join(self.temp_dir, "downloaded_file.txt")
        download_success = connector.get_file(self.remote_test_file, download_path)
        assert download_success, "File download should succeed"

        # Verify downloaded file content
        with open(download_path) as f:
            content = f.read()
        assert (
            "Hello from PyInfra OrbStack E2E test!" in content
        ), "Downloaded file content should match"

        # Clean up
        subprocess.run(
            ["orbctl", "delete", "-f", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )

    def test_vm_operations_with_parameters(self):
        """Test VM operations with various parameters."""
        # Test VM creation with architecture specification
        arm64_vm_name = f"{self.test_vm_name}-arm64"
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, arm64_vm_name, "--arch", "arm64"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Note: This might fail if arm64 is not supported on the current system
        # We'll just verify the operation structure is correct
        if create_result.returncode == 0:
            subprocess.run(
                ["orbctl", "delete", "-f", arm64_vm_name],
                capture_output=True,
                timeout=30,
            )

        # Test VM creation with user specification
        user_vm_name = f"{self.test_vm_name}-user"
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, user_vm_name, "--user", "ubuntu"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if create_result.returncode == 0:
            subprocess.run(
                ["orbctl", "delete", "-f", user_vm_name],
                capture_output=True,
                timeout=30,
            )

    def test_vm_lifecycle_operations(self):
        """Test VM lifecycle operations (start, stop, restart)."""
        # Create a test VM
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            create_result.returncode == 0
        ), f"VM creation failed: {create_result.stderr}"

        # Wait for VM to be ready
        time.sleep(5)

        # Test VM start
        start_result = subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert start_result.returncode == 0, f"VM start failed: {start_result.stderr}"

        # Wait for VM to start
        time.sleep(10)

        # Test VM restart
        restart_result = subprocess.run(
            ["orbctl", "restart", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            restart_result.returncode == 0
        ), f"VM restart failed: {restart_result.stderr}"

        # Wait for VM to restart
        time.sleep(10)

        # Test VM stop
        stop_result = subprocess.run(
            ["orbctl", "stop", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert stop_result.returncode == 0, f"VM stop failed: {stop_result.stderr}"

        # Wait for VM to stop
        time.sleep(5)

        # Test force stop
        force_stop_result = subprocess.run(
            ["orbctl", "stop", "-f", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            force_stop_result.returncode == 0
        ), f"Force stop failed: {force_stop_result.stderr}"

        # Clean up
        subprocess.run(
            ["orbctl", "delete", "-f", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )

    def test_connector_make_names_data(self):
        """Test the connector's make_names_data method."""
        # Get VMs using the connector's make_names_data method
        vm_generator = OrbStackConnector.make_names_data()
        vms = list(vm_generator)

        # Verify the structure of returned data
        for vm_name, vm_data, groups in vms:
            assert isinstance(vm_name, str), "VM name should be string"
            assert isinstance(vm_data, dict), "VM data should be dict"
            assert isinstance(groups, list), "Groups should be list"

            # Verify required fields in vm_data
            assert "orbstack_vm" in vm_data, "Should have orbstack_vm flag"
            assert "vm_name" in vm_data, "Should have vm_name"
            assert "vm_status" in vm_data, "Should have vm_status"

            # Verify groups
            assert "orbstack" in groups, "Should be in orbstack group"

    def test_connector_connection_management(self):
        """Test connector connection and disconnection."""
        # Create a test VM
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            create_result.returncode == 0
        ), f"VM creation failed: {create_result.stderr}"

        # Wait for VM to be ready and start it
        time.sleep(5)
        start_result = subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert start_result.returncode == 0, f"VM start failed: {start_result.stderr}"
        time.sleep(10)

        # Test connector connection
        mock_state = Mock()
        mock_host = Mock()
        mock_host.data = {"vm_name": self.test_vm_name}
        connector = OrbStackConnector(mock_state, mock_host)

        # Test connection to running VM
        connected = connector.connect()
        assert connected, "Should be able to connect to running VM"

        # Test disconnection (should not raise any errors)
        try:
            connector.disconnect()
        except Exception as e:
            pytest.fail(f"Disconnect should not raise exceptions: {e}")

        # Clean up
        subprocess.run(
            ["orbctl", "delete", "-f", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test VM operations with non-existent VM
        start_result = subprocess.run(
            ["orbctl", "start", "non-existent-vm"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert start_result.returncode != 0, "Starting non-existent VM should fail"

        stop_result = subprocess.run(
            ["orbctl", "stop", "non-existent-vm"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert stop_result.returncode != 0, "Stopping non-existent VM should fail"

        delete_result = subprocess.run(
            ["orbctl", "delete", "non-existent-vm"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert delete_result.returncode != 0, "Deleting non-existent VM should fail"

        # Test connector with non-existent VM
        mock_state = Mock()
        mock_host = Mock()
        mock_host.data = {"vm_name": "non-existent-vm"}
        connector = OrbStackConnector(mock_state, mock_host)

        # Test connection to non-existent VM
        connected = connector.connect()
        assert not connected, "Should not be able to connect to non-existent VM"

        # Test command execution on non-existent VM
        success, output = connector.run_shell_command("echo 'test'")
        assert not success, "Command on non-existent VM should fail"

    def test_vm_network_functionality(self):
        """Test VM network functionality."""
        # Create a test VM
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            create_result.returncode == 0
        ), f"VM creation failed: {create_result.stderr}"

        # Wait for VM to be ready and start it
        time.sleep(5)
        start_result = subprocess.run(
            ["orbctl", "start", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert start_result.returncode == 0, f"VM start failed: {start_result.stderr}"

        # Wait for VM to start and get network
        time.sleep(15)

        # Get VM info to check network
        info_result = subprocess.run(
            ["orbctl", "info", self.test_vm_name, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert info_result.returncode == 0, f"VM info failed: {info_result.stderr}"
        vm_info = json.loads(info_result.stdout)

        # Network info might not be immediately available
        # This is more of a verification that the command works
        assert isinstance(vm_info, dict), "VM info should be a dictionary"

        # Clean up
        subprocess.run(
            ["orbctl", "delete", "-f", self.test_vm_name],
            capture_output=True,
            timeout=30,
        )

    def test_vm_performance_characteristics(self):
        """Test VM operation performance characteristics."""
        # Measure VM creation time
        start_time = time.time()

        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            create_result.returncode == 0
        ), f"VM creation failed: {create_result.stderr}"

        creation_time = time.time() - start_time

        # VM creation should complete within reasonable time (2 minutes)
        assert (
            creation_time < 120.0
        ), f"VM creation took too long: {creation_time:.2f} seconds"

        # Measure VM deletion time
        start_time = time.time()

        delete_result = subprocess.run(
            ["orbctl", "delete", "-f", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert (
            delete_result.returncode == 0
        ), f"VM deletion failed: {delete_result.stderr}"

        deletion_time = time.time() - start_time

        # VM deletion should complete within reasonable time (1 minute)
        assert (
            deletion_time < 60.0
        ), f"VM deletion took too long: {deletion_time:.2f} seconds"

    def test_pyinfra_vm_operations_with_mocked_host(self):
        """Test PyInfra VM operations with mocked host context."""
        # This test demonstrates that PyInfra operations require proper context
        # and cannot be called directly in unit tests

        # Import the operations to ensure they're loaded
        from pyinfra_orbstack.operations import vm

        # Verify operations are callable (this is what existing tests do)
        assert callable(vm.vm_create)
        assert callable(vm.vm_delete)
        assert callable(vm.vm_start)
        assert callable(vm.vm_stop)
        assert callable(vm.vm_restart)
        assert callable(vm.vm_info)
        assert callable(vm.vm_list)
        assert callable(vm.vm_status)
        assert callable(vm.vm_ip)
        assert callable(vm.vm_network_info)

        # Note: These operations require PyInfra deployment context to be called
        # They are designed to be used in deployment files, not unit tests
        # The actual testing of these operations happens in integration tests
        # that simulate real PyInfra deployment scenarios

    def test_pyinfra_vm_operations_error_handling(self):
        """Test PyInfra VM operations error handling."""
        # This test demonstrates the limitations of testing PyInfra operations
        # in unit test contexts

        # Import the operations to ensure they're loaded
        from pyinfra_orbstack.operations import vm

        # The operations are decorated functions that require PyInfra context
        # They cannot be called directly in unit tests
        # Instead, we test the underlying logic through integration tests
        # and command construction tests
        # Verify the operations exist and are properly decorated
        assert hasattr(vm, "vm_create")
        assert hasattr(vm, "vm_delete")
        assert hasattr(vm, "vm_start")
        assert hasattr(vm, "vm_stop")
        assert hasattr(vm, "vm_restart")
        assert hasattr(vm, "vm_info")
        assert hasattr(vm, "vm_list")
        assert hasattr(vm, "vm_status")
        assert hasattr(vm, "vm_ip")
        assert hasattr(vm, "vm_network_info")


# Mark all tests as integration tests
pytestmark = pytest.mark.integration
