# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

- Refactored connector to use PyInfra's built-in `extract_control_arguments()` utility instead of manual parameter filtering, aligning with docker, dockerssh, and chroot connectors for improved consistency and maintainability.

### Deprecated

### Removed

### Fixed

### Security

## [0.11.0] - 2025-11-02

### Fixed

- **CRITICAL**: Fixed bug introduced in v0.10.0 where connector control parameters (`_success_exit_codes`, `_timeout`, `_get_pty`, `_stdin`) were incorrectly passed to `make_unix_command_for_host()`, causing all fact gathering operations to fail with "make_unix_command() got an unexpected keyword argument '_success_exit_codes'". These parameters are now correctly filtered out before command generation and only used by the connector itself for command execution control. This restores deployment success rate from 0% to ~100%.

## [0.10.0] - 2025-11-02

### Changed

- **BREAKING (Internal)**: Refactored `run_shell_command()` to use PyInfra's standard `make_unix_command_for_host()` utility for command preparation, aligning with other PyInfra connectors (SSH, Local, Docker, Podman, Chroot, DockerSSH). This change improves consistency, maintainability, and ensures correct handling of fact gathering, shell operators, and sudo elevation. While this is an internal refactor with no expected user-visible changes, it represents a significant architectural improvement.
- Improved `test_cross_vm_connectivity_orb_local` integration test to provision and cleanup its own VMs, making it self-sufficient and more reliable. The test now gracefully skips when `.orb.local` DNS is not configured rather than failing.
- Connector test coverage improved from 90% to 93%, with 338 total tests passing.

### Fixed

- Fixed potential `TypeError` when `make_unix_command_for_host()` accesses `host.connector_data` by ensuring it's always initialized as a dictionary in the connector's `__init__` method.

## [0.9.0] - 2025-11-01

### Fixed

- **CRITICAL**: Fixed incorrect implementation of bash history expansion fix from v0.8.0. The previous fix wrapped `bash +H -c` commands in an additional `sh -c` layer, which defeated the purpose because the outer shell still interpreted `!` before passing to bash. Commands with sudo now correctly use `bash +H -c` as the outer shell wrapper, ensuring history expansion is disabled throughout the command execution chain. This fixes "command not found" errors when using `!` (logical negation) in commands with `_sudo=True`.

### Added

- Integration test (`test_connector_sudo_with_logical_negation`) that verifies the bash history expansion fix works correctly with actual VMs, ensuring commands with `!` execute properly when using sudo.

## [0.8.0] - 2025-11-01

### Fixed

- **CRITICAL**: Fixed bash history expansion causing "command not found" errors for commands containing `!` (logical negation) when used with sudo. Commands with `!` now execute correctly by using `bash +H` to disable history expansion.

## [0.7.0] - 2025-11-01

### Fixed

- **CRITICAL**: Fixed sudo operations not working with PyInfra's underscore-prefixed arguments (`_sudo`, `_sudo_user`)
- Fixed single-bit `StringCommand` sudo wrapping to prevent "command not found" errors with shell operators
- All three methods (`run_shell_command()`, `put_file()`, `get_file()`) now check for both prefixed and non-prefixed argument versions

### Changed

- Single-bit StringCommand objects with sudo now wrap in `sh -c` before applying sudo for correct execution
- Complex shell commands with operators (`||`, `&&`, pipes, timeouts) now work correctly with sudo

## [0.6.0] - 2025-11-01

### Added

- Add sudo support to `put_file()` for uploading files to protected locations
- Add sudo support to `get_file()` for downloading files from protected locations
- Add `mode` parameter to `put_file()` for setting custom file permissions
- Add 18 new comprehensive unit tests for file operations and coverage improvements

### Changed

- File operations now use two-stage approach with temp files when sudo is required
- Test coverage improved from 87% to 93% with low-effort coverage tests
- Total test count increased to 60 tests (all passing)

### Fixed

- File operations now handle permission errors gracefully with detailed logging
- Temp file cleanup failures no longer cause operations to fail

## [0.5.0] - 2025-11-01

### Added

- Add sudo and sudo_user argument support to `run_shell_command()` for operations requiring elevated privileges
- Support for running commands as specific users via `_sudo_user` parameter
- Safe command quoting with `shlex.quote()` for special characters
- Comprehensive test suite with 9 new sudo-specific unit tests covering all command types

### Changed

- Connector coverage improved from 28% to 94% with new sudo tests
- Total test count increased to 42 tests (all passing)

## [0.4.0] - 2025-11-01

### Fixed

- Connector now wraps shell commands in `sh -c` to properly support shell features (pipes, boolean operators, redirections). Plain strings and single-bit StringCommand objects are now wrapped, while multi-bit commands pass through unchanged.

## [0.3.0] - 2025-10-31

### Fixed

- Connector now properly handles `StringCommand` objects by extracting individual arguments from `.bits` attribute, fixing PyInfra facts that use `sh -c` command wrappers

## [0.2.0] - 2025-10-31

### Fixed

- Connector now passes shell commands as single string to `orbctl run` instead of splitting on whitespace, fixing commands with quotes and special characters

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

[Unreleased]: https://github.com/elazar/pyinfra-orbstack/compare/v0.11.0...HEAD
[0.11.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/elazar/pyinfra-orbstack/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/elazar/pyinfra-orbstack/releases/tag/v0.1.0
