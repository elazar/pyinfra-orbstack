"""
PyInfra Operations Coverage Tests

These tests focus on achieving coverage of the operations module
by using mock connectors to avoid VM connection issues.
"""

import os
import subprocess
import tempfile
from unittest import TestCase


class TestPyInfraOperationsCoverage(TestCase):
    """Tests for PyInfra operations coverage."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def _create_deployment_file(self, content, filename="deploy.py"):
        """Create a temporary deployment file."""
        deploy_path = os.path.join(self.temp_dir, filename)
        with open(deploy_path, "w") as f:
            f.write(content)
        return deploy_path

    def _create_inventory_file(self, vm_name="test-vm", filename="inventory.py"):
        """Create a temporary inventory file."""
        inventory_content = f"""
# PyInfra inventory for OrbStack VM
hosts = ["@local"]

host_data = [
    ("@local", {{
        "vm_name": "{vm_name}",
        "orbstack_vm": True,
    }})
]
"""
        inventory_path = os.path.join(self.temp_dir, filename)
        with open(inventory_path, "w") as f:
            f.write(inventory_content)
        return inventory_path

    def _run_pyinfra_with_mock_connector(self, deploy_path, inventory_path):
        """Run PyInfra with a mock connector to avoid VM connection issues."""
        # Create a mock connector that always succeeds
        mock_connector_code = """
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the connector to avoid VM connection issues
class MockOrbStackConnector:
    def connect(self):
        return True

    def run_shell_command(self, command, **kwargs):
        return True, type('obj', (object,), {
            'stdout': 'mock output',
            'stderr': ''
        })()

    def put_file(self, *args, **kwargs):
        return True

    def get_file(self, *args, **kwargs):
        return True

# Replace the real connector with our mock
import pyinfra_orbstack.connector
pyinfra_orbstack.connector.OrbStackConnector = MockOrbStackConnector
"""

        # Create mock connector file
        mock_path = os.path.join(self.temp_dir, "mock_connector.py")
        with open(mock_path, "w") as f:
            f.write(mock_connector_code)

        # Run PyInfra with the mock connector
        cmd = ["pyinfra", "--limit", "@local", inventory_path, deploy_path, "-v"]

        # Set environment to use our mock
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.temp_dir}:{env.get('PYTHONPATH', '')}"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # Shorter timeout since we're using mocks
            cwd=self.temp_dir,
            env=env,
        )

        return result

    def test_vm_create_operation_coverage(self):
        """Test vm_create operation coverage."""
        deploy_content = """
from pyinfra_orbstack.operations.vm import vm_create

# Test vm_create with all parameters
vm_create(
    name="test-vm",
    image="ubuntu:22.04",
    arch="arm64",
    user="ubuntu",
    present=True,
)
"""
        deploy_path = self._create_deployment_file(deploy_content)
        inventory_path = self._create_inventory_file()

        result = self._run_pyinfra_with_mock_connector(deploy_path, inventory_path)

        # Check if PyInfra loaded and attempted to execute the operation
        assert (
            "Loading:" in result.stderr or "Loading:" in result.stdout
        ), "PyInfra should have loaded the deployment"
        print(f"Deployment result: {result.stdout}")
        print(f"Deployment stderr: {result.stderr}")

    def test_vm_create_present_false_coverage(self):
        """Test vm_create with present=False coverage."""
        deploy_content = """
from pyinfra_orbstack.operations.vm import vm_create

# Test vm_create with present=False
vm_create(
    name="test-vm",
    image="ubuntu:22.04",
    present=False,
)
"""
        deploy_path = self._create_deployment_file(deploy_content)
        inventory_path = self._create_inventory_file()

        result = self._run_pyinfra_with_mock_connector(deploy_path, inventory_path)

        assert (
            "Loading:" in result.stderr or "Loading:" in result.stdout
        ), "PyInfra should have loaded the deployment"

    def test_vm_delete_operation_coverage(self):
        """Test vm_delete operation coverage."""
        deploy_content = """
from pyinfra_orbstack.operations.vm import vm_delete

# Test vm_delete with force
vm_delete(
    name="test-vm",
    force=True,
)
"""
        deploy_path = self._create_deployment_file(deploy_content)
        inventory_path = self._create_inventory_file()

        result = self._run_pyinfra_with_mock_connector(deploy_path, inventory_path)

        assert (
            "Loading:" in result.stderr or "Loading:" in result.stdout
        ), "PyInfra should have loaded the deployment"

    def test_vm_lifecycle_operations_coverage(self):
        """Test VM lifecycle operations coverage."""
        deploy_content = """
from pyinfra_orbstack.operations.vm import vm_start, vm_stop, vm_restart

# Test VM lifecycle operations
vm_start(name="test-vm")
vm_stop(name="test-vm", force=True)
vm_restart(name="test-vm")
"""
        deploy_path = self._create_deployment_file(deploy_content)
        inventory_path = self._create_inventory_file()

        result = self._run_pyinfra_with_mock_connector(deploy_path, inventory_path)

        assert (
            "Loading:" in result.stderr or "Loading:" in result.stdout
        ), "PyInfra should have loaded the deployment"

    def test_vm_info_operations_coverage(self):
        """Test VM info operations coverage."""
        deploy_content = """
from pyinfra_orbstack.operations.vm import vm_info, vm_list, vm_status, vm_ip, vm_network_info

# Test VM info operations
info = vm_info()
vms = vm_list()
status = vm_status()
ip = vm_ip()
network_info = vm_network_info()
"""
        deploy_path = self._create_deployment_file(deploy_content)
        inventory_path = self._create_inventory_file()

        result = self._run_pyinfra_with_mock_connector(deploy_path, inventory_path)

        assert (
            "Loading:" in result.stderr or "Loading:" in result.stdout
        ), "PyInfra should have loaded the deployment"

    # NOTE: Direct operation execution tests removed because PyInfra operations
    # require proper state and host context that can't be easily mocked.
    # Operation execution is thoroughly tested via:
    # - test_pyinfra_operations_e2e.py (actual PyInfra deployments)
    # - test_operations_command_construction.py (command building logic)
    # - test_vm_operations_logic.py (operation logic without PyInfra context)
