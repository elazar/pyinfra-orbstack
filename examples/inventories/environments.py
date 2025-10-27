"""
Example Inventory: Development Environment

This inventory defines development, staging, and production environments.

Usage:
    # Deploy to all environments
    pyinfra inventories/environments.py deploy.py

    # Deploy to specific environment
    pyinfra inventories/environments.py:dev deploy.py
    pyinfra inventories/environments.py:staging deploy.py
    pyinfra inventories/environments.py:prod deploy.py
"""

# Development environment
dev = [
    ("@orbstack/dev-vm",),
]

# Staging environment
staging = [
    ("@orbstack/staging-web",),
    ("@orbstack/staging-db",),
]

# Production environment
prod = [
    ("@orbstack/prod-web-1",),
    ("@orbstack/prod-web-2",),
    ("@orbstack/prod-db",),
    ("@orbstack/prod-cache",),
]
