# Python 3.9 Support Decision

**Date:** 2025-10-28
**Status:** Decision Needed
**Type:** Technical Decision / Policy

## Context

During Phase 7 preparation for PyPI publishing, we encountered a CI failure due to `isort 7.0.0` requiring Python 3.10+, while our project currently supports Python 3.9+. This raises the strategic question: should we maintain Python 3.9 support?

## Critical Information: Python 3.9 is EOL

**Python 3.9 End-of-Life:** October 5, 2025 (23 days ago)

- No more security updates
- No more bug fixes
- No more official support from Python Software Foundation

**Source:** [Python EOL Schedule](https://endoflife.date/python)

## Current Project State

**Declared Support:** Python 3.9+ (as of `pyproject.toml`)

**CI Testing Matrix:**
- Python 3.9 ✅
- Python 3.10 ✅
- Python 3.11 ✅
- Python 3.12 ✅

**System Python:** macOS 15.x ships with Python 3.9.6 (as of Oct 2025)

**Current Issue:** Modern tooling (isort 7.0.0+) is dropping Python 3.9 support

## Pros of Maintaining Python 3.9 Support

### 1. **Broader User Base (Short-term)**
- Users on older systems can still use the package
- No forced Python upgrades required
- Smoother adoption curve

### 2. **macOS Default Python**
- macOS 15.x (current) ships with Python 3.9.6
- Users can use system Python without installing newer version
- Lower barrier to entry

### 3. **Conservative Approach**
- "If it works, don't break it"
- Minimal user disruption

### 4. **Current Implementation**
- Already configured and tested
- All tests pass on Python 3.9
- No code changes needed for compatibility

## Cons of Maintaining Python 3.9 Support

### 1. **Security Risks** ⚠️ **CRITICAL**
- No security patches after EOL (Oct 5, 2025)
- Vulnerabilities will not be fixed
- Potential liability for projects using our connector

**Impact:** High - Security vulnerabilities in Python 3.9 affect all users

### 2. **Dependency Ecosystem Moving On**
- isort 7.0.0+ requires Python 3.10+
- Other tools will follow (black, mypy, flake8, pytest)
- New versions of libraries will drop 3.9 support
- Stuck with older, unmaintained versions of tools

**Current Example:**
- isort 7.0.0 (latest) requires Python 3.10+
- isort 6.1.3 (last 3.9-compatible) released months ago
- isort 6.x may not receive updates

**Projected Timeline:**
- Q1 2026: Most major tools drop Python 3.9
- Q2 2026: Critical dependencies may drop 3.9
- Q3 2026: Increasingly difficult to maintain

### 3. **Development Complexity**
- Can't use latest tooling (isort, black, mypy updates)
- Can't use Python 3.10+ features (structural pattern matching, improved type hints)
- Slower CI (testing 4 Python versions vs 3)
- More testing overhead

### 4. **Opportunity Cost**
- Time spent maintaining 3.9 compatibility
- Can't adopt newer Python features
- Holding back from ecosystem advances

### 5. **False Sense of Support**
- Users may think 3.9 is "supported" when it's EOL
- We can't fix Python-level security issues
- Better to be honest: "Use supported Python"

### 6. **CI/CD Complications**
- Need older tool versions for 3.9 compatibility
- Split between "modern tools" and "3.9-compatible tools"
- Pre-commit hooks failing on 3.9

## What Do Similar Projects Do?

### PyInfra Itself

Let me check PyInfra's requirements...

**PyInfra 3.x:** Requires Python 3.8+ (but this was before 3.9 EOL)

**Expectation:** PyInfra will likely drop 3.9 support in next major release

### Industry Standard (2025)

**Common patterns:**
- **Conservative:** Support N-1 (3.11 + 3.12) = 2 versions
- **Moderate:** Support N-2 (3.10 + 3.11 + 3.12) = 3 versions
- **Aggressive:** Support N only (3.12) = 1 version

**Python 3.10 Status:**
- Released: October 2021
- EOL: October 2026 (1 year away)
- Stable and widely adopted

## Real-World User Impact

### Scenario 1: User on Python 3.9
**If we support 3.9:**
- User can install pyinfra-orbstack
- User is running EOL Python with security vulnerabilities
- User may blame our package for issues caused by Python 3.9

**If we require 3.10+:**
- User sees clear error: "Requires Python 3.10+"
- User upgrades Python (one-time, 10 minutes)
- User gets secure Python + our connector

### Scenario 2: User on macOS 15.x (Python 3.9.6)
**If we support 3.9:**
- Works with system Python
- But system Python is EOL and insecure

**If we require 3.10+:**
- User installs Python 3.12 via Homebrew: `brew install python@3.12`
- Takes 2 minutes
- User gets modern Python

**Reality:** Anyone using OrbStack (a modern dev tool) can install Python 3.10+

## Technical Constraints

### Current Blocker: isort 7.0.0
- Latest isort requires Python 3.10+
- Options:
  1. Pin isort to 6.x (last 3.9-compatible version)
  2. Drop Python 3.9 support, use isort 7.x

### Future Blockers (Projected)
- black 25.x: May require 3.10+ in 2026
- mypy 2.x: May require 3.10+ in 2026
- pytest 9.x: May require 3.10+ in 2026

**Pattern:** As Python 3.9 EOL recedes into past, tools drop support

## Recommendations

### Option A: Drop Python 3.9 Support ✅ **RECOMMENDED**

**Action:**
1. Update `pyproject.toml`: `requires-python = ">=3.10"`
2. Remove Python 3.9 from CI matrix
3. Use latest tooling (isort 7.x, etc.)
4. Update all documentation

**Rationale:**
- Python 3.9 is EOL (security risk)
- Ecosystem is moving on (tooling compatibility)
- Users should upgrade to supported Python
- Cleaner, simpler maintenance

**Timeline:**
- **Immediate:** Aligns with Python 3.9 EOL
- **Industry-standard:** Most projects dropped 3.9 in Q4 2025

**Benefits:**
- ✅ No security liability
- ✅ Use modern tooling
- ✅ Cleaner CI/CD
- ✅ Can use Python 3.10+ features
- ✅ No dependency version constraints

**Downsides:**
- ❌ Users on macOS with only system Python need to install 3.10+
  - **Mitigation:** Clear error message, easy install instructions
  - **Reality:** Takes 2 minutes to install via Homebrew

### Option B: Maintain Python 3.9 Support ⚠️ **NOT RECOMMENDED**

**Action:**
1. Pin isort to 6.x in `.pre-commit-config.yaml`
2. Monitor other tools for 3.9 support
3. Accept limitations of older tooling

**Rationale:**
- Broader compatibility (short-term)
- No breaking change for 3.9 users

**Benefits:**
- ✅ Works with macOS system Python
- ✅ Broader user base (temporarily)

**Downsides:**
- ❌ Security risk (EOL Python)
- ❌ Stuck with older tools
- ❌ More complex CI/CD
- ❌ Will need to drop 3.9 eventually anyway
- ❌ False sense of support

### Option C: Hybrid Approach (Not Viable)

**Idea:** Support 3.9 but with caveats

**Reality:** Can't half-support a Python version
- Either CI tests it or doesn't
- Either tools work or don't
- Creates confusion

## Decision Criteria

### Technical Factors
| Factor | 3.9 Support | 3.10+ Only |
|--------|-------------|------------|
| Security | ❌ EOL, vulnerable | ✅ Supported |
| Tooling | ❌ Degrading | ✅ Modern |
| CI complexity | ❌ Higher | ✅ Simpler |
| Maintenance | ❌ Higher | ✅ Lower |
| Python features | ❌ Limited to 3.9 | ✅ 3.10+ features |

### User Impact
| Factor | 3.9 Support | 3.10+ Only |
|--------|-------------|------------|
| macOS users | ✅ System Python | ⚠️ Need Homebrew Python |
| Initial install | ✅ No extra step | ⚠️ Install Python 3.10+ |
| Security | ❌ Vulnerable | ✅ Secure |
| Long-term | ❌ Must upgrade eventually | ✅ Stable |

### Project Health
| Factor | 3.9 Support | 3.10+ Only |
|--------|-------------|------------|
| Code quality | ⚠️ Older patterns | ✅ Modern patterns |
| Dependencies | ❌ Pinned/old | ✅ Latest |
| Future-proofing | ❌ Technical debt | ✅ Aligned with ecosystem |

## Decision: Keep Python 3.9 Support (For Now)

**Date:** 2025-10-28
**Status:** Accepted
**Decision:** Maintain Python 3.9 support in version 0.1.0

### Rationale

1. **macOS Default:** macOS 15.x ships with Python 3.9.6 by default
2. **Conservative Approach:** Let ecosystem settle before dropping support
3. **Initial Release:** Broader compatibility for v0.1.0 adoption
4. **Monitor Ecosystem:** Wait for other tools and macOS to move on

### Implementation

**Immediate fix for CI:**
- Downgrade isort from 7.0.0 → 5.13.2 (last stable version supporting Python 3.9)
- Keep all other tools at latest versions
- Continue testing Python 3.9, 3.10, 3.11, 3.12 in CI

**Documentation:**
- State minimum version: Python 3.9+
- Note that 3.9 is EOL (transparency)
- Recommend 3.10+ for security

### Re-evaluation Criteria

Drop Python 3.9 support when **any** of these occur:

1. **macOS Update:** macOS ships with Python 3.10+ by default
2. **Tooling Pressure:** 2+ core tools (black, mypy, pytest) drop 3.9 support
3. **Timeline:** 6 months post-EOL (April 2026)
4. **PyInfra:** PyInfra drops Python 3.9 support
5. **User Feedback:** No users report using Python 3.9

### Monitoring Plan

**Quarterly Reviews (Q1 2026, Q2 2026, Q3 2026):**
- Check tool compatibility (black, mypy, isort, pytest, flake8)
- Review macOS default Python version
- Check PyInfra Python requirements
- Assess user reports/issues mentioning Python versions

**Likely Timeline:**
- **Q1 2026:** Continue 3.9 support
- **Q2 2026:** Re-evaluate (expect pressure from tools)
- **Q3 2026:** Likely drop 3.9 in version 0.2.0 or 1.0.0

### Trade-offs Accepted

**Benefits (keeping 3.9):**
- ✅ macOS users can use system Python
- ✅ Broader initial adoption
- ✅ Conservative, user-friendly approach

**Costs (keeping 3.9):**
- ⚠️ Pinned isort version (5.x vs 7.x latest)
- ⚠️ More CI matrix complexity (4 versions vs 3)
- ⚠️ Supporting EOL Python (transparency via docs)
- ⚠️ Will need to drop eventually

## Conclusion

**Decision:** Keep Python 3.9 support for version 0.1.0, with plan to drop in future version based on ecosystem movement.

**Next Steps:**
1. ✅ Pin isort to 5.13.2 (supports Python 3.9)
2. ✅ Keep documentation stating Python 3.9+
3. ✅ Add note in docs that 3.9 is EOL
4. ⏭️ Re-evaluate in Q2 2026

**Impact:** Minimal current impact, deferred decision to later version when ecosystem has clearly moved on.

### Justification

1. **Python 3.9 is End-of-Life** (Oct 5, 2025)
   - No security updates
   - Industry standard is to drop EOL versions

2. **Ecosystem is Moving On**
   - isort 7.0+ requires 3.10+
   - More tools will follow in 2026
   - Fighting the tide is costly

3. **User Best Interest**
   - Users should use supported Python
   - Clear error better than false security

4. **Project Health**
   - Use modern tooling
   - Access Python 3.10+ features
   - Simpler maintenance

5. **Initial Release Timing**
   - This is version 0.1.0 (initial release)
   - No existing users to break
   - Perfect time to set minimum version

### Implementation Plan

1. **Update `pyproject.toml`:**
   ```toml
   requires-python = ">=3.10"
   ```

2. **Update CI matrix** (`.github/workflows/ci.yml`):
   ```yaml
   python-version: ["3.10", "3.11", "3.12"]
   ```

3. **Update all documentation:**
   - README.md: Python 3.10+
   - CONTRIBUTING.md: Python 3.10+
   - docs/user-guide/compatibility.md: Update matrix
   - docs/user-guide/troubleshooting.md: Python 3.10+

4. **Add clear error message** in installation docs:
   ```markdown
   **Python 3.9 or older:** Python 3.9 reached end-of-life on October 5, 2025.
   Please upgrade to Python 3.10 or later.

   # macOS users
   brew install python@3.12
   ```

5. **Use latest tooling:**
   - isort 7.x (keep current)
   - Future tools without version constraints

### Migration Path for Users

**For macOS users with system Python 3.9:**

```bash
# Install Python 3.12 via Homebrew (2 minutes)
brew install python@3.12

# Create virtual environment with Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate

# Install pyinfra-orbstack
pip install pyinfra-orbstack
```

**Total time:** 2-5 minutes for one-time setup

## Alternatives Considered

### Alternative 1: Support 3.9 for 0.1.x, drop in 0.2.0
**Rejected because:**
- Python 3.9 is already EOL
- Will have to drop it soon anyway
- Initial release (0.1.0) is perfect time to set requirements
- No existing users to break

### Alternative 2: Support 3.9 but document as "best effort"
**Rejected because:**
- Unclear support status confuses users
- CI either tests it or doesn't
- Half-measures don't work for Python versions

### Alternative 3: Feature flag for 3.9 compatibility
**Rejected because:**
- Overly complex
- Code paths diverge
- Maintenance nightmare

## Open Questions

1. **What does PyInfra support?**
   - Need to verify PyInfra's Python requirements
   - Should align with upstream

2. **Will this hurt adoption?**
   - Probably not - anyone using OrbStack can install Python 3.10+
   - Clear requirements better than mysterious errors

3. **Should we support 3.13+?**
   - Yes - no reason to exclude newer versions
   - May need testing in future

## References

- [Python 3.9 EOL Announcement](https://endoflife.date/python)
- [isort Changelog - Python 3.10+ requirement](https://github.com/PyCQA/isort/releases)
- [Python Version Support Best Practices](https://packaging.python.org/en/latest/discussions/python-versions/)
- [Anaconda: Python 3.9 EOL Impact](https://www.anaconda.com/blog/python-3-9-end-of-life)

## Conclusion

**Decision:** Drop Python 3.9 support, require Python 3.10+

**Reasoning:**
1. Python 3.9 is EOL (security risk)
2. Tooling ecosystem moving to 3.10+
3. Initial release (0.1.0) - no breaking change
4. User best interest: use supported Python
5. Project health: modern tooling and features

**Next Steps:**
1. Update `pyproject.toml` to `requires-python = ">=3.10"`
2. Update CI matrix to test 3.10, 3.11, 3.12
3. Update all documentation
4. Proceed with Phase 7 PyPI publishing

**Impact:** Minimal - users can easily upgrade Python, and it's the right technical decision for security and maintainability.
