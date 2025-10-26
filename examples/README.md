# PyInfra OrbStack Examples

This directory contains practical examples demonstrating how to use the PyInfra OrbStack connector in real-world scenarios.

## Available Examples

*TODO*

### Planned Examples

- **Basic VM Setup** - Create and configure a simple VM
- **Multi-VM Deployment** - Deploy and coordinate multiple VMs
- **Network Configuration** - Cross-VM communication and networking
- **Web Server Deployment** - Complete web server setup
- **Database Server Setup** - Database server configuration
- **Migration from orbctl** - Converting raw orbctl commands to PyInfra operations

## Running Examples

Each example is a self-contained Python script or directory with:

- `deploy.py` - Main deployment script
- `inventory.py` - Host inventory configuration (if needed)
- `README.md` - Example-specific documentation

To run an example:

```bash
cd examples/example-name
uv run pyinfra inventory.py deploy.py
```

## Requirements

- Python 3.8+
- PyInfra 2.0.0+
- OrbStack installed and running
- pyinfra-orbstack package installed (`uv add pyinfra-orbstack`)
