# ADR-0008: Automated Version Management with hatch-vcs

**Date:** 2025-11-01
**Status:** Accepted
**Deciders:** Matthew Turland
**Type:** Architecture Decision Record

## Context

Previously, package versioning required manual updates in multiple locations:

- `pyproject.toml` had hardcoded `version = "0.7.0"`
- `__init__.py` contained outdated `__version__ = "0.1.0"` (inconsistent with actual package version)
- Manual updates required for each release in multiple files
- Risk of version inconsistencies and human error
- No automatic connection between git tags and package version

This created friction in the release process and increased the likelihood of version mismatches between source code, built packages, and git tags.

## Decision

Implement automated version management using `hatch-vcs`, which derives the package version directly from git tags rather than hardcoded version strings.

### Configuration

**pyproject.toml changes:**
```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "pyinfra-orbstack"
dynamic = ["version"]  # Version is dynamically determined

[tool.hatch.version]
source = "vcs"  # Use version control system (git)

[tool.hatch.build.hooks.vcs]
version-file = "src/pyinfra_orbstack/_version.py"  # Generated at build time
```

**Runtime version access** (in `src/pyinfra_orbstack/__init__.py`):
Multi-level fallback strategy:
1. Try importing from `_version.py` (generated during build)
2. Fall back to `importlib.metadata.version()` (for installed packages)
3. Fall back to placeholder `0.0.0.dev0+unknown` (for development without git)

### Version Derivation

- **Tagged commit**: `v0.7.0` → package version `0.7.0`
- **Between tags**: Development version with metadata (e.g., `0.7.1.dev5+gc7e459fbf.d20251101`)
- **No tags**: Placeholder `0.0.0.dev0+unknown`

## Consequences

### Positive Consequences

1. **Single Source of Truth**: Git tags are the authoritative version source
2. **No Manual Updates**: No need to edit `pyproject.toml` or `__init__.py` for version changes
3. **Consistency**: Version is always synchronized with git tags
4. **Traceability**: Development versions include git commit hash and distance from last tag
5. **CI/CD Friendly**: Build systems automatically detect the version without configuration
6. **Standards Compliant**: Follows PEP 621 (dynamic metadata) and PEP 440 (version format)
7. **Reduced Human Error**: Eliminates version mismatch issues

### Negative Consequences

1. **Git Dependency**: Requires git repository with proper tag history
2. **Build-time Dependency**: Adds `hatch-vcs` as a build dependency
3. **Shallow Clone Issues**: CI/CD systems using shallow clones need `git fetch --unshallow`
4. **Learning Curve**: Maintainers need to understand git tag-based versioning
5. **Tag Discipline**: Requires proper git tagging practices (can't easily revert)

## Alternatives Considered

### Alternative 1: setuptools-scm

**Description**: Standard Python tool for version management from VCS
**Pros**: Well-established, widely used, extensive documentation
**Cons**: Project uses `hatchling`, not `setuptools`; would require changing build backend
**Decision**: Rejected - `hatch-vcs` is the natural choice for `hatchling` projects

### Alternative 2: Manual Versioning (Status Quo)

**Description**: Continue manually updating version in `pyproject.toml` and `__init__.py`
**Pros**: Simple, no additional dependencies, full control
**Cons**: Prone to inconsistencies, manual effort, error-prone, poor DX
**Decision**: Rejected - automation provides significant benefits

### Alternative 3: bumpversion / bump2version

**Description**: CLI tools for automated version bumping
**Pros**: Structured version management, templating support
**Cons**: Still requires manual triggering, doesn't connect to git tags, extra tool
**Decision**: Rejected - doesn't provide git tag integration

### Alternative 4: dunamai

**Description**: Dynamic versioning library
**Pros**: VCS-agnostic, flexible
**Cons**: Less integrated with hatchling, more configuration needed
**Decision**: Rejected - `hatch-vcs` is better integrated with existing build system

## Implementation

The implementation was completed on 2025-11-01.

**Key Technical Details:**
- Modified `pyproject.toml` to use `dynamic = ["version"]`
- Configured `hatch-vcs` to generate `_version.py` at build time
- Implemented multi-level fallback version import in `__init__.py`
- Added `hatchling` and `hatch-vcs` as development dependencies

For detailed implementation notes, troubleshooting, and technical specifications, see:
- Implementation summary: `docs/dev-journal/20251101-version-management-implementation.md`
- Release workflow: `.cursor/rules/personal/release-workflow.mdc`

## Verification

Version detection confirmed working:
```bash
$ python -c "import pyinfra_orbstack; print(pyinfra_orbstack.__version__)"
0.7.1.dev0+gc7e459fbf.d20251101
```

This shows development version between v0.7.0 and next release, with commit hash and date.

## Release Workflow Impact

### Old Workflow
1. Manually update version in `pyproject.toml`
2. Manually update version in `__init__.py`
3. Update CHANGELOG.md
4. Commit changes
5. Create git tag
6. Build and publish

### New Workflow
1. Update CHANGELOG.md
2. Commit changes
3. Create git tag (e.g., `v0.8.0`)
4. Build (version automatically extracted)
5. Publish

Version is now derived from the git tag during the build step, eliminating manual version file edits.

## Related Decisions

- Complements existing use of `hatchling` as build backend
- Aligns with semantic versioning strategy (SemVer 2.0.0)
- Supports existing git workflow and tagging conventions

## References

### Related ADRs

- [ADR-0002: Scope Limitation for Advanced Operations](0002-advanced-operations-scope.md) - Build system considerations

### Implementation Documents

- `docs/dev-journal/20251101-version-management-implementation.md` - Implementation summary and technical details
- `.cursor/rules/personal/release-workflow.mdc` - Release workflow procedures
- `src/pyinfra_orbstack/__init__.py` - Runtime version detection implementation

### External References

- [hatch-vcs Documentation](https://github.com/ofek/hatch-vcs)
- [Hatchling Build System](https://hatch.pypa.io/latest/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [PEP 621 - Project Metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [Semantic Versioning 2.0.0](https://semver.org/)
