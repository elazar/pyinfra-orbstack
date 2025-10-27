#!/usr/bin/env python3
"""
Development Environment Setup Example

This example demonstrates:
- Setting up a complete development environment
- Installing language runtimes (Python, Node.js, Go)
- Setting up development tools and editors
- Configuring shell environment

Prerequisites:
- VM created: dev-vm
  orbctl create dev-vm ubuntu:22.04

Usage:
    pyinfra @orbstack/dev-vm 05-dev-environment.py
"""

from pyinfra.operations import apt, files, server

# Update system
apt.update(
    name="Update apt cache",
    cache_time=3600,
)

apt.packages(
    name="Upgrade system packages",
    packages=[],
    upgrade=True,
)

# Install essential development tools
apt.packages(
    name="Install essential dev tools",
    packages=[
        "build-essential",
        "git",
        "curl",
        "wget",
        "unzip",
        "vim",
        "tmux",
        "htop",
        "jq",
        "tree",
        "ca-certificates",
        "gnupg",
    ],
)

# Install Python development environment
apt.packages(
    name="Install Python",
    packages=[
        "python3",
        "python3-pip",
        "python3-venv",
        "python3-dev",
    ],
)

# Install Node.js LTS
server.shell(
    name="Install Node.js",
    commands=[
        "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -",
    ],
)

apt.packages(
    name="Install Node.js package",
    packages=["nodejs"],
)

# Install Go
server.shell(
    name="Install Go",
    commands=[
        "wget -q https://go.dev/dl/go1.21.5.linux-arm64.tar.gz -O /tmp/go.tar.gz || true",
        "rm -rf /usr/local/go || true",
        "tar -C /usr/local -xzf /tmp/go.tar.gz || true",
        "rm /tmp/go.tar.gz || true",
    ],
)

# Install Docker (for containerized development)
server.shell(
    name="Install Docker convenience script",
    commands=[
        "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh",
        "sh /tmp/get-docker.sh || true",
        "rm /tmp/get-docker.sh",
    ],
)

# Create development user
server.user(
    name="Create developer user",
    user="developer",
    shell="/bin/bash",
    home="/home/developer",
)

# Add developer to docker group
server.group(
    name="Add developer to docker group",
    group="docker",
    user="developer",
    present=True,
)

# Create development directories
for directory in ["/home/developer/projects", "/home/developer/bin"]:
    files.directory(
        name=f"Create {directory}",
        path=directory,
        user="developer",
        group="developer",
        mode="755",
    )

# Configure shell environment
files.put(
    name="Configure .bashrc",
    src=None,
    dest="/home/developer/.bashrc",
    user="developer",
    group="developer",
    mode="644",
    content="""# Developer .bashrc

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# History settings
HISTCONTROL=ignoreboth
HISTSIZE=10000
HISTFILESIZE=20000
shopt -s histappend

# Colorful prompt
PS1='\\[\\033[01;32m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ '

# Enable color support
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias ll='ls -lah'

# Go environment
export GOPATH=$HOME/go
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin:$HOME/bin

# Python environment
export PYTHONDONTWRITEBYTECODE=1

# Node environment
export NODE_OPTIONS="--max-old-space-size=4096"

# Development aliases
alias gs='git status'
alias gd='git diff'
alias gp='git pull'
alias dc='docker compose'

# Useful functions
mkcd() {
    mkdir -p "$1" && cd "$1"
}

# Show system info on login
echo "Development Environment Ready!"
echo "Python: $(python3 --version)"
echo "Node: $(node --version)"
echo "Go: $(go version | cut -d' ' -f3)"
echo "Git: $(git --version)"
echo ""
""",
)

# Install common Python packages
server.shell(
    name="Install common Python packages",
    commands=[
        "pip3 install --upgrade pip",
        "pip3 install ipython pytest black flake8 mypy requests",
    ],
)

# Install common Node packages globally
server.shell(
    name="Install common Node packages",
    commands=[
        "npm install -g npm@latest",
        "npm install -g yarn pnpm typescript nodemon",
    ],
)

# Create a sample project structure
files.put(
    name="Create sample project README",
    src=None,
    dest="/home/developer/projects/README.md",
    user="developer",
    group="developer",
    mode="644",
    content="""# Development Projects

This directory is for your development projects.

## Installed Tools

- Python 3 with pip, venv
- Node.js LTS with npm, yarn, pnpm
- Go 1.21+
- Docker with Compose
- Git, tmux, vim

## Quick Start

### Python Project
```bash
cd ~/projects
python3 -m venv myproject
cd myproject
source bin/activate
pip install -r requirements.txt
```

### Node.js Project
```bash
cd ~/projects
npm init -y
npm install
```

### Go Project
```bash
cd ~/projects
mkdir mygoproject && cd mygoproject
go mod init mygoproject
```

## Useful Commands

- `gs` - git status
- `dc` - docker compose
- `ll` - detailed file listing
- `mkcd <dir>` - create and cd into directory
""",
)

# Show installed versions
server.shell(
    name="Show installed versions",
    commands=[
        "python3 --version",
        "node --version",
        "npm --version",
        "go version",
        "git --version",
        "docker --version",
    ],
)

print("✅ Development environment setup complete!")
print("")
print("Environment includes:")
print("  • Python 3 with pip, venv, ipython, pytest, black, flake8, mypy")
print("  • Node.js LTS with npm, yarn, pnpm, typescript")
print("  • Go 1.21+")
print("  • Docker with Compose")
print("  • Git, tmux, vim, and essential tools")
print("")
print("User: developer (in docker group)")
print("Home: /home/developer")
print("Projects: /home/developer/projects")
print("")
print("Connect with:")
print("  orbctl run dev-vm -- su - developer")
