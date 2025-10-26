# Documentation

This directory contains project documentation and architectural decision records (ADRs).

## Documentation Organization

### Directory Structure and Standards

- **`user-guide/`** - User-facing documentation (installation, usage, tutorials, troubleshooting)
- **`dev-journal/`** - Development journal and historical analysis documents with date-stamped filenames (`YYYYMMDD-topic.md`)
- **`adrs/`** - Architecture Decision Records (ADRs) documenting significant architectural decisions
- **Root `docs/`** - Single-file documentation (this `README.md` file, standards)
- **Additional subdirectories** - Topic-specific multi-file documentation as needed

## Architecture Decision Records (ADRs)

ADRs document significant architectural decisions made during development, providing context for why certain choices were made. Each ADR captures:

- **Context**: The situation that led to the decision
- **Decision**: The architectural choice that was made
- **Consequences**: The positive and negative outcomes
- **Alternatives**: Other options that were considered

We follow the [Michael Nygard ADR template](https://github.com/joelparkerhenderson/architecture-decision-record#decision-record-template-by-michael-nygard).

### Current ADRs

- [ADR-0001: Package Namespace Structure](adrs/0001-package-namespace.md) - Decision on using `pyinfra_orbstack` vs `pyinfra.orbstack` namespace
- [ADR-0002: Scope Limitation for Advanced Operations](adrs/0002-advanced-operations-scope.md) - Decision to limit operations to those supported by OrbStack CLI and PyInfra's architectural model

### Related Analysis Documents

- [Phase 3 Feasibility Analysis](dev-journal/20251023-phase3-feasibility-analysis.md) - Comprehensive analysis of OrbStack CLI capabilities and PyInfra architectural constraints (informed ADR-0002)

### Creating New ADRs

When making significant architectural decisions:

1. Create a new ADR file in `adrs/` with format: `NNNN-decision-title.md` (e.g., `0003-caching-strategy.md`)
2. Follow the [Michael Nygard template](https://github.com/joelparkerhenderson/architecture-decision-record#decision-record-template-by-michael-nygard)
3. Update this `README.md` file to list the new ADR in the "Current ADRs" section
4. Reference the ADR in relevant code or documentation
5. Consider adding detailed analysis to `dev-journal/` if needed (link from ADR)

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

- [Testing and Coverage Methodology](dev-journal/20251021-testing-and-coverage-methodology.md) - Comprehensive testing strategy and coverage standards
- [Test Suite Refactoring Analysis](dev-journal/20251021-test-suite-refactoring-analysis.md) - Analysis of test redundancy and consolidation recommendations
- [Test Implementation Analysis](dev-journal/20250817-test-implementation-analysis.md) - Details on test structure and implementation
- [Running Tests](dev-journal/20251021-running-tests.md) - Guide to running tests with various options
- [Test Timing Guide](dev-journal/20251025-test-timing-guide.md) - How to view test execution times and identify slow tests
- [Live Test Monitoring](dev-journal/20251025-live-test-monitoring.md) - Real-time monitoring of test execution with live elapsed time updates
- [Benchmark Guide](dev-journal/20251025-benchmark-guide.md) - Performance benchmarking and regression detection

## System Performance and Troubleshooting

- [OrbStack Timeout Analysis](dev-journal/20251025-orbstack-timeout-analysis.md) - Root cause analysis and
  mitigation strategies for VM creation timeouts
- [Process Analysis and Recommendations](dev-journal/20251025-process-analysis-recommendations.md) - Memory
  optimization strategy and system resource management
- [Test Results: Post Optimization](dev-journal/20251025-test-results-post-optimization.md) - Comprehensive
  test suite results after memory optimization

## References

- [Architecture Decision Records](https://github.com/joelparkerhenderson/architecture-decision-record) - Comprehensive guide to ADRs
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) - Michael Nygard's original ADR concept
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html) - Version numbering specification
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format specification
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) - Changelog format specification
