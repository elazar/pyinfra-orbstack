"""
Consolidated VM Lifecycle Tests for PyInfra OrbStack.

This module consolidates the overlapping VM lifecycle tests from:
- test_vm_operations_integration.py::test_vm_lifecycle_integration
- test_end_to_end.py::test_vm_lifecycle_end_to_end
- test_end_to_end.py::test_vm_lifecycle_operations

Provides comprehensive VM lifecycle testing with proper validation and cleanup.
"""

import json
import subprocess
import time
from unittest import TestCase

from tests.test_utils import (
    create_vm_with_retry,
    delete_vm_with_retry,
    start_vm_with_retry,
    stop_vm_with_retry,
)


class TestVMLifecycleConsolidated(TestCase):
    """Consolidated VM lifecycle tests using direct orbctl commands."""

    def setUp(self):
        """Set up test environment."""
        self.test_vm_name = f"consolidated-test-vm-{int(time.time())}"
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

    def test_comprehensive_vm_lifecycle(self):
        """Test comprehensive VM lifecycle operations."""
        # Create VM with resilient function
        assert create_vm_with_retry(
            self.test_image, self.test_vm_name
        ), "VM creation failed"

        # Start VM
        assert start_vm_with_retry(self.test_vm_name), "VM start failed"

        # Wait for VM to be ready
        time.sleep(5)

        # Get VM info
        info_result = subprocess.run(
            ["orbctl", "info", self.test_vm_name, "-f", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert info_result.returncode == 0, "VM info retrieval failed"

        vm_info = json.loads(info_result.stdout)
        assert (
            vm_info.get("record", {}).get("state") == "running"
        ), "VM should be running"

        # Stop VM
        assert stop_vm_with_retry(self.test_vm_name), "VM stop failed"

        # Verify VM is stopped
        info_result = subprocess.run(
            ["orbctl", "info", self.test_vm_name, "-f", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert info_result.returncode == 0, "VM info retrieval failed"

        vm_info = json.loads(info_result.stdout)
        assert (
            vm_info.get("record", {}).get("state") == "stopped"
        ), "VM should be stopped"

        # Delete VM
        assert delete_vm_with_retry(self.test_vm_name), "VM deletion failed"

        # Verify VM is deleted
        list_result = subprocess.run(
            ["orbctl", "list", "-f", "json"], capture_output=True, text=True, timeout=30
        )
        assert list_result.returncode == 0, "VM listing failed"

        vms = json.loads(list_result.stdout)
        vm_names = [vm.get("name") for vm in vms]
        assert self.test_vm_name not in vm_names, "VM should be deleted"

    def test_vm_lifecycle_with_parameters(self):
        """Test VM lifecycle with different parameters."""
        # Test VM creation with architecture specification
        arm64_vm_name = f"{self.test_vm_name}-arm64"
        assert create_vm_with_retry(
            self.test_image, arm64_vm_name, arch="arm64"
        ), "ARM64 VM creation failed"

        # Test basic lifecycle for ARM64 VM
        assert start_vm_with_retry(arm64_vm_name), "ARM64 VM start failed"
        time.sleep(5)
        assert stop_vm_with_retry(arm64_vm_name), "ARM64 VM stop failed"

        # Clean up
        assert delete_vm_with_retry(arm64_vm_name), "ARM64 VM deletion failed"

        # Test VM creation with user specification
        user_vm_name = f"{self.test_vm_name}-user"
        assert create_vm_with_retry(
            self.test_image, user_vm_name, user="ubuntu"
        ), "User VM creation failed"

        # Test basic lifecycle for user VM
        assert start_vm_with_retry(user_vm_name), "User VM start failed"
        time.sleep(5)
        assert stop_vm_with_retry(user_vm_name), "User VM stop failed"

        # Clean up
        assert delete_vm_with_retry(user_vm_name), "User VM deletion failed"
