"""
PyInfra OrbStack Operations

Operations for managing OrbStack VMs and containers.
"""

from .vm import (
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

__all__ = [
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
