#!/usr/bin/env python3
"""
Multi-VM Web Application Deployment

This example demonstrates:
- Using OrbStack connector with multiple VMs
- Setting up a web server on one VM
- Setting up a database on another VM
- Network connectivity between VMs using .orb.local domains

Prerequisites:
- Two VMs created: web-vm and db-vm
  orbctl create web-vm ubuntu:22.04
  orbctl create db-vm ubuntu:22.04

Usage:
    pyinfra inventories/web-stack.py 02-multi-vm-deployment.py

Create inventories/web-stack.py:
    web_server = [("@orbstack/web-vm",)]
    db_server = [("@orbstack/db-vm",)]
"""

from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

# Common setup for all hosts
apt.update(
    name="Update apt cache",
    cache_time=3600,
)

# Database Server Setup
if host.name == "db-vm":
    # Install PostgreSQL
    apt.packages(
        name="Install PostgreSQL",
        packages=["postgresql", "postgresql-contrib"],
    )

    # Start PostgreSQL
    systemd.service(
        name="Ensure PostgreSQL is running",
        service="postgresql",
        running=True,
        enabled=True,
    )

    # Create database user and database
    server.shell(
        name="Create application database",
        commands=[
            "sudo -u postgres psql -c \"CREATE USER appuser WITH PASSWORD 'changeme';\" || true",
            "sudo -u postgres createdb -O appuser appdb || true",
        ],
    )

    print(f"✅ Database server configured on {host.name}")
    print(f"   PostgreSQL accessible at: {host.name}.orb.local:5432")  # noqa: E501

# Web Server Setup
if host.name == "web-vm":
    # Install Nginx and Python
    apt.packages(
        name="Install web server packages",
        packages=[
            "nginx",
            "python3",
            "python3-pip",
            "python3-venv",
        ],
    )

    # Create web app directory
    files.directory(
        name="Create web app directory",
        path="/var/www/myapp",
        user="www-data",
        group="www-data",
        mode="755",
    )

    # Create a simple web app
    files.put(
        name="Deploy web application",
        src=None,
        dest="/var/www/myapp/app.py",
        user="www-data",
        group="www-data",
        mode="644",
        content="""#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        hostname = os.uname().nodename
        html = f'''
        <html>
        <head><title>PyInfra OrbStack Demo</title></head>
        <body>
            <h1>Hello from PyInfra OrbStack Connector!</h1>
            <p>Running on: {hostname}</p>
            <p>Database: db-vm.orb.local:5432</p>
        </body>
        </html>
        '''
        self.wfile.write(html.encode())

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), SimpleHandler)
    print('Server running on port 8080...')
    server.serve_forever()
""",
    )

    # Configure Nginx
    files.put(
        name="Configure Nginx",
        src=None,
        dest="/etc/nginx/sites-available/myapp",
        content="""server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
""",
    )

    # Enable the site
    files.link(
        name="Enable Nginx site",
        path="/etc/nginx/sites-enabled/myapp",
        target="/etc/nginx/sites-available/myapp",
    )

    # Remove default site
    files.file(
        name="Remove default Nginx site",
        path="/etc/nginx/sites-enabled/default",
        present=False,
    )

    # Restart Nginx
    systemd.service(
        name="Restart Nginx",
        service="nginx",
        restarted=True,
        enabled=True,
    )

    # Test connectivity to database
    server.shell(
        name="Test database connectivity",
        commands=[
            "nc -zv db-vm.orb.local 5432 || echo 'Database not reachable yet'",
        ],
    )

    print(f"✅ Web server configured on {host.name}")
    print(f"   Access at: http://{host.name}.orb.local")
    print("   Or from host: http://localhost (if port forwarding enabled)")

print("✅ Multi-VM deployment complete!")
print("   Web: http://web-vm.orb.local")
print("   DB:  postgresql://appuser@db-vm.orb.local:5432/appdb")
