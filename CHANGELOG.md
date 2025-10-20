# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project structure and setup
- Basic OrbStackConnector class with PyInfra integration
- VM lifecycle operations (create, delete, start, stop, restart)
- VM information operations (info, list, status, ip, network_info)
- File transfer capabilities (put_file, get_file)
- Command execution with user and working directory support
- Automatic VM discovery and grouping
- Comprehensive test suite with mocking
- PyPI packaging configuration
- Documentation and examples
- Development standards documentation (Semantic Versioning, Conventional Commits, Keep a Changelog)
- Architecture Decision Records (ADRs) system with documentation index

### Changed

- Refactored package structure from `pyinfra.orbstack` to `pyinfra_orbstack` to avoid namespace conflicts
- Updated all import statements and entry points to use correct namespace
- Migrated documentation to prioritize `uv` package manager with `pip` alternatives
- Consolidated development documentation and reduced redundancy across project files

### Deprecated

- N/A

### Removed

- N/A

### Fixed

- N/A

### Security

- N/A
