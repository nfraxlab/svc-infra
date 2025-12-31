# Contributing to svc-infra

Thank you for your interest in contributing to svc-infra! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build great software.

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry for dependency management
- Git

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nfraxlab/svc-infra.git
cd svc-infra

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Run tests
pytest -q

# Run linting
ruff check

# Run type checking
mypy src
```

## Development Workflow

### Quick Start (Recommended)

Use `make pr` for the fastest workflow:

```bash
# 1. Make your code changes
# 2. Create a PR with one command:
make pr m="feat: add your feature"
```

### Two-Mode Workflow

**Mode A: Start a new PR** (on default branch OR with `new=1`)
```bash
# On main → creates new branch + PR, stays on new branch
make pr m="feat: add caching middleware"

# On feature branch → split commits into new PR
make pr m="feat: split this work" new=1
```

**Mode B: Update current PR** (on feature branch)
```bash
# Add more commits to existing PR
make pr m="fix: address review feedback"

# Sync with main before pushing (rebase + force-push)
make pr m="fix: sync and update" sync=1
```

### All Options

| Option | Example | Description |
|--------|---------|-------------|
| `m=` | `m="feat: add X"` | Commit message (required, conventional commits) |
| `sync=1` | `sync=1` | Rebase on base branch before pushing |
| `new=1` | `new=1` | Force create new PR from current HEAD |
| `b=` | `b="my-branch"` | Use explicit branch name |
| `draft=1` | `draft=1` | Create PR as draft |
| `base=` | `base=develop` | Target different base branch |
| `FORCE=1` | `FORCE=1` | Skip conventional commit validation |

### Examples

```bash
# Basic: create PR from main
make pr m="feat: add rate limiting"

# Add commits to existing PR
make pr m="fix: handle edge case"

# Sync with main, then push
make pr m="refactor: clean up" sync=1

# Create draft PR
make pr m="feat: work in progress" draft=1

# Target a release branch
make pr m="fix: hotfix" base=release-v1

# Split work into new PR from feature branch
make pr m="feat: extract this part" new=1

# Batch commits before PR
make commit m="feat: add base class"
make commit m="feat: add implementation"
make pr m="feat: complete caching support"
```

### Manual Workflow

If you prefer manual git commands:

```bash
# 1. Create a branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# - Follow the existing code style
# - Add type hints to all functions
# - Write docstrings for public APIs
# - Add tests for new functionality

# 3. Run quality checks
ruff format
ruff check
mypy src
pytest -q

# 4. Commit and push
git add -A
git commit -m "feat: your feature"
git push origin feature/your-feature-name

# 5. Open a PR on GitHub
```

### Batching Multiple Commits

For related changes, batch commits before creating a PR:

```bash
make commit m="feat: add base class"
make commit m="feat: add implementation"
make pr m="feat: complete feature"
```

## Code Standards

### Type Hints

All functions must have complete type hints:

```python
# [OK] Good
def process_request(data: dict[str, Any], timeout: float = 30.0) -> Response:
    ...

# [X] Bad
def process_request(data, timeout=30.0):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Calculate the hash of the given data.

    Args:
        data: The bytes to hash.
        algorithm: The hash algorithm to use.

    Returns:
        The hexadecimal hash string.

    Raises:
        ValueError: If the algorithm is not supported.
    """
```

### Error Handling

- Use specific exception types, not bare `Exception`
- Always log errors before re-raising
- Never silently swallow exceptions

```python
# [OK] Good
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise

# [X] Bad
try:
    result = risky_operation()
except Exception:
    pass
```

### Testing

- Write tests for all new functionality
- Test both success and error paths
- Use pytest fixtures for common setup

```python
def test_cache_returns_stored_value():
    cache = MemoryCache()
    cache.set("key", "value", ttl=60)
    assert cache.get("key") == "value"

def test_cache_raises_on_expired():
    cache = MemoryCache()
    cache.set("key", "value", ttl=-1)  # Already expired
    with pytest.raises(KeyError):
        cache.get("key")
```

## Project Structure

```
svc-infra/
├── src/svc_infra/     # Main package
│   ├── api/           # FastAPI framework
│   ├── auth/          # Authentication & authorization
│   ├── cache/         # Caching backends
│   ├── db/            # Database utilities
│   ├── jobs/          # Background job processing
│   ├── obs/           # Observability (logging, metrics)
│   ├── storage/       # File storage backends
│   └── webhooks/      # Webhook management
├── tests/             # Test files
├── docs/              # Documentation
└── examples/          # Example applications
```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format. This enables automated CHANGELOG generation.

**Format:** `type(scope): description`

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `perf:` Performance improvement
- `test:` Adding or updating tests
- `ci:` CI/CD changes
- `chore:` Maintenance tasks

**Examples:**
```
feat: add Redis cache backend
fix: handle connection timeout in database pool
docs: update authentication guide
refactor: extract retry logic to shared utility
test: add unit tests for webhook signing
```

**Bad examples (will be grouped as "Other Changes"):**
```
Refactor code for improved readability  ← Missing type prefix!
updating docs                           ← Missing type prefix!
bug fix                                 ← Missing type prefix!
```

### PR Title Enforcement

A GitHub Action automatically ensures your PR title reflects the highest-priority commit type:

1. Scans all commits in the PR for conventional commit prefixes
2. Auto-updates the PR title if needed (e.g., `docs:` → `feat:` if there's a `feat:` commit)
3. Passes with a warning after update

**Priority order:** `feat!` > `feat` > `fix` > `perf` > `refactor` > `docs` > `chore` > `test` > `ci` > `build`

This ensures squash-merge commits trigger the correct semantic-release.

## Deprecation Guidelines

When removing or changing public APIs, follow our [Deprecation Policy](DEPRECATION.md).

### When to Deprecate vs Remove

- **Deprecate first** if the feature has any external users
- **Immediate removal** only for security vulnerabilities (see DEPRECATION.md)
- **Never remove** without at least 2 minor versions of deprecation warnings

### How to Add Deprecation Warnings

Use the `@deprecated` decorator:

```python
from svc_infra.utils.deprecation import deprecated

@deprecated(
    version="1.2.0",
    reason="Use new_function() instead",
    removal_version="1.4.0"
)
def old_function():
    ...
```

For deprecated parameters:

```python
from svc_infra.utils.deprecation import deprecated_parameter

def my_function(new_param: str, old_param: str | None = None):
    if old_param is not None:
        deprecated_parameter(
            name="old_param",
            version="1.2.0",
            reason="Use new_param instead"
        )
        new_param = old_param
    ...
```

### Documentation Requirements

When deprecating a feature, you must:

1. Add `@deprecated` decorator or call `deprecated_parameter()`
2. Update the docstring with deprecation notice
3. Add entry to "Deprecated Features Registry" in DEPRECATION.md
4. Add entry to CHANGELOG.md under "Deprecated" section

### Migration Guide Requirements

For significant deprecations, create a migration guide:

1. Create `docs/migrations/v{version}.md`
2. Explain what changed and why
3. Provide before/after code examples
4. Link from the deprecation warning message

## CI Pipeline & Production Readiness

Every PR triggers our CI pipeline. Understanding the flow helps you debug failures faster.

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  PR opened / updated                                                │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    ┌─────────┐      ┌───────────┐     ┌───────────────┐
    │  lint   │      │ type-check│     │ security-scan │
    │ (ruff)  │      │  (mypy)   │     │   (bandit)    │
    └────┬────┘      └─────┬─────┘     └───────────────┘
         │                 │
         └────────┬────────┘
                  ▼
            ┌───────────┐
            │   test    │  ← runs AFTER lint & type-check pass
            │ (pytest)  │
            └─────┬─────┘
                  │
                  ▼ (only PRs → main with code/packaging changes)
    ┌──────────────────────────────┐
    │   production-readiness       │
    │   • Vulnerability scan       │
    │   • Package build + verify   │
    │   • Docs check               │
    └──────────────────────────────┘
```

### Production Readiness Gate

The `production-readiness` job runs `make report` with special CI flags:

```bash
# What CI runs (don't run this locally - it requires evidence variables)
make report STRICT=1 REPORT_MODE=ci
```

**Key behaviors:**
- `REPORT_MODE=ci` skips lint/mypy/pytest (already ran in earlier jobs)
- `STRICT=1` enforces score ≥ 9/11 and requires pip-audit
- CI mode requires `LINT_PASSED=1`, `TYPE_PASSED=1`, `TESTS_PASSED=1` environment variables (set by upstream jobs)

### Local Testing

Run the full report locally before pushing:

```bash
# Full local check (recommended before any PR)
make report

# With strict mode (same threshold as CI)
make report STRICT=1

# Custom coverage threshold
make report COV_MIN=80
```

**Scoring (11 points total):**

| Check | Points | Notes |
|-------|--------|-------|
| Linting (ruff) | 1 | Must pass |
| Type checking (mypy) | 1 | Must pass |
| Tests pass | 2 | All tests green |
| Coverage ≥ threshold | 2 | Default: 60% |
| No vulnerabilities | 2 | pip-audit clean |
| Package builds | 2 | poetry build + twine check |
| Documentation | 1 | README + docs/ |

**STRICT mode fails if:**
- Score < 9/11
- pip-audit not installed
- Any critical check fails (tests, vulnerabilities, build)

## Required Checks Before PR

- [ ] No hardcoded secrets or default fallbacks
- [ ] No silent exception swallowing
- [ ] Parameterized SQL queries (no string interpolation)
- [ ] `ruff check` passes
- [ ] `mypy src` passes
- [ ] `pytest` passes
- [ ] Deprecations follow the deprecation policy

## Questions?

- Open an issue for bugs or feature requests
- Join our discussions for general questions

Thank you for contributing!
