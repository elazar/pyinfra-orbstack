# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2025-10-29

Initial public release of PyInfra OrbStack Connector.

### Added

- **Core Connector:**
  - OrbStackConnector class with PyInfra integration
  - Automatic VM discovery and grouping (@orbstack connector)
  - File transfer capabilities (put_file, get_file)
  - Command execution with user and working directory support

- **VM Lifecycle Operations (16 operations):**
  - VM creation with image and architecture support
  - VM deletion with force option
  - VM start, stop, and restart operations
  - VM cloning for instant duplication
  - VM export/import for backup and restore
  - VM rename operation

- **VM Information Operations (5 operations):**
  - Detailed VM information retrieval
  - VM listing with status
  - VM status checking
  - IP address retrieval (IPv4/IPv6)
  - Network information extraction

- **VM Networking Operations (3 operations):**
  - Comprehensive network details
  - Cross-VM connectivity testing (ping, curl, nc)
  - DNS lookup with multiple record types

- **Configuration Management (4 operations):**
  - Global OrbStack configuration get/set/show
  - Per-VM username configuration
  - Documentation of global vs per-VM settings

- **Diagnostics Operations (2 operations):**
  - VM system logs retrieval
  - Detailed VM status with comprehensive information

- **SSH Operations (2 operations):**
  - SSH connection information
  - SSH connection string generation

- **Timing Utility:**
  - Simple timing context manager and decorator
  - Standard Python logging integration
  - Operation performance monitoring

- **Testing:**
  - 287 comprehensive tests (100% pass rate)
  - 99% code coverage (210/211 statements)
  - Unit, integration, and E2E test suites
  - Session-scoped worker VM management
  - Performance benchmarking infrastructure

- **Documentation:**
  - Comprehensive README with badges and all operations documented
  - CONTRIBUTING.md with detailed development guidelines
  - User guide: compatibility, troubleshooting, migration, known limitations, timing
  - 5 practical deployment examples
  - 7 Architecture Decision Records (ADRs)
  - Complete API documentation with examples

- **Development Infrastructure:**
  - PyPI packaging configuration
  - CI/CD pipeline with GitHub Actions
  - Automated PyPI publishing on release
  - Pre-commit hooks (black, flake8, mypy, isort)
  - Python 3.9-3.12 compatibility testing

### Changed

- Refactored package structure from `pyinfra.orbstack` to `pyinfra_orbstack` to avoid namespace conflicts
- Updated all import statements and entry points to use correct namespace
- Migrated documentation to prioritize `uv` package manager with `pip` alternatives
- Extracted command builders from operations for better testability
- Downgraded isort to 5.13.2 for Python 3.9 compatibility

### Fixed

- Python 3.9 compatibility issues with isort
- All Python 3.8 references updated to Python 3.9
- E2E tests now skip gracefully when orbctl is not available
- VM creation timeout handling with proper string matching
- Worker VM reuse for 40% faster test execution

[Unreleased]: https://github.com/elazar/pyinfra-orbstack/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/elazar/pyinfra-orbstack/releases/tag/v0.1.0
