# Contributing to PyInfra OrbStack Connector

Thank you for considering contributing to the PyInfra OrbStack Connector! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Code Review Process](#code-review-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you are expected to:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on what is best for the community and project
- Show empathy towards other community members

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **macOS** (OrbStack's primary platform)
- **[OrbStack](https://orbstack.dev/)** 2.0.0+ installed and running
- **Python** 3.9 or higher
- **[uv](https://github.com/astral-sh/uv)** package manager (recommended) or [pip](https://pip.pypa.io/)
- **[Git](https://git-scm.com/)** for version control

### Finding Ways to Contribute

- **Bug Reports:** Open an issue describing the problem
- **Feature Requests:** Open an issue describing the desired functionality
- **Documentation:** Improve existing docs or add missing documentation
- **Code:** Fix bugs, implement features, or improve performance
- **Testing:** Add test coverage or improve test infrastructure

For common issues and solutions, see the [Troubleshooting Guide](docs/user-guide/troubleshooting.md).

Check the [GitHub Issues](https://github.com/yourusername/pyinfra-orbstack/issues) for:
- Issues labeled `good first issue` for newcomers
- Issues labeled `help wanted` for community contributions
- Issues labeled `documentation` for documentation improvements

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/elazar/pyinfra-orbstack.git
cd pyinfra-orbstack

# Add upstream remote
git remote add upstream https://github.com/elazar/pyinfra-orbstack.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
uv venv
# or:
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows (if OrbStack ever supports it)

# Install dependencies
uv sync --dev
# or:
pip install -e ".[dev]"
```

### 3. Verify Setup

```bash
# Run tests to verify everything works
pytest

# Check code formatting
black --check src/ tests/

# Run linter
flake8 src/ tests/

# Run type checker
mypy src/
```

### 4. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or:
git checkout -b fix/your-bug-fix
```

## Making Changes

### Code Style

This project follows standard Python conventions:

- **[PEP 8](https://peps.python.org/pep-0008/):** Python style guide
- **[Black](https://black.readthedocs.io/):** Code formatter (line length: 88)
- **[Type Hints](https://docs.python.org/3/library/typing.html):** Use type annotations for all functions
- **[Docstrings](https://peps.python.org/pep-0257/):** Document all public functions, classes, and modules

**Example:**

```python
from typing import Optional


def example_function(param1: str, param2: int) -> Optional[dict]:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")

    return {"result": param1 * param2}
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no functional changes)
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**

```bash
feat(vm): add vm_snapshot operation for VM backups

fix(connector): handle SSH connection timeout gracefully

docs: update installation guide with troubleshooting steps

test: add integration tests for vm_clone operation

refactor(operations): extract command builders to separate module
```

### Adding New Features

1. **Check existing functionality:**
   - Review current operations in `src/pyinfra_orbstack/operations/vm.py`
   - Check if feature can be implemented with existing operations

2. **Verify OrbStack support:**
   - Test with `orbctl` command directly
   - Document any OrbStack limitations (see [Known Limitations](docs/user-guide/known-limitations.md))

3. **Implement feature:**
   - Add operation to appropriate module
   - Use `@operation` decorator correctly
   - Follow existing patterns (see command builders)

4. **Add tests:**
   - Unit tests for command construction
   - Integration tests with real OrbStack (if applicable)
   - E2E tests for PyInfra integration

5. **Document feature:**
   - Add docstring with examples
   - Update `README.md` operations section
   - Add to `CHANGELOG.md` under "Unreleased"

### Fixing Bugs

1. **Reproduce the bug:**
   - Create a minimal test case
   - Document the expected vs. actual behavior

2. **Write a failing test:**
   - Add test that demonstrates the bug
   - Verify test fails before fix

3. **Implement the fix:**
   - Make minimal changes to fix the issue
   - Avoid refactoring in bug fix commits

4. **Verify the fix:**
   - Ensure new test passes
   - Run full test suite
   - Test manually if needed

5. **Document the fix:**
   - Update `CHANGELOG.md` under "Unreleased" → "Fixed"
   - Reference GitHub issue in commit message

## Testing

### Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
├── test_connector.py              # Connector unit tests
├── test_vm_command_builders.py    # Command builder tests
├── test_vm_operations_unit.py     # Operation unit tests
├── test_vm_operations_integration.py  # Integration tests
├── test_pyinfra_operations_e2e.py # End-to-end tests
└── test_utils.py                  # Test utilities
```

### Running Tests

See also: [Testing Guide](docs/README.md#testing-documentation) for more detailed information.

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_connector.py

# Run specific test
pytest tests/test_connector.py::test_make_names_data_basic

# Run with coverage
pytest --cov=src --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"

# Run with verbose output
pytest -vv
```

For more on pytest, see the [official pytest documentation](https://docs.pytest.org/).

### Writing Tests

**Unit Tests:**

```python
def test_vm_create_command_basic():
    """Test basic VM creation command construction."""
    from pyinfra_orbstack.operations.vm import _build_vm_create_command

    cmd = _build_vm_create_command("test-vm", "ubuntu:22.04")

    assert cmd == ["orbctl", "create", "test-vm", "ubuntu:22.04"]
```

**Integration Tests:**

```python
import pytest


@pytest.mark.integration
def test_vm_lifecycle_integration(worker_vm):
    """Test complete VM lifecycle with real OrbStack."""
    vm_name = worker_vm  # Reuse worker VM fixture

    # Test operations
    result = subprocess.run(
        ["orbctl", "info", vm_name],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
```

**E2E Tests:**

```python
def test_pyinfra_vm_info_operation():
    """Test vm_info operation via PyInfra deployment."""
    # Create deployment script
    deploy_content = """
from pyinfra_orbstack.operations.vm import vm_info

vm_data = vm_info()
print(f"VM State: {vm_data.get('record', {}).get('state')}")
"""
    # Execute with PyInfra
    # Verify results
```

### Test Coverage Requirements

- **Overall:** 80% minimum coverage
- **New code:** 90% minimum coverage
- **Command builders:** 100% coverage (testable logic)

### Test Best Practices

- **Independent:** Tests should not depend on each other
- **Fast:** Unit tests should run in milliseconds
- **Descriptive:** Test names should describe what they test
- **Focused:** Test one logical behavior per test (multiple related assertions are fine)
- **Cleanup:** Always clean up test resources

## Documentation

### Types of Documentation

1. **Code Documentation:**
   - Docstrings for all public functions/classes
   - Type hints for all function parameters and returns
   - Inline comments for complex logic

2. **User Documentation:**
   - `README.md` - Overview and quick start
   - `docs/user-guide/` - Installation, usage, troubleshooting
   - `examples/` - Practical examples

3. **Developer Documentation:**
   - `CONTRIBUTING.md` - This file
   - `docs/dev-journal/` - Implementation notes
   - `docs/adrs/` - [Architecture decisions](https://github.com/joelparkerhenderson/architecture-decision-record)

### Documentation Standards

- **[Markdown](https://github.github.com/gfm/):** All documentation in Markdown format
- **Examples:** Include code examples with output
- **Links:** Use relative links for internal documentation
- **Up-to-date:** Update docs with code changes

### Updating Documentation

When adding or changing features:

1. **Update docstrings** in code
2. **Update `README.md`** if public API changes
3. **Add examples** to `examples/` directory if helpful (see [Migration Guide](docs/user-guide/migration-guide.md) for examples)
4. **Update user guide** for significant features
5. **Add changelog entry** to `CHANGELOG.md`

## Submitting Changes

### Pre-Submission Checklist

Before opening a pull request:

- [ ] All tests pass: `pytest`
- [ ] Code is formatted: `black src/ tests/`
- [ ] No linting errors: `flake8 src/ tests/`
- [ ] Type checking passes: `mypy src/`
- [ ] Documentation is updated
- [ ] `CHANGELOG.md` is updated
- [ ] Commits follow conventional commit format
- [ ] Branch is up to date with the `main` git branch

### Opening a Pull Request

1. **Push your branch:**

```bash
git push origin feature/your-feature-name
```

2. **Create Pull Request on GitHub:**
   - Provide clear title and description
   - Reference related issues
   - Describe changes and rationale
   - Include screenshots/examples if applicable

3. **PR Description Template:**

```markdown
## Description

Brief description of the changes.

## Related Issues

Fixes #123
Related to #456

## Changes

- Added X feature
- Fixed Y bug
- Updated Z documentation

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist

- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] CHANGELOG.md updated
```

## Code Review Process

### What to Expect

- **Initial Review:** Within 1-2 weeks
- **Feedback:** Constructive comments and suggestions
- **Iterations:** May require changes before merge
- **Approval:** At least one maintainer approval required

### Review Criteria

Reviewers will check for:

- **Correctness:** Does the code work as intended?
- **Quality:** Is the code well-written and maintainable?
- **Tests:** Is there adequate test coverage?
- **Documentation:** Are changes documented?
- **Style:** Does it follow project conventions?
- **Impact:** Are there any breaking changes?

### Responding to Feedback

- **Be respectful:** Remember reviewers are helping improve the code
- **Ask questions:** If feedback is unclear, ask for clarification
- **Explain decisions:** Provide context for your choices
- **Make changes:** Address feedback promptly
- **Update PR:** Push changes to the same branch

## Release Process

### Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR:** Incompatible API changes
- **MINOR:** New functionality (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

### Release Workflow

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release date
3. Create release commit: `chore: release v0.2.0`
4. Tag release: `git tag v0.2.0`
5. Push to GitHub: `git push && git push --tags`
6. [GitHub Actions](https://docs.github.com/en/actions) builds and publishes to [PyPI](https://pypi.org/)

## Development Tips

### Useful Commands

```bash
# Format all code
black .

# Check what would be formatted
black --check .

# Run linter
flake8 .

# Run type checker
mypy src/

# Run tests with coverage
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
```

### Debugging

```bash
# Run single test with output
pytest -s tests/test_file.py::test_function

# Drop into debugger on failure
pytest --pdb

# Run with verbose OrbStack output
ORBCTL_DEBUG=1 pytest tests/test_integration.py
```

### Testing Against Real OrbStack

For OrbStack compatibility and version information, see the [Compatibility Matrix](docs/user-guide/compatibility.md).

```bash
# Create test VM for manual testing
orbctl create test-dev-vm ubuntu:22.04

# Test operations manually
python -c "
from pyinfra_orbstack.operations.vm import vm_info
data = vm_info()
print(data)
"

# Clean up
orbctl delete test-dev-vm
```

## Architectural Decisions

When making significant architectural changes, document them as ADRs:

- **Location:** `docs/adrs/`
- **Format:** `NNNN-decision-title.md` (e.g., `0007-caching-strategy.md`)
- **Template:** Follow [Michael Nygard ADR template](https://github.com/joelparkerhenderson/architecture-decision-record#decision-record-template-by-michael-nygard)

### Existing ADRs to Review

Before proposing architectural changes, review existing decisions:

- [ADR-0001: Package Namespace Structure](docs/adrs/0001-package-namespace.md)
- [ADR-0002: Scope Limitation for Advanced Operations](docs/adrs/0002-advanced-operations-scope.md)
- [ADR-0003: Multi-Level Testing Strategy](docs/adrs/0003-multi-level-testing-strategy.md)
- [ADR-0004: Session-Scoped Test VM Management](docs/adrs/0004-session-scoped-test-vms.md)
- [ADR-0005: Intelligent Retry Logic for OrbStack Operations](docs/adrs/0005-intelligent-retry-logic.md)
- [ADR-0006: PyInfra Operation Generator Pattern with Command Builders](docs/adrs/0006-operation-generator-pattern.md)

See [Architecture Decision Records](docs/adrs/README.md) for the complete list.

## Getting Help

- **[Documentation](docs/README.md):** Check `docs/` directory first
- **[Architecture Decision Records](docs/adrs/README.md):** Understand key architectural decisions
- **[GitHub Issues](https://github.com/elazar/pyinfra-orbstack/issues):** Search existing issues
- **[GitHub Discussions](https://github.com/elazar/pyinfra-orbstack/discussions):** Ask questions
- **PyInfra Community:** [pyinfra.com](https://pyinfra.com)

## Recognition

Contributors are recognized in:

- GitHub contributors list
- `CHANGELOG.md` acknowledgments
- Project `README.md` (for significant contributions)

---

Thank you for contributing to PyInfra OrbStack Connector! Your contributions help make this project better for everyone.
