"""
Unit tests for VM operations command builders.

These tests demonstrate how extracting command construction logic
into separate functions improves test coverage reporting.
"""

from pyinfra_orbstack.operations.vm import (
    build_ssh_info_command,
    build_vm_clone_command,
    build_vm_create_command,
    build_vm_delete_command,
    build_vm_export_command,
    build_vm_import_command,
    build_vm_info_command,
    build_vm_list_command,
    build_vm_rename_command,
    build_vm_restart_command,
    build_vm_start_command,
    build_vm_stop_command,
)


class TestVMCreateCommandBuilder:
    """Test vm_create command builder."""

    def test_basic_command(self):
        """Test basic VM creation command."""
        cmd = build_vm_create_command("test-vm", "ubuntu:22.04")
        assert cmd == "orbctl create ubuntu:22.04 test-vm"

    def test_with_arch(self):
        """Test VM creation with architecture."""
        cmd = build_vm_create_command("test-vm", "ubuntu:22.04", arch="arm64")
        assert cmd == "orbctl create ubuntu:22.04 test-vm --arch arm64"

    def test_with_user(self):
        """Test VM creation with user."""
        cmd = build_vm_create_command("test-vm", "ubuntu:22.04", user="ubuntu")
        assert cmd == "orbctl create ubuntu:22.04 test-vm --user ubuntu"

    def test_with_arch_and_user(self):
        """Test VM creation with both arch and user."""
        cmd = build_vm_create_command(
            "test-vm", "ubuntu:22.04", arch="arm64", user="ubuntu"
        )
        assert cmd == "orbctl create ubuntu:22.04 test-vm --arch arm64 --user ubuntu"


class TestVMCloneCommandBuilder:
    """Test vm_clone command builder."""

    def test_basic_clone(self):
        """Test basic VM clone command."""
        cmd = build_vm_clone_command("source-vm", "cloned-vm")
        assert cmd == "orbctl clone source-vm cloned-vm"


class TestVMExportCommandBuilder:
    """Test vm_export command builder."""

    def test_basic_export(self):
        """Test basic VM export command."""
        cmd = build_vm_export_command("test-vm", "/tmp/backup.tar.zst")
        assert cmd == "orbctl export test-vm /tmp/backup.tar.zst"


class TestVMImportCommandBuilder:
    """Test vm_import command builder."""

    def test_basic_import(self):
        """Test basic VM import command."""
        cmd = build_vm_import_command("/tmp/backup.tar.zst", "restored-vm")
        assert cmd == "orbctl import -n restored-vm /tmp/backup.tar.zst"


class TestVMRenameCommandBuilder:
    """Test vm_rename command builder."""

    def test_basic_rename(self):
        """Test basic VM rename command."""
        cmd = build_vm_rename_command("old-vm", "new-vm")
        assert cmd == "orbctl rename old-vm new-vm"


class TestVMDeleteCommandBuilder:
    """Test vm_delete command builder."""

    def test_basic_delete(self):
        """Test basic VM delete command."""
        cmd = build_vm_delete_command("test-vm")
        assert cmd == "orbctl delete  test-vm"

    def test_delete_with_force(self):
        """Test VM delete with force flag."""
        cmd = build_vm_delete_command("test-vm", force=True)
        assert cmd == "orbctl delete -f test-vm"


class TestVMLifecycleCommandBuilders:
    """Test VM lifecycle command builders."""

    def test_start_command(self):
        """Test VM start command."""
        cmd = build_vm_start_command("test-vm")
        assert cmd == "orbctl start test-vm"

    def test_stop_command(self):
        """Test VM stop command."""
        cmd = build_vm_stop_command("test-vm")
        assert cmd == "orbctl stop  test-vm"

    def test_stop_with_force(self):
        """Test VM stop with force."""
        cmd = build_vm_stop_command("test-vm", force=True)
        assert cmd == "orbctl stop -f test-vm"

    def test_restart_command(self):
        """Test VM restart command."""
        cmd = build_vm_restart_command("test-vm")
        assert cmd == "orbctl restart test-vm"


class TestVMInfoCommandBuilders:
    """Test VM information command builders."""

    def test_info_command(self):
        """Test VM info command."""
        cmd = build_vm_info_command("test-vm")
        assert cmd == "orbctl info test-vm --format json"

    def test_list_command(self):
        """Test VM list command."""
        cmd = build_vm_list_command()
        assert cmd == "orbctl list -f json"


class TestSSHCommandBuilders:
    """Test SSH command builders."""

    def test_ssh_info_with_machine(self):
        """Test SSH info with machine name."""
        cmd = build_ssh_info_command("test-vm")
        assert cmd == "orbctl info test-vm --format json"

    def test_ssh_info_without_machine(self):
        """Test SSH info without machine name."""
        cmd = build_ssh_info_command()
        assert cmd == "orbctl ssh"


class TestCommandBuilderEdgeCases:
    """Test edge cases for command builders."""

    def test_vm_names_with_special_characters(self):
        """Test VM names with special characters."""
        names = [
            ("test-vm-01", "test_vm_01"),
            ("web-server", "web_server"),
            ("db_01", "db-01"),
        ]

        for old_name, new_name in names:
            cmd = build_vm_rename_command(old_name, new_name)
            assert old_name in cmd
            assert new_name in cmd

    def test_export_paths_with_spaces(self):
        """Test export paths with special characters."""
        # Note: In real usage, paths with spaces should be handled by the shell
        cmd = build_vm_export_command("test-vm", "/tmp/my backup.tar.zst")
        assert "test-vm" in cmd
        assert "/tmp/my backup.tar.zst" in cmd

    def test_image_formats(self):
        """Test various image formats."""
        images = [
            "ubuntu:22.04",
            "alpine:latest",
            "debian:bullseye",
            "centos:7",
        ]

        for image in images:
            cmd = build_vm_create_command("test-vm", image)
            assert image in cmd
            assert "orbctl create" in cmd


class TestCommandBuilderIntegration:
    """Test command builder integration scenarios."""

    def test_backup_restore_workflow_commands(self):
        """Test commands for backup and restore workflow."""
        vm_name = "production-vm"
        backup_path = "/backups/production.tar.zst"
        restore_name = "production-restored"

        # Export command
        export_cmd = build_vm_export_command(vm_name, backup_path)
        assert export_cmd == f"orbctl export {vm_name} {backup_path}"

        # Import command
        import_cmd = build_vm_import_command(backup_path, restore_name)
        assert import_cmd == f"orbctl import -n {restore_name} {backup_path}"

    def test_clone_rename_workflow_commands(self):
        """Test commands for clone and rename workflow."""
        source = "base-vm"
        clone = "base-vm-clone"
        final = "production-vm"

        # Clone command
        clone_cmd = build_vm_clone_command(source, clone)
        assert clone_cmd == f"orbctl clone {source} {clone}"

        # Rename command
        rename_cmd = build_vm_rename_command(clone, final)
        assert rename_cmd == f"orbctl rename {clone} {final}"

    def test_lifecycle_workflow_commands(self):
        """Test complete lifecycle workflow commands."""
        vm_name = "test-vm"
        image = "ubuntu:22.04"

        # Create
        create_cmd = build_vm_create_command(vm_name, image, arch="arm64")
        assert "orbctl create" in create_cmd
        assert vm_name in create_cmd
        assert image in create_cmd
        assert "--arch arm64" in create_cmd

        # Start
        start_cmd = build_vm_start_command(vm_name)
        assert start_cmd == f"orbctl start {vm_name}"

        # Info
        info_cmd = build_vm_info_command(vm_name)
        assert info_cmd == f"orbctl info {vm_name} --format json"

        # Stop
        stop_cmd = build_vm_stop_command(vm_name, force=True)
        assert "orbctl stop -f" in stop_cmd

        # Delete
        delete_cmd = build_vm_delete_command(vm_name, force=True)
        assert "orbctl delete -f" in delete_cmd
