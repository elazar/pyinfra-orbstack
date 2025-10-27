# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the PyInfra OrbStack Connector project.

## What are ADRs?

ADRs document significant architectural decisions made during the project's development. Each ADR captures:

- **Context**: The situation that led to the decision
- **Decision**: The architectural choice that was made
- **Consequences**: The positive and negative outcomes
- **Alternatives**: Other options that were considered

## Format

All ADRs in this directory follow the [Michael Nygard ADR template](https://github.com/joelparkerhenderson/architecture-decision-record#decision-record-template-by-michael-nygard).

## Naming Convention

ADRs are numbered sequentially using the format: `NNNN-short-description.md`

Examples:
- `0001-package-namespace.md`
- `0002-advanced-operations-scope.md`
- `0003-caching-strategy.md`

## Current ADRs

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-package-namespace.md) | Package Namespace Structure | Accepted | 2025-01-16 |
| [0002](0002-advanced-operations-scope.md) | Scope Limitation for Advanced Operations | Accepted | 2025-10-23 |
| [0003](0003-multi-level-testing-strategy.md) | Multi-Level Testing Strategy | Accepted | 2025-10-27 |
| [0004](0004-session-scoped-test-vms.md) | Session-Scoped Test VM Management | Accepted | 2025-10-27 |
| [0005](0005-intelligent-retry-logic.md) | Intelligent Retry Logic for OrbStack Operations | Accepted | 2025-10-27 |
| [0006](0006-operation-generator-pattern.md) | PyInfra Operation Generator Pattern with Command Builders | Accepted | 2025-10-27 |

## Creating a New ADR

1. Determine the next sequential number
2. Create a new file: `NNNN-short-description.md`
3. Follow the Michael Nygard template structure
4. Update this README's table with the new ADR
5. Update the main [docs README](../README.md) to reference the new ADR
6. Reference the ADR in relevant code or documentation

## Related Documentation

- [Main Documentation Index](../README.md)
- [Development Journal](../dev-journal/) - Detailed analysis documents that may inform ADRs
- [Michael Nygard's ADR Template](https://github.com/joelparkerhenderson/architecture-decision-record)
