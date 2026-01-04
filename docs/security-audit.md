# Security Audit

**Last Audited**: January 3, 2026
**Reviewer**: AI Agent

This document records all Bandit security scanner skips and their justifications.

---

## Bandit Configuration

The following Bandit rules are skipped in `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests", ".venv", "venv"]
skips = [
    "B101",  # assert used (intentional in tests and contracts)
    "B104",  # hardcoded_bind_all_interfaces (intentional for container deployments)
    "B310",  # urllib urlopen (URL is validated/trusted in our code)
    "B311",  # random for non-crypto (intentional)
    "B324",  # SHA1/MD5 hash - used for cache keys and HIBP API, not security
]
```

---

## Skip Justifications

### B101: Use of assert

**Locations**: Throughout codebase
**Justification**: Assertions are used for programming contracts and invariants in non-production paths. Tests use assertions extensively for validation.
**Risk**: None - assertions are appropriate here.

### B104: Binding to 0.0.0.0

**Location**: [src/svc_infra/deploy/__init__.py](../src/svc_infra/deploy/__init__.py) line 280

```python
def get_host(default: str = "127.0.0.1") -> str:
    if is_containerized():
        return "0.0.0.0"
    return os.environ.get("HOST", default)
```

**Justification**: The `get_host()` function returns `0.0.0.0` only when `is_containerized()` returns True (detected via environment markers like `KUBERNETES_SERVICE_HOST`, `FLY_APP_NAME`, `RAILWAY_ENVIRONMENT`, etc.). Local development defaults to `127.0.0.1`.

**Risk**: None - behavior is environment-aware and secure by default.

### B310: urllib.request.urlopen

**Location**: [src/svc_infra/obs/cloud_dash.py](../src/svc_infra/obs/cloud_dash.py) line 26

```python
def _gapi(base, token, path, method="GET", body=None):
    url = f"{base.rstrip('/')}{path}"
    # ...
    with urllib.request.urlopen(req) as r:
```

**Justification**: This function calls Grafana Cloud API with URLs constructed from trusted configuration (base URL comes from environment/config, path is hardcoded). No user input flows into the URL.

**Risk**: None - URLs are from trusted sources.

### B311: Random for Non-Crypto

**Locations**: Various utility functions
**Justification**: `random` module is used for non-security purposes (sampling, jitter). Cryptographic operations use `secrets` module.
**Risk**: None - appropriate use of randomness.

### B324: Use of SHA1/MD5

**Locations**:
1. [src/svc_infra/cache/utils.py](../src/svc_infra/cache/utils.py) line 43
2. [src/svc_infra/security/hibp.py](../src/svc_infra/security/hibp.py) lines 13-14

**Cache Key Generation** (cache/utils.py):
```python
return hashlib.sha1(raw.encode("utf-8")).hexdigest()
```
**Justification**: SHA1 is used to generate deterministic cache keys from function arguments. This is not a security context - we need fast, deterministic hashing for cache lookups.

**HIBP Password Checking** (security/hibp.py):
```python
def sha1_hex(data: str) -> str:
    return hashlib.sha1(data.encode("utf-8")).hexdigest().upper()
```
**Justification**: The HaveIBeenPwned API requires SHA1 hashing of passwords for its k-anonymity range query protocol. This is the API specification - we cannot change it.

**Risk**: None - neither use case relies on collision resistance for security.

---

## Security Considerations for Users

1. **Password Security**: Passwords are hashed with modern algorithms (Argon2id or bcrypt via `svc_infra.security.password`). The SHA1 in HIBP client is only for breach checking lookups.

2. **JWT Secrets**: Store JWT secrets in environment variables. Support key rotation via `AUTH_JWT__OLD_SECRETS`.

3. **Session Security**: Enable `dismiss_stale_reviews` and `require_last_push_approval` in production.

4. **CORS Configuration**: Default CORS is deny-all. Explicitly configure allowed origins.

5. **Rate Limiting**: Use the built-in rate limiting middleware to protect endpoints.

---

## Recommendations

1. **Rotate Secrets Regularly**: Use the `OLD_SECRETS` pattern for zero-downtime rotation.

2. **Enable MFA**: Use the MFA hooks for sensitive operations.

3. **Audit Logging**: Enable hash-chain audit logs for compliance requirements.
