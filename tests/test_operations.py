"""
Tests for the PyInfra OrbStack Operations.
"""


class TestOperationsImport:
    """Test operations module imports."""

    def test_operations_import(self):
        """Test that operations can be imported."""
        from pyinfra_orbstack.operations import (
            vm_create,
            vm_delete,
            vm_info,
            vm_ip,
            vm_list,
            vm_network_info,
            vm_restart,
            vm_start,
            vm_status,
            vm_stop,
        )

        # Verify all operations are callable
        assert callable(vm_create)
        assert callable(vm_delete)
        assert callable(vm_start)
        assert callable(vm_stop)
        assert callable(vm_restart)
        assert callable(vm_info)
        assert callable(vm_list)
        assert callable(vm_status)
        assert callable(vm_ip)
        assert callable(vm_network_info)

    def test_operations_module_structure(self):
        """Test that the operations module has the expected structure."""
        from pyinfra_orbstack.operations import vm

        # Check that all expected operations exist
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

    def test_operations_are_functions(self):
        """Test that operations are functions."""
        from pyinfra_orbstack.operations import vm

        # Check that operations are callable
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

    def test_operations_have_names(self):
        """Test that operations have function names."""
        from pyinfra_orbstack.operations import vm

        # Check that operations are callable (PyInfra decorators change __name__)
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


class TestOperationsModule:
    """Test operations module structure."""

    def test_operations_module_import(self):
        """Test that the operations module can be imported."""
        import pyinfra_orbstack.operations
        import pyinfra_orbstack.operations.vm

        # Verify modules exist
        assert pyinfra_orbstack.operations is not None
        assert pyinfra_orbstack.operations.vm is not None

    def test_operations_all_list(self):
        """Test that __all__ list contains all operations."""
        from pyinfra_orbstack.operations import __all__

        expected_operations = [
            "vm_create",
            "vm_delete",
            "vm_start",
            "vm_stop",
            "vm_restart",
            "vm_info",
            "vm_list",
            "vm_status",
            "vm_ip",
            "vm_network_info",
        ]

        for operation in expected_operations:
            assert operation in __all__

    def test_operations_vm_module_structure(self):
        """Test that vm module has all expected operations."""
        from pyinfra_orbstack.operations import vm

        expected_operations = [
            "vm_create",
            "vm_delete",
            "vm_start",
            "vm_stop",
            "vm_restart",
            "vm_info",
            "vm_list",
            "vm_status",
            "vm_ip",
            "vm_network_info",
        ]

        for operation in expected_operations:
            assert hasattr(vm, operation)
