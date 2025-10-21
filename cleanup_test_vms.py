#!/usr/bin/env python3
"""
Cleanup script for orphaned test VMs.

This script can be run manually to clean up test VMs that were left behind
from previous test runs that crashed or were interrupted.

Usage:
    python cleanup_test_vms.py
    python cleanup_test_vms.py --dry-run
"""

import argparse
import json
import subprocess
import sys


def list_test_vms():
    """List all test VMs."""
    try:
        result = subprocess.run(
            ["orbctl", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        vms = json.loads(result.stdout)

        test_prefixes = [
            "test-vm-",
            "e2e-ops-vm-",
            "deploy-test-vm-",
            "consolidated-test-vm-",
            "e2e-test-vm-",
        ]

        test_vms = [
            vm for vm in vms if any(prefix in vm["name"] for prefix in test_prefixes)
        ]

        return test_vms
    except subprocess.CalledProcessError as e:
        print(f"Error listing VMs: {e}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing VM list: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return []


def delete_vm(vm_name, dry_run=False):
    """Delete a single VM."""
    if dry_run:
        print(f"Would delete: {vm_name}")
        return True

    try:
        result = subprocess.run(
            ["orbctl", "delete", "--force", vm_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print(f"✓ Deleted: {vm_name}")
            return True
        else:
            print(f"✗ Failed to delete {vm_name}: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout deleting {vm_name}")
        return False
    except Exception as e:
        print(f"✗ Error deleting {vm_name}: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Clean up orphaned test VMs from OrbStack"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed information"
    )
    args = parser.parse_args()

    print("Scanning for test VMs...")
    test_vms = list_test_vms()

    if not test_vms:
        print("No test VMs found.")
        return 0

    print(f"\nFound {len(test_vms)} test VM(s):")
    if args.verbose:
        for vm in test_vms:
            state = vm.get("state", "unknown")
            size = vm.get("size", "unknown")
            print(f"  - {vm['name']} ({state}, {size})")
    else:
        for vm in test_vms:
            print(f"  - {vm['name']}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would delete {len(test_vms)} VM(s)")
        return 0

    print(f"\nDeleting {len(test_vms)} VM(s)...")
    success_count = 0
    for vm in test_vms:
        if delete_vm(vm["name"], dry_run=args.dry_run):
            success_count += 1

    print(f"\nCleanup complete: {success_count}/{len(test_vms)} VMs deleted")
    return 0 if success_count == len(test_vms) else 1


if __name__ == "__main__":
    sys.exit(main())
