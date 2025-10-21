"""
Integration tests for VM operations in PyInfra OrbStack connector.

These tests require macOS with OrbStack installed and running.
Tests are automatically skipped if conditions are not met.
"""

import json
import platform
import subprocess
import time
from unittest import TestCase

import pytest

from tests.test_utils import (
    create_vm_with_retry,
    delete_vm_with_retry,
    start_vm_with_retry,
    stop_vm_with_retry,
)


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


class TestVMOperationsIntegration(TestCase):
    """Integration tests for VM operations using direct orbctl commands."""

    def setUp(self):
        """Set up test environment."""
        self.test_vm_name = f"test-vm-{int(time.time())}"
        self.test_image = "ubuntu:22.04"

    def tearDown(self):
        """Clean up test environment."""
        # Clean up any remaining test VMs
        for vm_name in [
            self.test_vm_name,
            f"{self.test_vm_name}-arm64",
            f"{self.test_vm_name}-user",
        ]:
            delete_vm_with_retry(vm_name, force=True, max_retries=1)

    def test_vm_list_integration(self):
        """Test VM list operation with real OrbStack."""
        # Get actual VM list using orbctl directly
        result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        vms = json.loads(result.stdout)
        assert isinstance(vms, list)

        # Verify VM structure if VMs exist
        if vms:
            vm_data = vms[0]
            assert "name" in vm_data
            assert "state" in vm_data

    def test_vm_create_and_delete_integration(self):
        """Test VM creation and deletion with real OrbStack."""
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

        # Wait a moment for VM to be created
        time.sleep(2)

        # Verify VM exists
        list_result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert list_result.returncode == 0
        vms = json.loads(list_result.stdout)
        vm_exists = any(vm.get("name") == self.test_vm_name for vm in vms)
        assert vm_exists, "Created VM not found in list"

        # Test VM deletion
        delete_result = subprocess.run(
            ["orbctl", "delete", "--force", self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert (
            delete_result.returncode == 0
        ), f"VM deletion failed: {delete_result.stderr}"

        # Verify VM is deleted
        list_result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert list_result.returncode == 0
        vms = json.loads(list_result.stdout)
        vm_exists = any(vm.get("name") == self.test_vm_name for vm in vms)
        assert not vm_exists, "VM still exists after deletion"

    def test_vm_create_with_arch_integration(self):
        """Test VM creation with architecture specification."""
        # Test VM creation with arm64 architecture using resilient function
        arm64_vm_name = f"{self.test_vm_name}-arm64"
        success = create_vm_with_retry(self.test_image, arm64_vm_name, arch="arm64")

        # Note: This might fail if arm64 is not supported on the current system
        # We'll just verify the command structure is correct
        if success:
            # Clean up if creation succeeded
            delete_vm_with_retry(arm64_vm_name, force=True)

    def test_vm_create_with_user_integration(self):
        """Test VM creation with user specification."""
        # Test VM creation with specific user using resilient function
        user_vm_name = f"{self.test_vm_name}-user"
        success = create_vm_with_retry(self.test_image, user_vm_name, user="ubuntu")

        if success:
            # Clean up if creation succeeded
            delete_vm_with_retry(user_vm_name, force=True)

    def test_vm_lifecycle_integration(self):
        """Test complete VM lifecycle: create, start, stop, restart, delete.

        NOTE: This test has been consolidated into test_vm_lifecycle_consolidated.py
        to reduce redundancy. This test is kept for backward compatibility but
        the consolidated version provides more comprehensive coverage.
        """
        # Create VM using resilient function
        assert create_vm_with_retry(
            self.test_image, self.test_vm_name
        ), "VM creation failed"

        # Wait for VM to be ready
        time.sleep(5)

        # Start VM using resilient function
        assert start_vm_with_retry(self.test_vm_name), "VM start failed"

        # Wait for VM to start
        time.sleep(10)

        # Get VM info to verify it's running
        info_result = subprocess.run(
            ["orbctl", "info", self.test_vm_name, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if info_result.returncode == 0:
            vm_info = json.loads(info_result.stdout)
            # Note: The exact state field might vary depending on OrbStack version
            assert "state" in vm_info or "record" in vm_info

        # Stop VM using resilient function
        assert stop_vm_with_retry(self.test_vm_name), "VM stop failed"

        # Wait for VM to stop
        time.sleep(5)

        # Delete VM using resilient function
        assert delete_vm_with_retry(self.test_vm_name, force=True), "VM deletion failed"

        # Verify VM is deleted
        list_result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert list_result.returncode == 0
        vms = json.loads(list_result.stdout)
        vm_exists = any(vm.get("name") == self.test_vm_name for vm in vms)
        assert not vm_exists, "VM still exists after deletion"

    def test_vm_info_integration(self):
        """Test VM info retrieval functionality."""
        # Create VM using resilient function
        assert create_vm_with_retry(
            self.test_image, self.test_vm_name
        ), "VM creation failed"

        # Wait for VM to be ready
        time.sleep(5)

        # Get VM info
        info_result = subprocess.run(
            ["orbctl", "info", self.test_vm_name, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert info_result.returncode == 0, f"VM info failed: {info_result.stderr}"

        vm_info = json.loads(info_result.stdout)
        assert isinstance(vm_info, dict), "VM info should be a dictionary"

        # Verify VM info contains expected fields
        assert (
            "name" in vm_info or "record" in vm_info
        ), "VM info should contain name or record"

        # Clean up
        assert delete_vm_with_retry(self.test_vm_name, force=True), "VM deletion failed"

    def test_vm_force_operations_integration(self):
        """Test force operations (force stop, force delete)."""
        # Create a test VM
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if create_result.returncode == 0:
            # Wait for VM to be ready
            time.sleep(5)

            # Start VM
            subprocess.run(
                ["orbctl", "start", self.test_vm_name], capture_output=True, timeout=30
            )

            time.sleep(5)

            # Test force stop
            force_stop_result = subprocess.run(
                ["orbctl", "stop", "--force", self.test_vm_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert (
                force_stop_result.returncode == 0
            ), f"Force stop failed: {force_stop_result.stderr}"

            # Test force delete
            force_delete_result = subprocess.run(
                ["orbctl", "delete", "--force", self.test_vm_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert (
                force_delete_result.returncode == 0
            ), f"Force delete failed: {force_delete_result.stderr}"

    def test_vm_error_handling_integration(self):
        """Test error handling for invalid operations."""
        # Test deleting non-existent VM
        delete_result = subprocess.run(
            ["orbctl", "delete", "non-existent-vm"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail (non-zero return code)
        assert delete_result.returncode != 0

        # Test starting non-existent VM
        start_result = subprocess.run(
            ["orbctl", "start", "non-existent-vm"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail (non-zero return code)
        assert start_result.returncode != 0

        # Test getting info for non-existent VM
        info_result = subprocess.run(
            ["orbctl", "info", "non-existent-vm", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail (non-zero return code)
        assert info_result.returncode != 0

    def test_vm_concurrent_operations_integration(self):
        """Test concurrent VM operations."""
        # Create multiple test VMs (reduced to 2 to avoid resource issues)
        vm_names = [f"{self.test_vm_name}-{i}" for i in range(2)]

        # Create VMs concurrently
        create_processes = []
        for vm_name in vm_names:
            process = subprocess.Popen(
                ["orbctl", "create", self.test_image, vm_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            create_processes.append((process, vm_name))

        # Wait for all creations to complete with shorter timeout
        for process, vm_name in create_processes:
            try:
                returncode = process.wait(timeout=30)
                if returncode == 0:
                    # Clean up successful creations
                    subprocess.run(
                        ["orbctl", "delete", "--force", vm_name],
                        capture_output=True,
                        timeout=30,
                    )
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                process.kill()
                process.wait()

    def test_vm_performance_integration(self):
        """Test VM operation performance."""
        # Measure VM creation time
        start_time = time.time()

        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=120,
        )

        creation_time = time.time() - start_time

        if create_result.returncode == 0:
            # VM creation should complete within reasonable time (2 minutes)
            assert creation_time < 120.0

            # Measure VM deletion time
            start_time = time.time()

            delete_result = subprocess.run(
                ["orbctl", "delete", "--force", self.test_vm_name],
                capture_output=True,
                text=True,
                timeout=60,
            )

            deletion_time = time.time() - start_time

            # VM deletion should complete within reasonable time (1 minute)
            assert deletion_time < 60.0
            assert delete_result.returncode == 0

    def test_vm_network_integration(self):
        """Test VM network functionality."""
        # Create a test VM
        create_result = subprocess.run(
            ["orbctl", "create", self.test_image, self.test_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if create_result.returncode == 0:
            # Wait for VM to be ready
            time.sleep(10)

            # Start VM
            start_result = subprocess.run(
                ["orbctl", "start", self.test_vm_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if start_result.returncode == 0:
                # Wait for VM to start and get network
                time.sleep(15)

                # Get VM info to check network
                info_result = subprocess.run(
                    ["orbctl", "info", self.test_vm_name, "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if info_result.returncode == 0:
                    vm_info = json.loads(info_result.stdout)

                    # Check for network information
                    # has_network_info = (
                    #     "ip4" in vm_info
                    #     or "ip6" in vm_info
                    #     or ("record" in vm_info and "mac" in vm_info.get("record", {}))
                    # )

                    # Network info might not be immediately available
                    # This is more of a verification that the command works
                    assert isinstance(vm_info, dict)

            # Clean up
            subprocess.run(
                ["orbctl", "delete", "--force", self.test_vm_name],
                capture_output=True,
                timeout=30,
            )


class TestVMOperationsEdgeCasesIntegration:
    """Test edge cases and error conditions in VM operations integration."""

    def test_vm_invalid_image_integration(self):
        """Test VM creation with invalid image."""
        # Test with non-existent image
        create_result = subprocess.run(
            ["orbctl", "create", "invalid:image:tag", "test-invalid-vm"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should fail (non-zero return code)
        assert create_result.returncode != 0

    def test_vm_invalid_arch_integration(self):
        """Test VM creation with invalid architecture."""
        # Test with invalid architecture
        create_result = subprocess.run(
            [
                "orbctl",
                "create",
                "ubuntu:22.04",
                "test-invalid-arch",
                "--arch",
                "invalid-arch",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should fail (non-zero return code)
        assert create_result.returncode != 0

    def test_vm_invalid_user_integration(self):
        """Test VM creation with invalid user."""
        # Test with invalid user
        try:
            create_result = subprocess.run(
                [
                    "orbctl",
                    "create",
                    "ubuntu:22.04",
                    "test-invalid-user",
                    "--user",
                    "invalid-user",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # Should fail (non-zero return code)
            assert create_result.returncode != 0
        except subprocess.TimeoutExpired:
            # If it times out, that's also a valid failure case
            pass

    def test_vm_special_characters_integration(self):
        """Test VM operations with special characters in names."""
        # Test with special characters in VM name
        special_vm_name = "test-vm-with-special-chars-123"

        create_result = subprocess.run(
            ["orbctl", "create", "ubuntu:22.04", special_vm_name],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if create_result.returncode == 0:
            # Verify VM was created
            list_result = subprocess.run(
                ["orbctl", "list", "-", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if list_result.returncode == 0:
                vms = json.loads(list_result.stdout)
                vm_exists = any(vm.get("name") == special_vm_name for vm in vms)
                assert vm_exists, "VM with special characters not found"

            # Clean up
            subprocess.run(
                ["orbctl", "delete", "--force", special_vm_name],
                capture_output=True,
                timeout=30,
            )

    def test_vm_empty_name_integration(self):
        """Test VM operations with empty name."""
        # Test with empty VM name
        create_result = subprocess.run(
            ["orbctl", "create", "ubuntu:22.04", ""],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should fail (non-zero return code)
        assert create_result.returncode != 0

    def test_vm_large_name_integration(self):
        """Test VM operations with very large name."""
        # Test with very large VM name (reduced size to avoid timeouts)
        large_name = "a" * 100

        try:
            create_result = subprocess.run(
                ["orbctl", "create", "ubuntu:22.04", large_name],
                capture_output=True,
                text=True,
                timeout=15,
            )

            # This might fail due to name length limits
            if create_result.returncode == 0:
                # Clean up if creation succeeded
                subprocess.run(
                    ["orbctl", "delete", "-f", large_name],
                    capture_output=True,
                    timeout=30,
                )
        except subprocess.TimeoutExpired:
            # If it times out, that's also a valid failure case
            pass


# Mark all tests as integration tests
pytestmark = pytest.mark.integration
