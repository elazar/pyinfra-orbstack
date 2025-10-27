# Example Inventories

This directory contains example inventory files for PyInfra deployments using the OrbStack connector.

## Available Inventories

### `web-stack.py` - Multi-Tier Web Application

Defines a complete web stack with:
- Load-balanced web servers (web-1, web-2)
- Database server (db-1)
- Cache server (cache-1)

**Usage:**
```bash
# Create VMs
orbctl create web-1 ubuntu:22.04
orbctl create web-2 ubuntu:22.04
orbctl create db-1 ubuntu:22.04
orbctl create cache-1 ubuntu:22.04

# Deploy to all tiers
pyinfra inventories/web-stack.py deploy.py

# Deploy to specific tier
pyinfra inventories/web-stack.py:web_servers deploy.py
pyinfra inventories/web-stack.py:database deploy.py
```

### `environments.py` - Dev/Staging/Production

Defines separate environments for development workflow:
- Development (single VM)
- Staging (web + db)
- Production (2x web, db, cache)

**Usage:**
```bash
# Deploy to specific environment
pyinfra inventories/environments.py:dev deploy.py
pyinfra inventories/environments.py:staging deploy.py
pyinfra inventories/environments.py:prod deploy.py

# Deploy to all environments (careful!)
pyinfra inventories/environments.py deploy.py
```

## Creating Custom Inventories

### Basic Inventory

```python
# Simple list of hosts
servers = [
    ("@orbstack/server-1",),
    ("@orbstack/server-2",),
]
```

### With Groups

```python
# Multiple groups
web_servers = [
    ("@orbstack/web-1",),
    ("@orbstack/web-2",),
]

db_servers = [
    ("@orbstack/db-1",),
]

# All servers
all_servers = web_servers + db_servers
```

### With Host Data

```python
# Attach data to hosts
web_servers = [
    ("@orbstack/web-1", {"env": "prod", "role": "web"}),
    ("@orbstack/web-2", {"env": "prod", "role": "web"}),
]

# Access in deploy script:
from pyinfra import host
env = host.data.get("env")
role = host.data.get("role")
```

### Dynamic Inventories

```python
# Generate hosts dynamically
import subprocess
import json

def get_orbstack_vms():
    result = subprocess.run(
        ["orbctl", "list", "--format", "json"],
        capture_output=True,
        text=True
    )
    vms = json.loads(result.stdout)
    return [(f"@orbstack/{vm['name']}",) for vm in vms if vm['state'] == 'running']

# All running VMs
all_vms = get_orbstack_vms()
```

## Best Practices

### 1. Descriptive Names

Use clear, descriptive names for groups:
```python
# Good
web_servers = [...]
api_servers = [...]
database_primary = [...]

# Avoid
servers1 = [...]
group_a = [...]
```

### 2. Environment Separation

Keep environments separate:
```python
# Separate files for safety
# inventories/production.py
# inventories/staging.py
# inventories/development.py

# Or use groups
dev = [...]
staging = [...]
prod = [...]
```

### 3. Host Data

Attach relevant metadata:
```python
servers = [
    ("@orbstack/web-1", {
        "env": "production",
        "role": "web",
        "region": "us-west",
        "version": "v2",
    }),
]
```

### 4. Documentation

Document your inventory:
```python
"""
Production Web Stack

Web Tier: 2x Ubuntu 22.04, Nginx + uWSGI
DB Tier: 1x Ubuntu 22.04, PostgreSQL 14
Cache Tier: 1x Ubuntu 22.04, Redis 7

Last Updated: 2025-10-26
"""
```

## Targeting Specific Groups

```bash
# Target specific group
pyinfra inventory.py:web_servers deploy.py

# Target multiple groups
pyinfra inventory.py:web_servers,db_servers deploy.py

# Exclude groups
pyinfra inventory.py:all_servers,!staging deploy.py
```

## See Also

- [PyInfra Inventory Documentation](https://docs.pyinfra.com/en/2.x/inventory.html)
- [Example Deployments](../)
- [OrbStack Connector Documentation](../../docs/README.md)
