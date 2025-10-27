"""
Example Inventory: Web Stack with Separate Database

This inventory defines a multi-tier web application with:
- Web servers (load balanced)
- Database server (single instance)
- Cache server (Redis)

Usage:
    pyinfra inventories/web-stack.py deploy.py
"""

# Web tier - multiple instances for load balancing
web_servers = [
    ("@orbstack/web-1",),
    ("@orbstack/web-2",),
]

# Database tier - single instance
database = [
    ("@orbstack/db-1",),
]

# Cache tier - Redis
cache = [
    ("@orbstack/cache-1",),
]

# All production servers
production = web_servers + database + cache
