"""
Unit tests for VM operations command builders.

These tests demonstrate how extracting command construction logic
into separate functions improves test coverage reporting.
"""

from pyinfra_orbstack.operations.vm import (
    build_config_get_command,
    build_config_set_command,
    build_config_show_command,
    build_ssh_info_command,
    build_vm_clone_command,
    build_vm_create_command,
    build_vm_delete_command,
    build_vm_dns_lookup_command,
    build_vm_export_command,
    build_vm_import_command,
    build_vm_info_command,
    build_vm_list_command,
    build_vm_logs_command,
    build_vm_network_details_command,
    build_vm_rename_command,
    build_vm_restart_command,
    build_vm_start_command,
    build_vm_stop_command,
    build_vm_test_connectivity_command,
    build_vm_username_set_command,
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


# Phase 3B: Configuration Management Command Builder Tests


class TestConfigGetCommandBuilder:
    """Test orbstack_config_get command builder."""

    def test_get_cpu_config(self):
        """Test getting CPU configuration."""
        cmd = build_config_get_command("cpu")
        assert cmd == "orbctl config get cpu"

    def test_get_memory_config(self):
        """Test getting memory configuration."""
        cmd = build_config_get_command("memory_mib")
        assert cmd == "orbctl config get memory_mib"

    def test_get_network_config(self):
        """Test getting network configuration."""
        cmd = build_config_get_command("network.subnet4")
        assert cmd == "orbctl config get network.subnet4"

    def test_get_nested_config(self):
        """Test getting nested configuration."""
        cmd = build_config_get_command("docker.expose_ports_to_lan")
        assert cmd == "orbctl config get docker.expose_ports_to_lan"

    def test_get_rosetta_config(self):
        """Test getting Rosetta configuration."""
        cmd = build_config_get_command("rosetta")
        assert cmd == "orbctl config get rosetta"


class TestConfigSetCommandBuilder:
    """Test orbstack_config_set command builder."""

    def test_set_cpu_config(self):
        """Test setting CPU configuration."""
        cmd = build_config_set_command("cpu", "8")
        assert cmd == "orbctl config set cpu 8"

    def test_set_memory_config(self):
        """Test setting memory configuration."""
        cmd = build_config_set_command("memory_mib", "16384")
        assert cmd == "orbctl config set memory_mib 16384"

    def test_set_boolean_config(self):
        """Test setting boolean configuration."""
        cmd = build_config_set_command("rosetta", "true")
        assert cmd == "orbctl config set rosetta true"

    def test_set_network_config(self):
        """Test setting network configuration."""
        cmd = build_config_set_command("network.subnet4", "192.168.100.0/24")
        assert cmd == "orbctl config set network.subnet4 192.168.100.0/24"

    def test_set_nested_config(self):
        """Test setting nested configuration."""
        cmd = build_config_set_command("setup.use_admin", "false")
        assert cmd == "orbctl config set setup.use_admin false"


class TestConfigShowCommandBuilder:
    """Test orbstack_config_show command builder."""

    def test_show_config(self):
        """Test showing all configuration."""
        cmd = build_config_show_command()
        assert cmd == "orbctl config show"


class TestVMUsernameSetCommandBuilder:
    """Test vm_username_set command builder."""

    def test_set_username_basic(self):
        """Test setting VM username."""
        cmd = build_vm_username_set_command("test-vm", "ubuntu")
        assert cmd == "orbctl config set machine.test-vm.username ubuntu"

    def test_set_username_different_user(self):
        """Test setting different usernames for different VMs."""
        cmd1 = build_vm_username_set_command("web-server", "nginx")
        cmd2 = build_vm_username_set_command("db-server", "postgres")

        assert cmd1 == "orbctl config set machine.web-server.username nginx"
        assert cmd2 == "orbctl config set machine.db-server.username postgres"

    def test_set_username_with_hyphens(self):
        """Test setting username for VM with hyphens."""
        cmd = build_vm_username_set_command("my-test-vm-01", "testuser")
        assert cmd == "orbctl config set machine.my-test-vm-01.username testuser"

    def test_set_username_with_underscores(self):
        """Test setting username for VM with underscores."""
        cmd = build_vm_username_set_command("test_vm_prod", "admin")
        assert cmd == "orbctl config set machine.test_vm_prod.username admin"


class TestConfigCommandBuilderEdgeCases:
    """Test edge cases for configuration command builders."""

    def test_config_keys_with_dots(self):
        """Test configuration keys with multiple dots."""
        keys = [
            "network.subnet4",
            "network.https",
            "docker.expose_ports_to_lan",
            "machine.test-vm.username",
        ]

        for key in keys:
            cmd = build_config_get_command(key)
            assert key in cmd
            assert "orbctl config get" in cmd

    def test_config_values_with_special_chars(self):
        """Test configuration values with special characters."""
        test_cases = [
            ("network.subnet4", "192.168.100.0/24"),
            ("machines.forward_ports", "true"),
            ("setup.use_admin", "false"),
        ]

        for key, value in test_cases:
            cmd = build_config_set_command(key, value)
            assert key in cmd
            assert value in cmd

    def test_numeric_values_as_strings(self):
        """Test numeric configuration values passed as strings."""
        cmd1 = build_config_set_command("cpu", "16")
        cmd2 = build_config_set_command("memory_mib", "32768")

        assert "cpu 16" in cmd1
        assert "memory_mib 32768" in cmd2


class TestConfigWorkflows:
    """Test configuration management workflows."""

    def test_resource_allocation_workflow(self):
        """Test commands for resource allocation workflow."""
        # Get current CPU
        get_cpu = build_config_get_command("cpu")
        assert get_cpu == "orbctl config get cpu"

        # Set new CPU value
        set_cpu = build_config_set_command("cpu", "12")
        assert set_cpu == "orbctl config set cpu 12"

        # Get current memory
        get_mem = build_config_get_command("memory_mib")
        assert get_mem == "orbctl config get memory_mib"

        # Set new memory value
        set_mem = build_config_set_command("memory_mib", "24576")
        assert set_mem == "orbctl config set memory_mib 24576"

    def test_vm_user_configuration_workflow(self):
        """Test commands for VM user configuration workflow."""
        vms = [
            ("web-1", "nginx"),
            ("web-2", "nginx"),
            ("db-1", "postgres"),
            ("cache-1", "redis"),
        ]

        for vm_name, username in vms:
            cmd = build_vm_username_set_command(vm_name, username)
            assert vm_name in cmd
            assert username in cmd
            assert "orbctl config set" in cmd

    def test_inspect_and_modify_workflow(self):
        """Test commands for inspect and modify workflow."""
        # Show all config
        show_cmd = build_config_show_command()
        assert show_cmd == "orbctl config show"

        # Get specific value
        get_cmd = build_config_get_command("rosetta")
        assert "get rosetta" in get_cmd

        # Set new value
        set_cmd = build_config_set_command("rosetta", "false")
        assert "set rosetta false" in set_cmd

    def test_multi_vm_setup_workflow(self):
        """Test commands for setting up multiple VMs."""
        vm_configs = {
            "dev-vm": "developer",
            "test-vm": "tester",
            "staging-vm": "deployer",
            "prod-vm": "admin",
        }

        for vm_name, username in vm_configs.items():
            cmd = build_vm_username_set_command(vm_name, username)
            expected = f"orbctl config set machine.{vm_name}.username {username}"
            assert cmd == expected


# Phase 3C: Logging and Diagnostics Command Builder Tests


class TestVMLogsCommandBuilder:
    """Test vm_logs command builder."""

    def test_basic_logs(self):
        """Test basic VM logs command."""
        cmd = build_vm_logs_command("test-vm")
        assert cmd == "orbctl logs test-vm"

    def test_logs_with_all_flag(self):
        """Test VM logs with --all flag."""
        cmd = build_vm_logs_command("test-vm", all_logs=True)
        assert cmd == "orbctl logs test-vm --all"

    def test_logs_without_all_flag(self):
        """Test VM logs without --all flag explicitly."""
        cmd = build_vm_logs_command("test-vm", all_logs=False)
        assert cmd == "orbctl logs test-vm"

    def test_logs_various_vm_names(self):
        """Test logs command with various VM names."""
        test_vms = [
            "web-server",
            "db_server",
            "cache-01",
            "prod-vm",
        ]

        for vm_name in test_vms:
            cmd = build_vm_logs_command(vm_name)
            assert vm_name in cmd
            assert "orbctl logs" in cmd


class TestLogsCommandBuilderEdgeCases:
    """Test edge cases for logs command builder."""

    def test_logs_vm_names_with_special_chars(self):
        """Test logs with VM names containing special characters."""
        vm_names = [
            "test-vm-01",
            "web_server_prod",
            "db-cluster-primary",
            "cache_01",
        ]

        for vm_name in vm_names:
            cmd = build_vm_logs_command(vm_name)
            assert vm_name in cmd
            cmd_all = build_vm_logs_command(vm_name, all_logs=True)
            assert vm_name in cmd_all
            assert "--all" in cmd_all


class TestLogsWorkflows:
    """Test logging and diagnostics workflows."""

    def test_debugging_workflow(self):
        """Test commands for VM debugging workflow."""
        vm_name = "problem-vm"

        # Get basic logs
        basic_logs = build_vm_logs_command(vm_name)
        assert basic_logs == f"orbctl logs {vm_name}"

        # Get detailed logs for debugging
        detailed_logs = build_vm_logs_command(vm_name, all_logs=True)
        assert detailed_logs == f"orbctl logs {vm_name} --all"

        # Get VM info for status
        vm_info = build_vm_info_command(vm_name)
        assert vm_info == f"orbctl info {vm_name} --format json"

    def test_monitoring_workflow(self):
        """Test commands for VM monitoring workflow."""
        vms = ["web-1", "web-2", "db-1"]

        for vm_name in vms:
            # Check status
            info_cmd = build_vm_info_command(vm_name)
            assert "orbctl info" in info_cmd
            assert vm_name in info_cmd

            # Check logs if issues
            logs_cmd = build_vm_logs_command(vm_name)
            assert "orbctl logs" in logs_cmd
            assert vm_name in logs_cmd

    def test_troubleshooting_workflow(self):
        """Test commands for troubleshooting workflow."""
        vm_name = "failing-vm"

        # Step 1: Check VM info/status
        info = build_vm_info_command(vm_name)
        assert f"orbctl info {vm_name}" in info

        # Step 2: Get basic logs
        logs = build_vm_logs_command(vm_name)
        assert logs == f"orbctl logs {vm_name}"

        # Step 3: Get detailed logs if needed
        detailed = build_vm_logs_command(vm_name, all_logs=True)
        assert detailed == f"orbctl logs {vm_name} --all"

        # Step 4: Restart if needed
        restart = build_vm_restart_command(vm_name)
        assert restart == f"orbctl restart {vm_name}"


# ============================================================================
# Phase 3A: VM Networking Information Command Builder Tests
# ============================================================================


class TestVMNetworkDetailsCommandBuilder:
    """Test vm_network_details command builder."""

    def test_builds_network_details_command(self):
        """Test basic network details command construction."""
        vm_name = "web-vm"
        cmd = build_vm_network_details_command(vm_name)

        assert cmd == "orbctl info web-vm --format json"

    def test_different_vm_names(self):
        """Test network details command with various VM names."""
        test_cases = [
            ("simple", "orbctl info simple --format json"),
            ("with-dashes", "orbctl info with-dashes --format json"),
            ("vm_123", "orbctl info vm_123 --format json"),
        ]

        for vm_name, expected in test_cases:
            cmd = build_vm_network_details_command(vm_name)
            assert cmd == expected


class TestVMTestConnectivityCommandBuilder:
    """Test vm_test_connectivity command builder."""

    def test_ping_method_default(self):
        """Test ping connectivity command with default count."""
        cmd = build_vm_test_connectivity_command("other-vm.orb.local")
        assert cmd == "ping -c 3 other-vm.orb.local"

    def test_ping_method_custom_count(self):
        """Test ping connectivity command with custom count."""
        cmd = build_vm_test_connectivity_command(
            "other-vm.orb.local", method="ping", count=5
        )
        assert cmd == "ping -c 5 other-vm.orb.local"

    def test_curl_method(self):
        """Test curl connectivity command."""
        cmd = build_vm_test_connectivity_command(
            "http://other-vm.orb.local:8080", method="curl"
        )
        assert cmd == (
            "curl -s -o /dev/null -w '%{http_code}' "
            "--connect-timeout 5 http://other-vm.orb.local:8080"
        )

    def test_nc_method_with_port(self):
        """Test netcat connectivity command with explicit port."""
        cmd = build_vm_test_connectivity_command("other-vm.orb.local:3306", method="nc")
        assert cmd == "nc -zv -w 5 other-vm.orb.local 3306"

    def test_nc_method_default_port(self):
        """Test netcat connectivity command with default port (22)."""
        cmd = build_vm_test_connectivity_command("other-vm.orb.local", method="nc")
        assert cmd == "nc -zv -w 5 other-vm.orb.local 22"

    def test_invalid_method_raises_error(self):
        """Test that invalid connectivity method raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="Unsupported connectivity test method"):
            build_vm_test_connectivity_command("target", method="invalid")


class TestVMDNSLookupCommandBuilder:
    """Test vm_dns_lookup command builder."""

    def test_default_a_record_lookup(self):
        """Test DNS lookup with default A record."""
        cmd = build_vm_dns_lookup_command("example.com")
        assert cmd == "host -t A example.com"

    def test_orb_local_domain_lookup(self):
        """Test DNS lookup for .orb.local domain."""
        cmd = build_vm_dns_lookup_command("other-vm.orb.local")
        assert cmd == "host -t A other-vm.orb.local"

    def test_aaaa_record_lookup(self):
        """Test DNS lookup for AAAA (IPv6) record."""
        cmd = build_vm_dns_lookup_command("example.com", lookup_type="AAAA")
        assert cmd == "host -t AAAA example.com"

    def test_mx_record_lookup(self):
        """Test DNS lookup for MX record."""
        cmd = build_vm_dns_lookup_command("example.com", lookup_type="MX")
        assert cmd == "host -t MX example.com"

    def test_cname_record_lookup(self):
        """Test DNS lookup for CNAME record."""
        cmd = build_vm_dns_lookup_command("www.example.com", lookup_type="CNAME")
        assert cmd == "host -t CNAME www.example.com"


class TestNetworkingCommandBuilderEdgeCases:
    """Test edge cases for networking command builders."""

    def test_network_details_empty_vm_name(self):
        """Test network details with empty VM name still builds command."""
        cmd = build_vm_network_details_command("")
        assert cmd == "orbctl info  --format json"

    def test_connectivity_with_ip_address(self):
        """Test connectivity test with IP address instead of hostname."""
        cmd = build_vm_test_connectivity_command("192.168.1.1")
        assert cmd == "ping -c 3 192.168.1.1"

    def test_connectivity_curl_with_https(self):
        """Test curl connectivity with HTTPS URL."""
        cmd = build_vm_test_connectivity_command("https://example.com", method="curl")
        assert "https://example.com" in cmd
        assert "curl" in cmd

    def test_dns_lookup_subdomain(self):
        """Test DNS lookup for subdomain."""
        cmd = build_vm_dns_lookup_command("api.staging.example.com")
        assert cmd == "host -t A api.staging.example.com"

    def test_connectivity_nc_ipv6(self):
        """Test netcat with IPv6 address and port."""
        cmd = build_vm_test_connectivity_command("[::1]:8080", method="nc")
        assert cmd == "nc -zv -w 5 [::1] 8080"


class TestNetworkingWorkflows:
    """Test common networking workflow scenarios."""

    def test_cross_vm_communication_workflow(self):
        """Test workflow for setting up cross-VM communication."""
        source_vm = "frontend"
        target_vm = "backend"

        # Step 1: Get network details for both VMs
        source_net = build_vm_network_details_command(source_vm)
        target_net = build_vm_network_details_command(target_vm)
        assert "orbctl info frontend" in source_net
        assert "orbctl info backend" in target_net

        # Step 2: Test basic connectivity
        ping_cmd = build_vm_test_connectivity_command(
            f"{target_vm}.orb.local", method="ping"
        )
        assert ping_cmd == f"ping -c 3 {target_vm}.orb.local"

        # Step 3: Test service connectivity
        http_cmd = build_vm_test_connectivity_command(
            f"http://{target_vm}.orb.local:8080", method="curl"
        )
        assert f"{target_vm}.orb.local:8080" in http_cmd

    def test_dns_troubleshooting_workflow(self):
        """Test workflow for DNS troubleshooting."""
        hostname = "service.orb.local"

        # Step 1: Check A record
        a_lookup = build_vm_dns_lookup_command(hostname, lookup_type="A")
        assert a_lookup == f"host -t A {hostname}"

        # Step 2: Check IPv6
        aaaa_lookup = build_vm_dns_lookup_command(hostname, lookup_type="AAAA")
        assert aaaa_lookup == f"host -t AAAA {hostname}"

        # Step 3: Test connectivity once IP is known
        ping_cmd = build_vm_test_connectivity_command(hostname)
        assert ping_cmd == f"ping -c 3 {hostname}"

    def test_port_connectivity_workflow(self):
        """Test workflow for checking multiple ports."""
        target = "db.orb.local"
        ports = [22, 3306, 5432]

        for port in ports:
            cmd = build_vm_test_connectivity_command(f"{target}:{port}", method="nc")
            assert f"nc -zv -w 5 {target} {port}" == cmd
