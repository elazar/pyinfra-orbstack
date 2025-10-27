#!/usr/bin/env python3
"""
VM Lifecycle Management Example

This example demonstrates:
- Using OrbStack-specific operations from pyinfra_orbstack
- Creating and managing VMs
- Getting VM information
- VM lifecycle operations

Usage:
    python3 03-vm-lifecycle-management.py
"""

from pyinfra import host
from pyinfra.operations import server

# Import OrbStack-specific operations
from pyinfra_orbstack.operations.vm import (
    vm_info,
    vm_list,
)

# Additional operations available (commented out for safety):
# from pyinfra_orbstack.operations.vm import (
#     vm_create,
#     vm_delete,
#     vm_restart,
#     vm_start,
#     vm_stop,
# )

# Note: This example assumes you're running from a host that can execute orbctl
# You can target the local machine or use @local connector

# List all VMs
vm_list(
    name="List all OrbStack VMs",
)

# Get information about a specific VM
# (This operation should be run with @orbstack/vm-name connector)
if host.data.get("vm_name"):
    vm_info(
        name=f"Get info for {host.data['vm_name']}",
    )

# Example: Create a new VM (commented out to prevent accidental execution)
# vm_create(
#     name="Create development VM",
#     vm_name="dev-vm",
#     image="ubuntu:22.04",
#     arch="arm64",
# )

# Example: Start a VM
# vm_start(
#     name="Start VM",
#     vm_name="dev-vm",
# )

# Example: Stop a VM
# vm_stop(
#     name="Stop VM",
#     vm_name="dev-vm",
# )

# Example: Restart a VM
# vm_restart(
#     name="Restart VM",
#     vm_name="dev-vm",
# )

# Example: Delete a VM (commented out for safety)
# vm_delete(
#     name="Delete VM",
#     vm_name="dev-vm",
# )

# Check VM status using standard PyInfra operations
server.shell(
    name="Check OrbStack status",
    commands=[
        "orbctl status",
        "orbctl list",
    ],
)

print("✅ VM lifecycle operations demonstrated!")
print("")
print("To actually execute lifecycle operations, uncomment the desired")
print("operations in the script and run with appropriate permissions.")
print("")
print("Example commands:")
print("  # List VMs:")
print("  pyinfra @local 03-vm-lifecycle-management.py")
print("")
print("  # Get info about a specific VM:")
print("  pyinfra @orbstack/my-vm 03-vm-lifecycle-management.py")
