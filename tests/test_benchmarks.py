"""
Performance benchmarks for PyInfra OrbStack connector.

These tests use pytest-benchmark to track performance over time and detect regressions.
Run with: pytest tests/test_benchmarks.py --benchmark-only
"""

import json
from unittest.mock import Mock, patch

import pytest

from pyinfra_orbstack.connector import OrbStackConnector
from pyinfra_orbstack.operations.vm import (
    build_vm_create_command,
    build_vm_delete_command,
    build_vm_info_command,
    build_vm_list_command,
    build_vm_start_command,
    build_vm_stop_command,
)


class TestCommandBuilderBenchmarks:
    """Benchmark command builder functions."""

    def test_benchmark_vm_create_command(self, benchmark):
        """Benchmark VM create command builder."""
        result = benchmark(
            build_vm_create_command,
            "test-vm",
            "ubuntu:22.04",
            arch="arm64",
            user="test",
        )
        assert "orbctl create" in result

    def test_benchmark_vm_delete_command(self, benchmark):
        """Benchmark VM delete command builder."""
        result = benchmark(build_vm_delete_command, "test-vm", force=True)
        assert "orbctl delete" in result

    def test_benchmark_vm_info_command(self, benchmark):
        """Benchmark VM info command builder."""
        result = benchmark(build_vm_info_command, "test-vm")
        assert "orbctl info" in result

    def test_benchmark_vm_list_command(self, benchmark):
        """Benchmark VM list command builder."""
        result = benchmark(build_vm_list_command)
        assert "orbctl list" in result

    def test_benchmark_vm_start_command(self, benchmark):
        """Benchmark VM start command builder."""
        result = benchmark(build_vm_start_command, "test-vm")
        assert "orbctl start" in result

    def test_benchmark_vm_stop_command(self, benchmark):
        """Benchmark VM stop command builder."""
        result = benchmark(build_vm_stop_command, "test-vm", force=True)
        assert "orbctl stop" in result


class TestConnectorBenchmarks:
    """Benchmark connector operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_state = Mock()
        self.mock_host = Mock()
        self.mock_host.data = {"vm_name": "test-vm"}

    @patch("subprocess.run")
    def test_benchmark_make_names_data(self, mock_run, benchmark):
        """Benchmark make_names_data method."""
        # Mock orbctl list output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            [
                {"name": "vm1", "state": "running", "distro": "ubuntu"},
                {"name": "vm2", "state": "stopped", "distro": "debian"},
                {"name": "vm3", "state": "running", "distro": "fedora"},
            ]
        )
        mock_run.return_value = mock_result

        result = benchmark(lambda: list(OrbStackConnector.make_names_data()))
        assert len(result) == 3

    @patch("subprocess.run")
    def test_benchmark_connect(self, mock_run, benchmark):
        """Benchmark connect method."""
        # Mock orbctl info output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"state": "running"})
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)
        result = benchmark(connector.connect)
        assert result is True

    @patch("subprocess.run")
    def test_benchmark_run_shell_command(self, mock_run, benchmark):
        """Benchmark run_shell_command method."""
        # Mock orbctl run output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        connector = OrbStackConnector(self.mock_state, self.mock_host)

        def run_command():
            success, _ = connector.run_shell_command("echo test")
            return success

        result = benchmark(run_command)
        assert result is True


class TestIntegrationBenchmarks:
    """Benchmark integration scenarios (requires OrbStack)."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_benchmark_vm_list_real(self, benchmark):
        """Benchmark real VM listing (integration test)."""
        import subprocess

        def list_vms():
            result = subprocess.run(
                ["orbctl", "list", "-f", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0

        result = benchmark(list_vms)
        assert result is True

    @pytest.mark.integration
    @pytest.mark.slow
    def test_benchmark_vm_info_real(self, benchmark):
        """Benchmark real VM info retrieval (integration test)."""
        import subprocess

        # Get first available VM
        list_result = subprocess.run(
            ["orbctl", "list", "-f", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if list_result.returncode != 0:
            pytest.skip("No VMs available")

        vms = json.loads(list_result.stdout)
        if not vms:
            pytest.skip("No VMs available")

        vm_name = vms[0]["name"]

        def get_vm_info():
            result = subprocess.run(
                ["orbctl", "info", vm_name, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0

        result = benchmark(get_vm_info)
        assert result is True


# Benchmark groups for comparison
@pytest.mark.benchmark(group="command-builders")
class TestCommandBuilderPerformance:
    """Compare performance of different command builders."""

    def test_simple_command(self, benchmark):
        """Benchmark simple command (list)."""
        benchmark(build_vm_list_command)

    def test_command_with_args(self, benchmark):
        """Benchmark command with arguments (info)."""
        benchmark(build_vm_info_command, "test-vm")

    def test_complex_command(self, benchmark):
        """Benchmark complex command (create with options)."""
        benchmark(
            build_vm_create_command,
            "test-vm",
            "ubuntu:22.04",
            arch="arm64",
            user="testuser",
        )
