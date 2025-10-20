"""
End-to-End Tests for Connector Coverage Gaps

This module contains tests specifically designed to cover the missing lines
in the connector module through end-to-end testing scenarios.
"""

import subprocess
from unittest import TestCase
from unittest.mock import Mock, patch

from pyinfra_orbstack.connector import OrbStackConnector


class TestConnectorCoverageE2E(TestCase):
    """End-to-end tests to cover missing lines in connector module."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_state = Mock()
        self.mock_host = Mock()
        self.mock_host.data = {"vm_name": "test-vm"}
        self.connector = OrbStackConnector(self.mock_state, self.mock_host)

    def test_network_operation_detection(self):
        """Test network operation detection logic (Line 65)."""
        # Test commands that should be detected as network operations
        network_commands = [
            "apt update",
            "yum install package",
            "dnf install package",
            "wget https://example.com",
            "curl https://example.com",
            "create vm",
            "download image",
            "pull container",
        ]

        for cmd in network_commands:
            with patch.object(self.connector, "_execute_with_retry") as mock_execute:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "success"
                mock_result.stderr = ""
                mock_execute.return_value = mock_result

                # This should trigger network operation detection
                self.connector.run_shell_command(cmd)

                # Verify _execute_with_retry was called with is_network_operation=True
                mock_execute.assert_called()
                call_kwargs = mock_execute.call_args.kwargs
                assert (
                    call_kwargs.get("is_network_operation") is True
                ), f"Command '{cmd}' should be detected as network operation"

    def test_network_error_retry_logic(self):
        """Test network error retry logic (Lines 85-91)."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            # Mock network error response
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "network timeout"
            mock_execute.return_value = mock_result

            # This should trigger the retry logic
            success, output = self.connector.run_shell_command("apt update")

            assert not success
            # Verify the retry logic was triggered (network operation detection)
            mock_execute.assert_called()
            call_args = mock_execute.call_args
            assert call_args.kwargs.get("is_network_operation") is True

    def test_make_names_data_error_handling(self):
        """Test error handling in make_names_data (Line 102)."""
        with patch("subprocess.run") as mock_run:
            # Mock subprocess error to trigger error handling
            mock_run.side_effect = subprocess.CalledProcessError(1, ["orbctl", "list"])

            # This should trigger the error handling path
            result = list(OrbStackConnector.make_names_data())

            # Should handle error gracefully and return empty list
            assert result == []

    def test_make_names_data_json_error(self):
        """Test JSON decode error handling in make_names_data."""
        with patch("subprocess.run") as mock_run:
            # Mock successful subprocess but invalid JSON
            mock_result = Mock()
            mock_result.stdout = "invalid json"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # This should trigger JSON decode error handling
            result = list(OrbStackConnector.make_names_data())

            # Should handle error gracefully and return empty list
            assert result == []

    def test_execute_with_retry_max_retries_exceeded(self):
        """Test max retries exceeded scenario (Line 152)."""
        with patch("subprocess.run") as mock_run:
            # Mock subprocess to always fail with network error
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "network timeout"
            mock_run.return_value = mock_result

            # Test with max_retries=1 to trigger max retries exceeded
            result = self.connector._execute_with_retry(
                ["orbctl", "create", "ubuntu:22.04", "test-vm"],
                max_retries=1,
                is_network_operation=True,
            )

            # Should return failed result after max retries
            assert result.returncode == 1
            assert "network timeout" in result.stderr

    def test_execute_with_retry_unexpected_exception(self):
        """Test unexpected exception handling (Lines 146-147)."""
        with patch("subprocess.run") as mock_run:
            # Mock subprocess to raise unexpected exception
            mock_run.side_effect = ValueError("Unexpected error")

            # This should trigger the exception handling path
            with self.assertRaises(ValueError):
                self.connector._execute_with_retry(
                    ["orbctl", "create", "ubuntu:22.04", "test-vm"], max_retries=1
                )

    def test_run_shell_command_unexpected_exception(self):
        """Test unexpected exception handling in run_shell_command."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            # Mock _execute_with_retry to raise unexpected exception
            mock_execute.side_effect = RuntimeError("Unexpected runtime error")

            success, output = self.connector.run_shell_command("echo hello")

            assert not success
            assert "Unexpected error" in str(output)
            assert "Unexpected runtime error" in str(output)

    def test_network_operation_timeout_retry(self):
        """Test timeout retry logic for network operations."""
        with patch("subprocess.run") as mock_run:
            # Mock timeout exception
            mock_run.side_effect = subprocess.TimeoutExpired(["orbctl", "create"], 60)

            # This should trigger timeout retry logic
            with self.assertRaises(subprocess.TimeoutExpired):
                self.connector._execute_with_retry(
                    ["orbctl", "create", "ubuntu:22.04", "test-vm"],
                    max_retries=1,
                    is_network_operation=True,
                )

    def test_non_network_operation_no_retry(self):
        """Test that non-network operations don't trigger retry logic."""
        with patch.object(self.connector, "_execute_with_retry") as mock_execute:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "command not found"
            mock_execute.return_value = mock_result

            # This should NOT trigger network retry logic
            success, output = self.connector.run_shell_command("ls /nonexistent")

            assert not success
            # Verify it was called with is_network_operation=False
            mock_execute.assert_called()
            call_kwargs = mock_execute.call_args.kwargs
            assert call_kwargs.get("is_network_operation") is False
