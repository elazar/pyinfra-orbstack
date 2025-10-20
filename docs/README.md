# Documentation

This directory contains project documentation and architectural decision records (ADRs).

## Architecture Decision Records (ADRs)

Architecture Decision Records (ADRs) are documents that capture important architectural decisions made during the project's development. They provide context for why certain decisions were made and help future developers understand the reasoning behind the current architecture.

### What are ADRs?

ADRs are short text documents that capture a single architecture decision. They include:

- **Context**: The situation that led to the decision
- **Decision**: The architectural choice that was made
- **Consequences**: The positive and negative outcomes of the decision
- **Alternatives**: Other options that were considered

### ADR Format

Our ADRs follow the [Michael Nygard template](https://github.com/joelparkerhenderson/architecture-decision-record#decision-record-template-by-michael-nygard) and include:

- **Date**: When the decision was made
- **Status**: Current status (Proposed, Accepted, Deprecated, etc.)
- **Deciders**: Who made the decision
- **Type**: Type of decision (Architecture Decision Record)

### Current ADRs

- [ADR-001: Package Namespace Structure](20250116-package-namespace-structure.md) - Decision on using `pyinfra_orbstack` vs `pyinfra.orbstack` namespace

### Creating New ADRs

When making significant architectural decisions:

1. Create a new ADR file in this directory
2. Use the format: `YYYYMMDD-decision-title.md`
3. Follow the template structure
4. Update this README to include the new ADR
5. Reference the ADR in relevant code or documentation

## Development Standards

This project adheres to several development standards to ensure consistency, maintainability, and quality.

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (SemVer) for version numbering:

- **MAJOR.MINOR.PATCH** format (e.g., 1.2.3)
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

### Conventional Commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit message formatting. This standard provides a structured format for commit messages that enables automated tools for generating changelogs, determining semantic versioning, and more.

#### Commit Message Format

```plain
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries

#### Examples

```bash
feat: add vm_create operation for OrbStack VMs
fix(connector): handle SSH connection failures gracefully
docs: update installation instructions for uv package manager
refactor(operations): simplify VM status checking logic
test: add unit tests for OrbStackConnector class
chore: update dependencies to latest versions
```

#### Benefits

- **Automated Changelog Generation**: Commit messages can be parsed to automatically generate changelogs
- **Semantic Versioning**: Commit types help determine version bumps (feat = minor, fix = patch, breaking = major)
- **Clear History**: Structured messages make it easier to understand project history
- **Tool Integration**: Works with tools like semantic-release, conventional-changelog, and more

### Keep a Changelog

This project follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format for the [CHANGELOG.md](../CHANGELOG.md) file:

- **Unreleased**: Changes that haven't been released yet
- **Versioned sections**: Each release has its own section
- **Categorized changes**: Added, Changed, Deprecated, Removed, Fixed, Security
- **Chronological order**: Most recent changes first

### Development Workflow

#### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/pyinfra_orbstack

# Alternative using pip
pip install -e ".[dev]"
pytest
pytest --cov=src/pyinfra_orbstack
```

#### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run flake8 src/ tests/

# Type checking
uv run mypy src/

# Alternative using pip
black src/ tests/
flake8 src/ tests/
mypy src/
```

#### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all hooks
uv run pre-commit run --all-files
```

## Testing Documentation

- [Testing and Coverage Methodology](testing-and-coverage-methodology.md) - Comprehensive testing strategy and coverage standards
- [Test Implementation Analysis](test-implementation-analysis.md) - Details on test structure and implementation
- [Coverage Gaps Analysis](coverage-gaps-analysis.md) - Analysis of code coverage and gaps

## References

- [Architecture Decision Records](https://github.com/joelparkerhenderson/architecture-decision-record) - Comprehensive guide to ADRs
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) - Michael Nygard's original ADR concept
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html) - Version numbering specification
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format specification
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) - Changelog format specification
