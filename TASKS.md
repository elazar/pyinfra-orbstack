# PyInfra OrbStack Connector Development Tasks

**Project:** pyinfra-orbstack
**Date:** 2025-10-23
**Status:** Phase 3 Complete - Ready for Phase 4 or Next Priority
**Current Version:** 0.1.0

## Overview

This document outlines the iterative progressive tasks for developing a custom PyInfra
connector for OrbStack VM management. The development follows a phased approach with
incremental functionality and comprehensive testing at each stage. The final goal
is to publish this as a reusable Python package on PyPI.

## Development Phases

### Phase 1: Foundation and Core Infrastructure

#### Task 1.1: Project Setup and Structure

- [x] **1.1.1** Create project directory structure
  - [x] Initialize `pyinfra-orbstack/` package directory
  - [x] Create `src/pyinfra_orbstack/` module structure
  - [x] Set up `tests/` directory with test structure
  - [x] Create `docs/` directory for documentation

- [x] **1.1.2** Initialize Python package configuration
  - [x] Create `pyproject.toml` with proper metadata for PyPI publishing
  - [x] Configure entry points for PyInfra connector registration
  - [x] Set up development dependencies (pytest, black, flake8, mypy)
  - [x] Configure build system (hatchling or setuptools)
  - [x] Add package classifiers for PyPI (Python versions, OS, etc.)
  - [x] Configure package keywords and description for PyPI discovery

- [x] **1.1.3** Set up development environment
  - [x] Create virtual environment with `uv`
  - [x] Install development dependencies with `uv sync --dev`
  - [x] Configure pre-commit hooks
  - [x] Set up CI/CD pipeline configuration
  - [x] Configure PyPI publishing workflow in CI/CD

#### Task 1.2: Basic Connector Framework

- [x] **1.2.1** Create base connector class
  - [x] Implement `OrbStackConnector` class inheriting from `BaseConnector`
  - [x] Set `handles_execution = True`
  - [x] Add proper type hints and docstrings
  - [x] Implement basic error handling structure

- [x] **1.2.2** Implement static `make_names_data` method
  - [x] Create method signature with optional hostname parameter
  - [x] Implement `orbctl list -f json` command execution
  - [x] Parse JSON output and extract VM information
  - [x] Generate host data tuples with proper group assignment
  - [x] Add error handling for CLI failures and JSON parsing

- [x] **1.2.3** Implement basic connection management
  - [x] Create `connect()` method for VM verification
  - [x] Implement `disconnect()` method for cleanup
  - [x] Add VM existence and accessibility checks
  - [x] Handle VM startup for non-running VMs

#### Task 1.3: Core Command Execution

- [x] **1.3.1** Implement `run_shell_command` method
  - [x] Create method signature matching PyInfra requirements
  - [x] Build `orbctl run` command with proper arguments
  - [x] Handle user specification with `-u` flag
  - [x] Handle working directory with `-w` flag
  - [x] Implement command execution with timeout support
  - [x] Return proper `CommandOutput` objects

- [x] **1.3.2** Add file transfer capabilities
  - [x] Implement `put_file` method using `orbctl push`
  - [x] Implement `get_file` method using `orbctl pull`
  - [x] Handle file path validation and error cases
  - [x] Add progress reporting for large file transfers

#### Task 1.4: Entry Point Registration

- [x] **1.4.1** Configure PyInfra connector registration
  - [x] Add entry point in `pyproject.toml`
  - [x] Test connector discovery by PyInfra
  - [x] Verify `@orbstack` connector availability
  - [x] Create basic usage documentation

#### Task 1.5: Enhanced Unit Testing with Realistic Mocks

- [x] **1.5.1** Expand unit tests with comprehensive OrbStack CLI mocks
  - [x] Create realistic OrbStack CLI response mocks
  - [x] Test VM listing with various JSON responses
  - [x] Test VM connection scenarios (running, stopped, non-existent)
  - [x] Test command execution with different parameters
  - [x] Test file transfer operations
  - [x] Test error handling and edge cases
  - [x] Achieve 100% connector coverage with 80 test cases

#### Task 1.6: Integration Testing Framework

- [x] **1.6.1** Create integration tests with OS and OrbStack detection
  - [x] Implement OS detection (macOS required)
  - [x] Implement OrbStack availability detection
  - [x] Create tests that run automatically when conditions are met
  - [x] Test real OrbStack CLI interactions
  - [x] Test VM lifecycle operations
  - [x] Test file transfer operations
  - [x] Test error handling and edge cases

### Phase 2: VM Lifecycle Operations ✅ **COMPLETED**

#### Task 2.1: VM Management Operations

- [x] **2.1.1** Create VM lifecycle operations module ✅ **COMPLETED**
  - [x] Create `operations/vm.py` module
  - [x] Implement `vm_create` operation with image and arch support
  - [x] Implement `vm_delete` operation with force option
  - [x] Implement `vm_start`, `vm_stop`, `vm_restart` operations
  - [x] Add proper operation decorators and documentation

- [x] **2.1.2** Implement VM cloning and export operations ✅ **COMPLETED**
  - [x] Create `vm_clone` operation for VM duplication
  - [x] Implement `vm_export` and `vm_import` operations
  - [x] Add `vm_rename` operation for changing VM names
  - [x] Handle VM configuration preservation (via export/import)

#### Task 2.2: VM Information Operations

- [x] **2.2.1** Create VM information retrieval operations ✅ **COMPLETED**
  - [x] Implement `vm_info` operation for detailed VM data
  - [x] Create `vm_list` operation for all VMs
  - [x] Implement `vm_status` operation for current state
  - [x] Add `vm_ip` operation for network information

- [x] **2.2.2** Implement network information operations ✅ **COMPLETED**
  - [x] Create `vm_network_info` operation
  - [x] Add IP address retrieval (IPv4/IPv6)
  - [x] Implement MAC address extraction (via vm_info)
  - [x] Add network interface information

#### Task 2.3: SSH Configuration Operations

- [x] **2.3.1** Implement SSH information operations ✅ **COMPLETED**
  - [x] Create `ssh_info` operation for connection details
  - [x] Implement `ssh_connect_string` operation
  - [x] SSH operations use orbctl info and orbctl ssh commands
  - [x] Operations properly integrated with PyInfra context

#### Phase 2 Completion Summary

**Completed:** 2025-10-23

**Deliverables:**

- ✅ 16 VM lifecycle operations (create, delete, start, stop, restart, clone, export, import, rename)
- ✅ 5 VM information operations (info, list, status, ip, network_info)
- ✅ 2 SSH configuration operations (ssh_info, ssh_connect_string)
- ✅ 12 testable command builder functions (refactored for better coverage)
- ✅ 208 comprehensive tests (unit, integration, E2E)
- ✅ 94% overall test coverage (100% for testable code)
- ✅ Documentation updates (README, CHANGELOG, testing methodology)
- ✅ Coverage configuration optimized for PyInfra decorators

**Key Achievements:**

- Implemented command builder pattern to separate testable logic from decorators
- Achieved 100% coverage for all command construction logic
- Added centralized coverage exclusion configuration
- Comprehensive integration and E2E test suites validate all operations

**Commits:**

- `728e82e` - feat: add Phase 2 VM operations (clone, export, import, rename, SSH)
- `fed1107` - refactor: extract command builders to improve test coverage
- `0e31fe0` - build: configure coverage to exclude @operation decorator code

### Phase 3: Enhanced VM Operations ✅ **COMPLETED**

**Note:** Phase 3 was redesigned based on ADR-002 feasibility analysis.
See `docs/20251023-phase3-feasibility-analysis.md` for detailed rationale.

#### Task 3.1: VM Networking Information Operations ✅ **COMPLETED**

- [x] **3.1.1** Implement comprehensive network information operations
  - [x] Create `vm_network_details()` operation for comprehensive network info
  - [x] Implement `vm_test_connectivity()` with ping/curl/nc methods
  - [x] Add `vm_dns_lookup()` operation for DNS resolution (A, AAAA, MX, CNAME)
  - [x] Support for OrbStack .orb.local domains
  - [x] Cross-VM communication testing capabilities

#### Task 3.2: Global Configuration Management ✅ **COMPLETED**

- [x] **3.2.1** Implement OrbStack configuration operations
  - [x] Create `orbstack_config_get()` for retrieving configuration values
  - [x] Implement `orbstack_config_set()` for updating configuration
  - [x] Add `orbstack_config_show()` for displaying all settings
  - [x] Create `vm_username_set()` for per-VM username configuration
  - [x] Document global vs. per-VM configuration limitations

#### Task 3.3: VM Logging and Diagnostics ✅ **COMPLETED**

- [x] **3.3.1** Implement VM troubleshooting operations
  - [x] Create `vm_logs()` operation for system log retrieval
  - [x] Implement `vm_status_detailed()` for comprehensive status
  - [x] Add support for detailed debugging logs (--all flag)
  - [x] Document distinction between OrbStack-level and in-VM logs

#### Phase 3 Completion Summary

**Completed:** 2025-10-23

**Deliverables:**

- ✅ 9 Phase 3 operations (3 networking + 4 config + 2 diagnostics)
- ✅ 7 command builder functions
- ✅ 37 comprehensive unit tests (29 new Phase 3 tests)
- ✅ 12 integration tests for Phase 3 operations
- ✅ 100% test coverage maintained on vm.py
- ✅ Comprehensive README documentation for all Phase 3 operations
- ✅ ADR-002 documenting feasibility analysis and redesign decisions

**Key Achievements:**

- Redesigned Phase 3 based on OrbStack CLI capabilities and PyInfra architecture
- Implemented all feasible operations from ADR-002
- Maintained 100% coverage on operations/vm.py (75 total tests passing)
- Comprehensive documentation distinguishing OrbStack vs. PyInfra responsibilities

**Commits:**

- `54298a3` - feat: implement Phase 3A - VM Networking Information Operations
- `51cb522` - feat: implement Phase 3C - VM Logging and Diagnostics
- `b1ba052` - feat: implement Phase 3B configuration management operations
- `f59d346` - docs: add ADR-002 Phase 3 feasibility analysis

**Original Phase 3 Tasks (Not Implemented - See ADR-002):**

The following tasks from the original Phase 3 specification were determined to be
infeasible or architecturally inappropriate during the ADR-002 analysis:

- ❌ VM-to-VM file transfer operations (not supported by OrbStack CLI)
- ❌ Per-VM resource management (OrbStack uses global resource pool)
- ❌ Network interface configuration (auto-configured by OrbStack)
- ❌ Custom VM parameters beyond username (not supported by OrbStack CLI)

These operations either:

1. Are not supported by OrbStack CLI
2. Conflict with PyInfra's architectural model
3. Are better served by standard PyInfra operations

See ADR-002 for complete analysis and recommendations.

### Phase 4: Testing and Validation

#### Task 4.1: Unit Testing Framework

- [ ] **4.1.1** Set up comprehensive test suite
  - [ ] Create test fixtures for OrbStack CLI mocking
  - [ ] Implement unit tests for all connector methods
  - [ ] Add tests for operation modules
  - [ ] Create test utilities for VM state simulation

- [ ] **4.1.2** Implement error scenario testing
  - [ ] Test VM not found scenarios
  - [ ] Test CLI command failures
  - [ ] Test network connectivity issues
  - [ ] Test file transfer failures

#### Task 4.2: Integration Testing

- [ ] **4.2.1** Create integration test environment
  - [ ] Set up test VMs with different distributions
  - [ ] Implement automated VM lifecycle testing
  - [ ] Create cross-VM communication tests
  - [ ] Add performance benchmarking tests

- [ ] **4.2.2** Implement real-world scenario testing
  - [ ] Test with various PyInfra deployment configurations
  - [ ] Validate migration from current CLI approach
  - [ ] Test concurrent operations on multiple VMs
  - [ ] Verify error recovery and retry mechanisms

#### Task 4.3: Compatibility Testing

- [ ] **4.3.1** Test OrbStack version compatibility
  - [ ] Test with different OrbStack versions
  - [ ] Validate CLI command compatibility
  - [ ] Test with various Linux distributions
  - [ ] Verify architecture support (arm64/amd64)

### Phase 5: Documentation and Examples

#### Task 5.1: Comprehensive Documentation

- [ ] **5.1.1** Create user documentation
  - [ ] Write installation and setup guide
  - [ ] Create usage examples and tutorials
  - [ ] Document all operations and their parameters
  - [ ] Add troubleshooting guide

- [ ] **5.1.2** Create developer documentation
  - [ ] Document connector architecture
  - [ ] Create contribution guidelines
  - [ ] Add API reference documentation
  - [ ] Document testing procedures

#### Task 5.2: Migration Guide and Examples

- [ ] **5.2.1** Create migration documentation
  - [ ] Document migration from current CLI approach
  - [ ] Provide step-by-step migration guide
  - [ ] Create before/after code examples
  - [ ] Add performance comparison documentation

- [ ] **5.2.2** Create practical examples
  - [ ] Implement common PyInfra deployment examples
  - [ ] Create multi-VM deployment examples
  - [ ] Add network configuration examples
  - [ ] Create monitoring and maintenance examples

### Phase 6: Performance Optimization and Advanced Features

#### Task 6.1: Performance Optimization

- [ ] **6.1.1** Implement caching and state management
  - [ ] Add intelligent caching for VM information
  - [ ] Implement incremental fact gathering
  - [ ] Optimize connection pooling
  - [ ] Add batch operation support

- [ ] **6.1.2** Add performance monitoring
  - [ ] Implement operation timing and metrics
  - [ ] Add resource usage monitoring
  - [ ] Create performance benchmarking tools
  - [ ] Implement optimization recommendations

#### Task 6.2: Advanced Features

- [ ] **6.2.1** Implement advanced VM management
  - [ ] Add VM snapshot management
  - [ ] Implement VM backup and restore
  - [ ] Create VM migration utilities
  - [ ] Add advanced networking features

- [ ] **6.2.2** Create monitoring and alerting
  - [ ] Implement VM health monitoring
  - [ ] Add automated alerting capabilities
  - [ ] Create dashboard integration
  - [ ] Implement log aggregation

### Phase 7: PyPI Publishing and Distribution

#### Task 7.1: Package Preparation for PyPI

- [ ] **7.1.1** Finalize package metadata
  - [ ] Review and update package description for PyPI
  - [ ] Add comprehensive package classifiers
  - [ ] Include license information and project URLs
  - [ ] Add author and maintainer information
  - [ ] Configure long description from README

- [ ] **7.1.2** Prepare distribution files
  - [ ] Create comprehensive README.md with installation and usage
  - [ ] Add `CHANGELOG.md` for version history
  - [ ] Include LICENSE file
  - [ ] Add `MANIFEST.in` for additional files
  - [ ] Create `setup.py` if needed for compatibility

#### Task 7.2: PyPI Publishing Setup

- [ ] **7.2.1** Configure PyPI publishing tools
  - [ ] Set up build tools (build, twine)
  - [ ] Configure PyPI API tokens and credentials
  - [ ] Test publishing to TestPyPI
  - [ ] Set up automated version management

- [ ] **7.2.2** Implement automated publishing
  - [ ] Configure GitHub Actions for PyPI publishing
  - [ ] Set up automated version bumping
  - [ ] Add publishing on release tags
  - [ ] Implement pre-release testing workflow

#### Task 7.3: Post-Publishing Tasks

- [ ] **7.3.1** Documentation and marketing
  - [ ] Create PyPI project page content
  - [ ] Add badges for build status, coverage, etc.
  - [ ] Create social media announcements
  - [ ] Update project documentation with PyPI installation

- [ ] **7.3.2** Community engagement
  - [ ] Create GitHub repository with issues template
  - [ ] Set up contribution guidelines
  - [ ] Add code of conduct
  - [ ] Create release notes template

## Testing Strategy

### Unit Testing

- **Coverage Target:** 90%+ code coverage
- **Test Types:** Connector methods, operations, utilities
- **Mocking:** OrbStack CLI commands and responses
- **Error Scenarios:** All failure modes and edge cases

### Integration Testing

- **Environment:** Real OrbStack VMs with multiple distributions
- **Scenarios:** Complete VM lifecycle, cross-VM communication
- **Performance:** Concurrent operations, large file transfers
- **Compatibility:** Different OrbStack versions and architectures

### End-to-End Testing

- **Real-world Usage:** PyInfra deployment integration
- **Migration Testing:** From current CLI approach
- **Stress Testing:** Multiple VMs, concurrent operations
- **Recovery Testing:** Error scenarios and recovery procedures

## Quality Assurance

### Code Quality

- **Linting:** Black, flake8, mypy compliance
- **Documentation:** Complete docstrings and type hints
- **Security:** Input validation and sanitization
- **Error Handling:** Comprehensive error handling and logging

### Performance Requirements

- **Response Time:** VM operations under 5 seconds
- **Throughput:** Support for 10+ concurrent VMs
- **Resource Usage:** Minimal memory and CPU overhead
- **Scalability:** Linear performance with VM count

### Compatibility Requirements

- **OrbStack Versions:** Support for current and recent versions
- **Python Versions:** Python 3.8+ compatibility
- **PyInfra Versions:** Support for current PyInfra releases
- **Operating Systems:** macOS (primary), Linux (secondary)
- **PyPI Compatibility:** Follow PyPI packaging standards and best practices

## Success Criteria

### Functional Requirements

- [ ] All VM lifecycle operations working correctly
- [ ] Cross-VM communication functional
- [ ] File transfer operations reliable
- [ ] SSH integration working properly
- [ ] Error handling robust and informative

### Performance Success Criteria

- [ ] VM operations complete within acceptable timeframes
- [ ] Memory usage remains reasonable with multiple VMs
- [ ] Concurrent operations work without conflicts
- [ ] File transfers handle large files efficiently

### Quality Requirements

- [ ] 90%+ test coverage achieved
- [ ] All linting checks passing
- [ ] Documentation complete and accurate
- [ ] Migration guide enables smooth transition

### User Experience Requirements

- [ ] Intuitive operation interface
- [ ] Clear error messages and debugging information
- [ ] Comprehensive examples and documentation
- [ ] Smooth integration with existing PyInfra workflows
- [ ] Easy installation via `uv add` from PyPI
- [ ] Clear PyPI project page with usage examples

## Risk Mitigation

### Technical Risks

- **OrbStack CLI Changes:** Monitor OrbStack updates and maintain compatibility
- **PyInfra API Changes:** Stay current with PyInfra releases and adapt as needed
- **Performance Issues:** Implement monitoring and optimization strategies
- **Compatibility Issues:** Test with multiple environments and versions

### Project Risks

- **Timeline Delays:** Implement iterative development with regular milestones
- **Scope Creep:** Maintain focus on core functionality in early phases
- **Quality Issues:** Implement comprehensive testing and review processes
- **Documentation Gaps:** Prioritize documentation alongside development

## Dependencies

### External Dependencies

- **OrbStack:** Must be installed and configured on target systems
- **PyInfra:** Compatible version required for connector integration
- **Python:** 3.8+ with standard library modules

### Internal Dependencies

- **Development Environment:** Proper setup with all tools and dependencies
- **Testing Infrastructure:** Access to OrbStack VMs for integration testing
- **Documentation Tools:** Markdown processing and documentation generation

## Next Steps

1. **Review and approve this task plan**
2. **Set up development environment**
3. **Begin Phase 1 implementation**
4. **Establish regular progress reviews**
5. **Create detailed task tracking system**
6. **Plan PyPI publishing strategy and timeline**

---

**Note:** This task plan is iterative and may be adjusted based on development progress,
feedback, and changing requirements. Each phase builds upon the previous one, ensuring
a solid foundation before adding complexity.
