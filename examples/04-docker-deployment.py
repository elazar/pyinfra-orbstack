#!/usr/bin/env python3
"""
Docker Container Deployment Example

This example demonstrates:
- Installing Docker on an OrbStack VM
- Deploying containerized applications
- Managing Docker containers with PyInfra

Prerequisites:
- VM created: docker-vm
  orbctl create docker-vm ubuntu:22.04

Usage:
    pyinfra @orbstack/docker-vm 04-docker-deployment.py
"""

from pyinfra.operations import apt, files, server, systemd

# Update system
apt.update(
    name="Update apt cache",
    cache_time=3600,
)

# Install Docker dependencies
apt.packages(
    name="Install Docker dependencies",
    packages=[
        "apt-transport-https",
        "ca-certificates",
        "curl",
        "gnupg",
        "lsb-release",
    ],
)

# Add Docker GPG key
server.shell(
    name="Add Docker GPG key",
    commands=[
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg || true",
    ],
)

# Add Docker repository
server.shell(
    name="Add Docker repository",
    commands=[
        'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null',
    ],
)

# Update apt cache with new repository
apt.update(
    name="Update apt cache after adding Docker repo",
    cache_time=0,
)

# Install Docker
apt.packages(
    name="Install Docker",
    packages=[
        "docker-ce",
        "docker-ce-cli",
        "containerd.io",
        "docker-compose-plugin",
    ],
)

# Ensure Docker is running
systemd.service(
    name="Ensure Docker is running",
    service="docker",
    running=True,
    enabled=True,
)

# Create Docker Compose file directory
files.directory(
    name="Create app directory",
    path="/opt/webapp",
    present=True,
    mode="755",
)

# Deploy a simple Docker Compose application
files.put(
    name="Create docker-compose.yml",
    src=None,
    dest="/opt/webapp/docker-compose.yml",
    content="""version: '3.8'

services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./html:/usr/share/nginx/html
    restart: unless-stopped

  redis:
    image: redis:alpine
    restart: unless-stopped
""",
)

# Create HTML directory
files.directory(
    name="Create HTML directory",
    path="/opt/webapp/html",
    present=True,
    mode="755",
)

# Create index.html
files.put(
    name="Create index.html",
    src=None,
    dest="/opt/webapp/html/index.html",
    content="""<!DOCTYPE html>
<html>
<head>
    <title>PyInfra OrbStack Docker Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        .info { background: #ecf0f1; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Welcome to PyInfra OrbStack Docker Deployment!</h1>
    <div class="info">
        <h2>Stack Information:</h2>
        <ul>
            <li>Web Server: Nginx (Alpine)</li>
            <li>Cache: Redis (Alpine)</li>
            <li>Deployed via: PyInfra + OrbStack</li>
        </ul>
    </div>
</body>
</html>
""",
)

# Start Docker Compose services
server.shell(
    name="Start Docker Compose services",
    commands=[
        "cd /opt/webapp && docker compose up -d",
    ],
)

# Show running containers
server.shell(
    name="Show running containers",
    commands=[
        "docker ps",
    ],
)

print("✅ Docker deployment complete!")
print("   Web server: http://docker-vm.orb.local:8080")
print("")
print("Useful commands:")
print("  docker ps                    # List containers")
print("  docker compose logs -f       # View logs")
print("  docker compose down          # Stop services")
