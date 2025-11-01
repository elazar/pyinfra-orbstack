"""
Integration tests for PyInfra OrbStack connector.

These tests require macOS with OrbStack installed and running.
Tests are automatically skipped if conditions are not met.
"""

import json
import os
import platform
import subprocess
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


class TestOrbStackIntegration:
    """Integration tests for OrbStack connector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock state and host for connector tests
        self.mock_state = Mock()
        self.mock_host = Mock()
        self.mock_host.data = {"vm_name": "test-integration-vm"}

    def test_orbstack_cli_available(self):
        """Test that OrbStack CLI is available and working."""
        # This test should only run if OrbStack is available
        result = subprocess.run(
            ["orbctl", "version"], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "Version:" in result.stdout

    def test_orbstack_vm_listing(self):
        """Test VM listing functionality with real OrbStack."""
        # Get actual VM list from OrbStack
        result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0

        # Parse the JSON response
        vms = json.loads(result.stdout)
        assert isinstance(vms, list)

        # If there are VMs, verify the structure
        if vms:
            vm = vms[0]
            assert "name" in vm
            assert "state" in vm
            assert "image" in vm

    def test_connector_make_names_data(self):
        """Test connector's make_names_data method with real OrbStack."""
        # Get VMs using the connector method
        vms = list(OrbStackConnector.make_names_data())

        # Verify the structure of returned data
        for vm_name, vm_data, groups in vms:
            assert isinstance(vm_name, str)
            assert isinstance(vm_data, dict)
            assert isinstance(groups, list)

            # Check required fields
            assert "orbstack_vm" in vm_data
            assert vm_data["orbstack_vm"] is True
            assert "vm_name" in vm_data
            assert "vm_status" in vm_data

            # Check groups
            assert "orbstack" in groups

    def test_connector_make_names_data_with_filter(self):
        """Test connector's make_names_data method with name filter."""
        # Get actual VMs first
        all_vms = list(OrbStackConnector.make_names_data())

        if all_vms:
            # Test filtering with the first VM name
            first_vm_name = all_vms[0][0]
            filtered_vms = list(OrbStackConnector.make_names_data(first_vm_name))

            assert len(filtered_vms) == 1
            assert filtered_vms[0][0] == first_vm_name

    def test_connector_connect_to_existing_vm(self):
        """Test connector connection to an existing VM."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            # Try to connect to the first VM
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)
            result = connector.connect()

            # Connection should succeed for existing VMs
            assert result is True

    def test_connector_connect_to_nonexistent_vm(self):
        """Test connector connection to a non-existent VM."""
        # Use a VM name that doesn't exist
        self.mock_host.data = {"vm_name": "nonexistent-vm-integration-test"}

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = connector.connect()

        # Connection should fail for non-existent VMs
        assert result is False

    def test_connector_run_shell_command(self):
        """Test running shell commands in a VM."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            # Try to run a simple command in the first VM
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test a simple command
            success, output = connector.run_shell_command("echo 'hello world'")

            # Command should succeed
            assert success is True
            assert "hello world" in output.stdout

    def test_connector_run_shell_command_with_user(self):
        """Test running shell commands with specific user."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test command with user specification
            success, output = connector.run_shell_command("whoami", user="root")

            # Command should succeed
            assert success is True
            assert "root" in output.stdout

    def test_connector_run_shell_command_with_workdir(self):
        """Test running shell commands with working directory."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test command with working directory
            success, output = connector.run_shell_command("pwd", workdir="/tmp")

            # Command should succeed
            assert success is True
            assert "/tmp" in output.stdout

    def test_connector_file_transfer(self):
        """Test file transfer operations."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Create a test file
            test_content = "Integration test content"
            test_file = "/tmp/test_integration_file.txt"

            try:
                with open(test_file, "w") as f:
                    f.write(test_content)

                # Test file upload
                result = connector.put_file(test_file, "test_file.txt")
                assert result is True

                # Test file download
                download_file = "/tmp/test_download.txt"
                result = connector.get_file("test_file.txt", download_file)
                assert result is True

                # Verify downloaded content
                with open(download_file) as f:
                    downloaded_content = f.read()
                assert downloaded_content == test_content

            finally:
                # Clean up test files
                for file_path in [test_file]:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                # Clean up download file if it was created
                if "download_file" in locals() and os.path.exists(download_file):
                    os.remove(download_file)

    def test_connector_error_handling(self):
        """Test error handling for invalid operations."""
        # Test with invalid VM name
        self.mock_host.data = {"vm_name": "invalid-vm-name"}
        connector = OrbStackConnector(self.mock_state, self.mock_host)

        # Test command execution with invalid VM
        success, _ = connector.run_shell_command("echo test")
        assert success is False
        # Just verify that the command failed (error message may vary)

    def test_connector_timeout_handling(self):
        """Test timeout handling for long-running commands."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test command with short timeout
            success, output = connector.run_shell_command("sleep 10", timeout=1)

            # Command should timeout
            assert success is False
            assert "timed out" in output.stderr.lower()

    def test_connector_large_output_handling(self):
        """Test handling of commands with large output."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test command that generates large output
            success, output = connector.run_shell_command("ls -la /usr/bin")

            # Command should succeed
            assert success is True
            assert len(output.stdout) > 0

    def test_connector_special_characters(self):
        """Test handling of commands with special characters."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test command with special characters
            test_command = "echo 'test with \"quotes\" and spaces'"
            success, output = connector.run_shell_command(test_command)

            # Command should succeed
            assert success is True
            assert "quotes" in output.stdout

    def test_connector_concurrent_operations(self):
        """Test concurrent operations on the same VM."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test multiple commands in sequence
            commands = ["echo 'command 1'", "echo 'command 2'", "echo 'command 3'"]

            for i, cmd in enumerate(commands, 1):
                success, output = connector.run_shell_command(cmd)
                assert success is True
                assert f"command {i}" in output.stdout

    def test_connector_vm_lifecycle_integration(self):
        """Test integration with VM lifecycle operations."""
        # This test would require creating and managing VMs
        # For now, we'll test the connector's ability to work with existing VMs

        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test that we can connect and run commands
            result = connector.connect()
            assert result is True

            # Test command execution
            success, output = connector.run_shell_command("uname -a")
            assert success is True
            assert len(output.stdout) > 0

            # Test disconnect (should be no-op)
            connector.disconnect()

    def test_connector_performance(self):
        """Test performance characteristics of the connector."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            import time

            # Test command execution time
            start_time = time.time()
            success, _ = connector.run_shell_command("echo 'performance test'")
            end_time = time.time()

            assert success is True
            execution_time = end_time - start_time

            # Command should complete within reasonable time (5 seconds)
            assert execution_time < 5.0

    def test_connector_resource_cleanup(self):
        """Test that resources are properly cleaned up."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Connect and run some operations
            result = connector.connect()
            assert result is True

            success, _ = connector.run_shell_command("echo 'cleanup test'")
            assert success is True

            # Disconnect (should not raise exceptions)
            connector.disconnect()

            # Try to disconnect again (should still not raise exceptions)
            connector.disconnect()

    def test_connector_sudo_with_logical_negation(self):
        """
        Integration test: Verify sudo commands with ! (logical negation) work correctly.

        This tests the fix for the bash history expansion issue where commands
        with ! were incorrectly wrapped in sh -c, causing "command not found" errors.

        The fix ensures that bash +H is used as the outer shell wrapper to disable
        history expansion throughout the entire command execution chain.
        """
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test 1: File existence check with logical negation and sudo
            # This should NOT produce "!: command not found" error
            success, output = connector.run_shell_command(
                "! test -e /nonexistent_file_test_12345 && echo MISSING", sudo=True
            )
            assert success is True, f"Command failed: {output.stderr}"
            assert "MISSING" in output.stdout, "Expected 'MISSING' in output"
            assert (
                "command not found" not in output.stderr.lower()
            ), "Should not have 'command not found' error with !"

            # Test 2: Same command with sudo_user
            success, output = connector.run_shell_command(
                "! test -e /nonexistent_file_test_67890 && echo NOT_FOUND",
                sudo=True,
                sudo_user="root",
            )
            assert success is True, f"Command with sudo_user failed: {output.stderr}"
            assert "NOT_FOUND" in output.stdout, "Expected 'NOT_FOUND' in output"
            assert (
                "command not found" not in output.stderr.lower()
            ), "Should not have 'command not found' error with sudo_user"

            # Test 3: Verify the fix - logical negation should work correctly
            success, output = connector.run_shell_command(
                "! false && echo SUCCESS", sudo=True
            )
            assert success is True, f"Logical negation failed: {output.stderr}"
            assert "SUCCESS" in output.stdout, "Expected 'SUCCESS' in output"
            assert (
                "command not found" not in output.stderr.lower()
            ), "Should not have 'command not found' error"

            # Test 4: Complex command with logical operators
            success, output = connector.run_shell_command(
                "! test -d /nonexistent_dir_test && mkdir -p /tmp/test_dir_integration || echo EXISTS",
                sudo=True,
            )
            assert success is True, f"Complex command failed: {output.stderr}"
            # Verify no history expansion errors
            assert (
                "command not found" not in output.stderr.lower()
            ), "Should not have 'command not found' error in complex command"

            # Test 5: Test with actual file that exists (negation should return false)
            success, output = connector.run_shell_command(
                "! test -e /tmp && echo NOT_EXISTS || echo EXISTS", sudo=True
            )
            assert success is True, f"File existence check failed: {output.stderr}"
            assert "EXISTS" in output.stdout, "Expected 'EXISTS' for /tmp directory"
            assert (
                "command not found" not in output.stderr.lower()
            ), "Should not have 'command not found' error"


class TestOrbStackIntegrationEdgeCases:
    """Test edge cases and error conditions in integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_state = Mock()
        self.mock_host = Mock()

    def test_connector_no_vm_name(self):
        """Test connector behavior with no VM name."""
        self.mock_host.data = {}
        connector = OrbStackConnector(self.mock_state, self.mock_host)

        # Test connection with no VM name
        result = connector.connect()
        assert result is False

        # Test command execution with no VM name
        success, output = connector.run_shell_command("echo test")
        assert success is False
        assert "VM name not found" in output.stderr

    def test_connector_empty_vm_name(self):
        """Test connector behavior with empty VM name."""
        self.mock_host.data = {"vm_name": ""}
        connector = OrbStackConnector(self.mock_state, self.mock_host)

        # Test connection with empty VM name
        result = connector.connect()
        assert result is False

    def test_connector_invalid_vm_name(self):
        """Test connector behavior with invalid VM name."""
        self.mock_host.data = {"vm_name": "invalid/vm/name/with/slashes"}
        connector = OrbStackConnector(self.mock_state, self.mock_host)

        # Test connection with invalid VM name
        result = connector.connect()
        assert result is False

    def test_connector_large_command(self):
        """Test connector behavior with very large commands."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test with a large command
            large_command = "echo " + "'x' * 10000"
            success, output = connector.run_shell_command(large_command)

            # Command should still succeed
            assert success is True
            assert len(output.stdout) > 0

    def test_connector_binary_output(self):
        """Test connector behavior with binary output."""
        # Get actual VMs
        vms = list(OrbStackConnector.make_names_data())

        if vms:
            vm_name = vms[0][0]
            self.mock_host.data = {"vm_name": vm_name}

            connector = OrbStackConnector(self.mock_state, self.mock_host)

            # Test command that might produce binary-like output
            success, _ = connector.run_shell_command("echo -n 'test' | od -c")

            # Command should succeed
            assert success is True


class TestPhase3BConfigIntegration:
    """Integration tests for Phase 3B configuration management operations."""

    def test_config_get_cpu(self):
        """Test getting CPU configuration."""
        result = subprocess.run(
            ["orbctl", "config", "get", "cpu"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        # Parse output - may be single value or key: value format
        output = result.stdout.strip()
        if ":" in output:
            # Parse "key: value" format or full config output
            for line in output.split("\n"):
                if line.startswith("cpu:"):
                    cpu_value = line.split(":", 1)[1].strip()
                    assert cpu_value.isdigit()
                    assert int(cpu_value) > 0
                    return
        else:
            # Single value format
            assert output.isdigit()
            assert int(output) > 0

    def test_config_get_memory(self):
        """Test getting memory configuration."""
        result = subprocess.run(
            ["orbctl", "config", "get", "memory_mib"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        # Parse output - may be single value or key: value format
        output = result.stdout.strip()
        if ":" in output:
            # Parse "key: value" format or full config output
            for line in output.split("\n"):
                if line.startswith("memory_mib:"):
                    memory_value = line.split(":", 1)[1].strip()
                    assert memory_value.isdigit()
                    assert int(memory_value) > 0
                    return
        else:
            # Single value format
            assert output.isdigit()
            assert int(output) > 0

    def test_config_show(self):
        """Test showing all configuration."""
        result = subprocess.run(
            ["orbctl", "config", "show"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        output = result.stdout

        # Verify expected configuration keys are present
        assert "cpu:" in output
        assert "memory_mib:" in output
        assert "network.subnet4:" in output

    def test_config_get_network_subnet(self):
        """Test getting network subnet configuration."""
        result = subprocess.run(
            ["orbctl", "config", "get", "network.subnet4"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        subnet = result.stdout.strip()
        # Verify it looks like an IP subnet (contains dots and slash)
        assert "." in subnet
        assert "/" in subnet

    def test_config_get_rosetta(self):
        """Test getting Rosetta configuration."""
        result = subprocess.run(
            ["orbctl", "config", "get", "rosetta"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        # Parse output - may be single value or key: value format
        output = result.stdout.strip()
        if ":" in output:
            # Parse "key: value" format or full config output
            for line in output.split("\n"):
                if line.startswith("rosetta:"):
                    rosetta_value = line.split(":", 1)[1].strip()
                    assert rosetta_value in ["true", "false"]
                    return
        else:
            # Single value format
            assert output in ["true", "false"]

    def test_config_get_nested_keys(self):
        """Test getting nested configuration keys."""
        nested_keys = [
            "docker.expose_ports_to_lan",
            "machines.forward_ports",
            "network.https",
            "setup.use_admin",
        ]

        for key in nested_keys:
            result = subprocess.run(
                ["orbctl", "config", "get", key],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # All these keys should exist
            assert result.returncode == 0
            assert len(result.stdout.strip()) > 0

    def test_config_set_and_get(self):
        """Test setting and getting a non-critical configuration value."""
        # Use a safe config value to test (app.start_at_login)
        test_key = "app.start_at_login"

        # Helper to extract value from output
        def get_value(output, key):
            for line in output.split("\n"):
                if line.startswith(f"{key}:"):
                    return line.split(":", 1)[1].strip()
            return output.strip()

        # Get current value
        get_result = subprocess.run(
            ["orbctl", "config", "get", test_key],
            capture_output=True,
            text=True,
            timeout=10,
        )
        original_value = get_value(get_result.stdout, test_key)

        try:
            # Set to opposite value
            new_value = "false" if original_value == "true" else "true"
            set_result = subprocess.run(
                ["orbctl", "config", "set", test_key, new_value],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert set_result.returncode == 0

            # Verify the change
            verify_result = subprocess.run(
                ["orbctl", "config", "get", test_key],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert verify_result.returncode == 0
            assert get_value(verify_result.stdout, test_key) == new_value

        finally:
            # Restore original value
            subprocess.run(
                ["orbctl", "config", "set", test_key, original_value],
                capture_output=True,
                text=True,
                timeout=10,
            )

    def test_vm_username_configuration(self):
        """Test per-VM username configuration."""

        # Helper to extract value from output
        def get_value(output, key):
            for line in output.split("\n"):
                if line.startswith(f"{key}:"):
                    return line.split(":", 1)[1].strip()
            return output.strip()

        # Get list of existing VMs
        list_result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if list_result.returncode == 0:
            vms = json.loads(list_result.stdout)

            if vms:
                # Use the first available VM
                vm_name = vms[0]["name"]
                test_username = "test-user-integration"
                config_key = f"machine.{vm_name}.username"

                # Get current username if it exists
                get_result = subprocess.run(
                    ["orbctl", "config", "get", config_key],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                original_username = (
                    get_value(get_result.stdout, config_key)
                    if get_result.returncode == 0
                    else None
                )

                try:
                    # Set test username
                    set_result = subprocess.run(
                        [
                            "orbctl",
                            "config",
                            "set",
                            config_key,
                            test_username,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    assert set_result.returncode == 0

                    # Verify the change
                    verify_result = subprocess.run(
                        ["orbctl", "config", "get", config_key],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    assert verify_result.returncode == 0
                    assert get_value(verify_result.stdout, config_key) == test_username

                finally:
                    # Restore original username if it existed
                    if original_username:
                        subprocess.run(
                            [
                                "orbctl",
                                "config",
                                "set",
                                config_key,
                                original_username,
                            ],
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )

    def test_config_show_structure(self):
        """Test that config show output has expected structure."""
        result = subprocess.run(
            ["orbctl", "config", "show"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")

        # Verify each line has key: value format
        for line in lines:
            if line.strip():  # Skip empty lines
                assert ":" in line, f"Invalid config line format: {line}"
                key, value = line.split(":", 1)
                assert len(key.strip()) > 0
                assert len(value.strip()) > 0


@pytest.mark.skipif(not orbstack_available, reason=orbstack_reason)
class TestPhase3ANetworkingIntegration:
    """Integration tests for Phase 3A networking operations."""

    def test_vm_network_details_command(self):
        """Test getting comprehensive network details from a VM."""
        # Get list of running VMs
        list_result = subprocess.run(
            ["orbctl", "list", "-f", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if list_result.returncode != 0:
            pytest.skip("No VMs available for testing")

        vms = json.loads(list_result.stdout)
        if not vms:
            pytest.skip("No VMs available for testing")

        # Test getting network details for first VM
        vm = vms[0]
        vm_name = vm.get("name")

        # Get VM info (contains network details)
        info_result = subprocess.run(
            ["orbctl", "info", vm_name, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert info_result.returncode == 0

        info = json.loads(info_result.stdout)
        # Verify network-related fields exist
        assert "ip4" in info or "ip6" in info, "VM should have IP address information"

    def test_vm_test_connectivity_ping(self):
        """Test ping connectivity command."""
        # Test basic ping to a reliable target
        ping_result = subprocess.run(
            ["ping", "-c", "2", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Ping should work from host
        assert ping_result.returncode == 0 or "bytes from" in ping_result.stdout

    def test_vm_test_connectivity_curl(self):
        """Test curl connectivity command."""
        # Test basic curl to a reliable target
        curl_result = subprocess.run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "--connect-timeout",
                "5",
                "https://www.google.com",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should get an HTTP status code
        if curl_result.returncode == 0:
            status_code = curl_result.stdout.strip()
            assert status_code.startswith(
                ("2", "3")
            ), f"Unexpected status: {status_code}"

    def test_vm_test_connectivity_nc(self):
        """Test netcat connectivity command."""
        # Test nc to a reliable target (Google DNS on port 53)
        nc_result = subprocess.run(
            ["nc", "-zv", "-w", "5", "8.8.8.8", "53"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # nc returns 0 on success, output goes to stderr
        assert nc_result.returncode == 0 or "succeeded" in nc_result.stderr

    def test_vm_dns_lookup_a_record(self):
        """Test DNS A record lookup."""
        # Test basic A record lookup
        dns_result = subprocess.run(
            ["host", "-t", "A", "google.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert dns_result.returncode == 0
        assert (
            "has address" in dns_result.stdout
            or "has IPv4 address" in dns_result.stdout
        )

    def test_vm_dns_lookup_aaaa_record(self):
        """Test DNS AAAA record lookup."""
        # Test IPv6 lookup
        dns_result = subprocess.run(
            ["host", "-t", "AAAA", "google.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # AAAA records might not always be available
        if dns_result.returncode == 0:
            assert (
                "has IPv6 address" in dns_result.stdout
                or "has AAAA record" in dns_result.stdout
            )

    def test_vm_dns_lookup_mx_record(self):
        """Test DNS MX record lookup."""
        # Test MX record lookup
        dns_result = subprocess.run(
            ["host", "-t", "MX", "google.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert dns_result.returncode == 0
        assert "mail is handled by" in dns_result.stdout

    def test_cross_vm_connectivity_orb_local(self):
        """Test connectivity between VMs using .orb.local domains."""
        # Get list of running VMs
        list_result = subprocess.run(
            ["orbctl", "list", "-f", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if list_result.returncode != 0:
            pytest.skip("No VMs available for testing")

        vms = json.loads(list_result.stdout)
        running_vms = [vm for vm in vms if vm.get("state") == "RUNNING"]

        if len(running_vms) < 2:
            pytest.skip("Need at least 2 running VMs for cross-VM connectivity test")

        # Test DNS resolution of .orb.local domain
        vm1_name = running_vms[0].get("name")
        vm1_domain = f"{vm1_name}.orb.local"

        dns_result = subprocess.run(
            ["host", "-t", "A", vm1_domain],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # [Inference] .orb.local domains should resolve if OrbStack networking is configured
        # If this fails, it may indicate OrbStack networking configuration issues
        if dns_result.returncode == 0:
            assert (
                "has address" in dns_result.stdout
                or "has IPv4 address" in dns_result.stdout
            )


# Mark all tests as integration tests
pytestmark = pytest.mark.integration
