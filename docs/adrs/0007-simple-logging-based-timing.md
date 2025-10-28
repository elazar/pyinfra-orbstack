# ADR-0007: Simple Logging-Based Timing Over Complex Metrics Infrastructure

**Date:** 2025-10-28
**Status:** Accepted
**Deciders:** Development Team
**Type:** Architecture Decision Record

## Context

Phase 6 initially proposed implementing comprehensive observability infrastructure for tracking operation performance. Three approaches were evaluated:

### Option 1: Complex Custom Metrics System (Initial Implementation)
- 304-line custom metrics collection infrastructure
- CSV/JSON export with statistics
- Aggregate statistics (mean, percentiles, success rates)
- Custom MetricsCollector class
- Operation metadata tracking

### Option 2: External Metrics Library (prometheus-client)
- Industry-standard Prometheus metrics
- Rich feature set (histograms, gauges, counters)
- Well-maintained, battle-tested
- ~200KB dependency
- Would increase runtime dependencies by 50% (1 → 2)

### Option 3: Simple Logging-Based Timing (Chosen)
- 123-line timing utility using stdlib logging
- Context manager and decorator for timing
- Standard Python logging integration
- Zero additional dependencies

### Project Context

**Current state:**
- Total codebase: ~1,500 lines
- Runtime dependencies: 1 (pyinfra)
- Use case: Local VM management tool for developers
- Phase 6 is **optional enhancement**, not core functionality

**User needs:**
- Debugging slow deployments
- Understanding operation timing
- Performance analysis during development

**Existing solutions:**
- PyInfra already shows timing in deployment output
- pytest-benchmark available for detailed performance testing
- Users can instrument with their own monitoring tools

## Decision

**Adopt Option 3: Simple logging-based timing utility**

Implementation provides:
1. Context manager: `with timed_operation("name")`
2. Decorator: `@timed` or `@timed("name")`
3. Standard Python logging integration
4. Error handling with timing on failures
5. Zero dependencies (stdlib only)

**Reject Options 1 and 2** for reasons detailed in Consequences section.

## Consequences

### Positive Consequences

**Simplicity:**
- 123 lines vs 304 lines (60% reduction)
- Uses familiar Python logging patterns
- No new concepts for users to learn
- Easy to understand and maintain

**Zero Dependencies:**
- No external dependencies added
- No version conflicts to manage
- No security vulnerabilities from deps
- Faster installation

**Integration:**
- Works with existing logging infrastructure
- Users control output via `logging.basicConfig()`
- Compatible with log aggregation tools
- Standard log analysis tools work out of the box

**Appropriate Scope:**
- Matches project philosophy (simple, focused)
- Optional feature shouldn't add complexity
- Good enough for debugging/performance analysis
- Doesn't lock users into specific monitoring approach

**Maintainability:**
- Small, straightforward codebase
- Standard Python idioms
- 100% test coverage achievable
- Low maintenance burden

### Negative Consequences

**Limited Features:**
- No automatic statistics aggregation
- No CSV/JSON export (users must parse logs)
- No percentile calculations
- No success rate tracking

**Log Parsing Required:**
- Users must parse logs for analysis
- No built-in visualization
- Requires external tools for aggregation

**Not Production-Ready Monitoring:**
- No Prometheus integration out of the box
- No dashboard support
- Users needing serious metrics must instrument themselves

### Trade-offs Accepted

**Rejected Option 1 (Complex Metrics) because:**
1. Adds 20% to total codebase for optional feature
2. Reinvents standard observability patterns
3. Maintenance burden for custom infrastructure
4. Most users won't use advanced features
5. YAGNI - "You Aren't Gonna Need It"

**Rejected Option 2 (prometheus-client) because:**
1. Adds 50% more runtime dependencies (1 → 2)
2. Overkill for local VM management tool
3. Most users won't export to Prometheus
4. Users needing Prometheus can add it themselves
5. Project scope: developer tool, not production service

**Dependency Policy Established:**
- Prefer stdlib solutions when adequate
- Each dependency must justify its value
- Consider maintenance burden in decision
- Keep runtime dependencies minimal

## Alternatives Considered

### Alternative 1: No Timing/Observability (Rejected)

**Why considered:**
- PyInfra already provides timing
- Minimal value-add

**Why rejected:**
- Small investment (123 lines) provides value
- Consistent interface for timing operations
- Useful for debugging and analysis
- Centralized helper better than ad-hoc timing

### Alternative 2: Third-Party Logging Library (Rejected)

**Examples:** structlog, loguru

**Why rejected:**
- Standard logging is sufficient
- Adds unnecessary dependency
- Users can swap logging backend if desired

### Alternative 3: Timing Only, No Logging (Rejected)

**Approach:** Return timing values, let users handle output

**Why rejected:**
- Requires users to write logging boilerplate
- Less consistent output format
- Logging integration provides more value

## Implementation Notes

### Code Structure

**timing.py (123 lines):**
```python
import logging
import time
from contextlib import contextmanager

@contextmanager
def timed_operation(name):
    start = time.time()
    logger.info(f"Starting {name}")
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.info(f"Completed {name} in {elapsed:.2f}s")

def timed(name=None):
    # Decorator implementation
    ...
```

### Usage Patterns

**Enable timing:**
```python
import logging
logging.basicConfig(level=logging.INFO)
```

**Time operations:**
```python
from pyinfra_orbstack.timing import timed_operation, timed

# Context manager
with timed_operation("vm_create"):
    create_vm("test-vm")

# Decorator
@timed("vm_deployment")
def deploy_vm(name):
    # implementation
```

## Lessons Learned

### YAGNI Principle Applied

**Initial approach:** Build comprehensive solution for future needs
**Result:** 304 lines of complex code

**Better approach:** Build minimal solution for actual needs
**Result:** 123 lines of simple code

**Lesson:** Challenge every feature - "Do users actually need this?"

### Dependency Discipline

**Question:** Should we add prometheus-client?
**Analysis:**
- Cost: 50% more runtime deps
- Benefit: Industry-standard metrics
- Reality: Most users won't use it

**Lesson:** Every dependency needs strong justification

### Simplicity Wins

**Complex solution:** Collect metrics, aggregate stats, export data
**Simple solution:** Log with timing, users do rest

**Lesson:** Provide building blocks, not complete solutions

## Success Criteria

This decision succeeds if:
1. ✅ Users can easily time operations (simple API)
2. ✅ Works with existing logging tools (no new infrastructure)
3. ✅ Low maintenance burden (minimal code)
4. ✅ Zero dependency additions (keep deps minimal)
5. ✅ Adequate for debugging/analysis (meets actual needs)

## Monitoring This Decision

**Indicators this decision is working:**
- Users find timing utility useful
- No requests for complex metrics features
- Low/no maintenance issues with timing code
- Documentation is sufficient

**Indicators we should reconsider:**
- Multiple user requests for metrics export
- Users building their own metrics collectors
- Significant demand for Prometheus integration
- Need for automated performance regression detection

**Reversibility:** High
- Can add prometheus-client later if needed
- Can build metrics on top of logging
- Timing API can remain unchanged
- Users can opt-in to advanced features

## References

### Related ADRs

- [ADR-0002: Scope Limitation for Advanced Operations](0002-advanced-operations-scope.md) - Similar YAGNI analysis
- [ADR-0006: Operation Generator Pattern](0006-operation-generator-pattern.md) - Simplicity over complexity

### Implementation Documents

- `docs/dev-journal/20251028-phase6-task6.1-timing-utility.md` - Implementation summary
- `docs/user-guide/timing-guide.md` - User documentation
- `src/pyinfra_orbstack/timing.py` - Implementation
- `tests/test_timing.py` - Test suite

### External References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [YAGNI Principle](https://martinfowler.com/bliki/Yagni.html)
- [Prometheus Client Library](https://github.com/prometheus/client_python)

## Decision Makers' Notes

### Why This Matters

This decision establishes project philosophy:
1. **Simplicity over features** - Do one thing well
2. **Stdlib over deps** - Minimize external dependencies
3. **YAGNI** - Build what's needed, not what might be needed
4. **User empowerment** - Provide tools, not complete solutions

### Pattern for Future Decisions

When evaluating future features:
1. Is it core functionality or optional enhancement?
2. Can stdlib solve it adequately?
3. What's the maintenance burden?
4. Do users actually need this?
5. Can users add it themselves if needed?

---

**Approval Date:** 2025-10-28
**Review Date:** When users request advanced metrics features
**Supersedes:** None
**Superseded By:** None
