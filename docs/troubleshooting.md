# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with svc-infra.

## Quick Diagnostics

Run this to check your environment:

```python
import os

checks = {
    "DATABASE_URL": os.getenv("DATABASE_URL"),
    "REDIS_URL": os.getenv("REDIS_URL"),
    "JWT_SECRET_KEY": bool(os.getenv("JWT_SECRET_KEY")),
    "WEBHOOK_SECRET": bool(os.getenv("WEBHOOK_SECRET")),
}

for name, value in checks.items():
    if isinstance(value, bool):
        status = "set" if value else "missing"
    else:
        status = "configured" if value else "missing"
    print(f"{name}: {status}")
```

---

## Database Connection Errors

### Symptoms

```
DatabaseError: Could not connect to database
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection refused
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed
```

### Causes

1. Database server not running
2. Incorrect connection string
3. Network/firewall issues
4. Connection pool exhausted
5. SSL configuration mismatch

### Solutions

**1. Verify database is running:**

```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# Or check with Docker
docker ps | grep postgres
```

**2. Validate connection string format:**

```python
# Correct formats:
DATABASE_URL = "postgresql://user:pass@localhost:5432/dbname"
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/dbname"  # Async

# Common mistakes:
# - Missing +asyncpg for async connections
# - Using postgres:// instead of postgresql://
# - Special characters in password not URL-encoded
```

**3. Test connection manually:**

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test_connection():
    engine = create_async_engine(
        "postgresql+asyncpg://user:pass@localhost:5432/dbname",
        echo=True,  # Show SQL
    )
    async with engine.connect() as conn:
        result = await conn.execute("SELECT 1")
        print(f"Connection OK: {result.scalar()}")

asyncio.run(test_connection())
```

**4. Handle connection pool exhaustion:**

```python
from svc_infra.db import get_engine

# Increase pool size for high-traffic apps
engine = get_engine(
    pool_size=20,           # Default: 5
    max_overflow=30,        # Allow 30 more connections under load
    pool_timeout=30,        # Wait up to 30s for a connection
    pool_recycle=1800,      # Recycle connections after 30 min
)
```

**5. Fix SSL issues (common in cloud databases):**

```python
# For AWS RDS, Azure, etc.
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db?ssl=require"

# Or with certificate verification
import ssl
ssl_context = ssl.create_default_context(cafile="/path/to/ca-cert.pem")
engine = create_async_engine(url, connect_args={"ssl": ssl_context})
```

---

## Redis Connection Issues

### Symptoms

```
CacheConnectionError: Could not connect to Redis
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
redis.exceptions.AuthenticationError: invalid password
```

### Causes

1. Redis server not running
2. Wrong host/port/password
3. Redis requires authentication
4. Memory limit reached

### Solutions

**1. Verify Redis is running:**

```bash
redis-cli ping
# Should return: PONG

# Or with Docker
docker ps | grep redis
```

**2. Test connection:**

```python
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    password="your_password",  # If authentication is enabled
    decode_responses=True,
)

try:
    r.ping()
    print("Redis connection OK")
except redis.ConnectionError as e:
    print(f"Failed: {e}")
```

**3. Handle authentication:**

```python
# Set in environment
REDIS_URL = "redis://:password@localhost:6379/0"

# Or with svc-infra
from svc_infra.cache import init_cache

await init_cache(
    url="redis://localhost:6379/0",
    password="your_password",
)
```

**4. Graceful degradation when Redis is down:**

```python
from svc_infra.cache import cache_read, init_cache
from svc_infra.exceptions import CacheConnectionError

# Initialize with fallback
try:
    await init_cache(url="redis://localhost:6379/0")
except CacheConnectionError:
    # Fall back to in-memory cache
    await init_cache(backend="memory")
    print("Warning: Using in-memory cache (Redis unavailable)")
```

**5. Check Redis memory:**

```bash
redis-cli info memory
# Look for used_memory_human and maxmemory
```

---

## OAuth Callback Failures

### Symptoms

```
OAuthError: Invalid state parameter
OAuthError: Code exchange failed
HTTPException: 400 Bad Request - OAuth callback error
```

### Causes

1. Mismatched redirect URI
2. State parameter expired or tampered
3. Authorization code already used
4. Clock skew between servers

### Solutions

**1. Verify redirect URI matches exactly:**

```python
# In your OAuth config
OAUTH_REDIRECT_URI = "https://myapp.com/auth/callback"

# Must match EXACTLY in OAuth provider settings:
# - Same protocol (https vs http)
# - Same domain (www.myapp.com vs myapp.com)
# - Same path (/auth/callback vs /auth/callback/)
```

**2. Check state parameter handling:**

```python
from svc_infra.security import generate_state, verify_state

# When starting OAuth flow
state = generate_state(
    user_session_id=session.id,
    expires_in=600,  # 10 minutes
)

# In callback
try:
    verify_state(received_state, expected_session_id=session.id)
except StateExpiredError:
    return redirect_to_login("Session expired, please try again")
except StateInvalidError:
    return error_response("Invalid OAuth state")
```

**3. Handle code reuse:**

```python
from svc_infra.api.auth import exchange_code

try:
    tokens = await exchange_code(code, redirect_uri)
except OAuthError as e:
    if "already been used" in str(e).lower():
        # User refreshed the callback page
        return redirect_to_login("Please sign in again")
    raise
```

**4. Debug OAuth flow:**

```python
import logging
logging.getLogger("svc_infra.api.auth").setLevel(logging.DEBUG)

# This will log:
# - State generation and verification
# - Token exchange requests/responses
# - User info fetches
```

---

## JWT Validation Errors

### Symptoms

```
TokenExpiredError: Token has expired
InvalidTokenError: Token signature verification failed
JWTDecodeError: Invalid token format
```

### Causes

1. Token expired
2. Wrong secret key
3. Token from different environment
4. Clock skew between servers
5. Malformed token

### Solutions

**1. Check token expiration:**

```python
import jwt
from datetime import datetime

token = "eyJ..."
try:
    # Decode without verification to inspect
    payload = jwt.decode(token, options={"verify_signature": False})
    exp = datetime.fromtimestamp(payload["exp"])
    print(f"Token expires: {exp}")
    print(f"Current time: {datetime.now()}")
    print(f"Expired: {datetime.now() > exp}")
except jwt.DecodeError as e:
    print(f"Malformed token: {e}")
```

**2. Verify secret key matches:**

```python
import os

# Ensure same secret across all services
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
print(f"Secret hash: {hash(JWT_SECRET)}")  # Compare across services
```

**3. Handle token refresh:**

```python
from svc_infra.security import verify_jwt, refresh_access_token
from svc_infra.exceptions import TokenExpiredError

async def authenticate(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    try:
        payload = verify_jwt(token)
        return payload
    except TokenExpiredError:
        # Try to refresh
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            new_tokens = await refresh_access_token(refresh_token)
            # Set new access token in response
            return new_tokens
        raise
```

**4. Handle clock skew:**

```python
from svc_infra.security import verify_jwt

# Allow 30 seconds of clock skew
payload = verify_jwt(
    token,
    leeway=30,  # Accept tokens up to 30s past expiration
)
```

**5. Debug JWT issues:**

```python
# Use jwt.io to decode and inspect tokens
# Or programmatically:
import jwt
import json

token = "eyJ..."
parts = token.split(".")
header = json.loads(jwt.utils.base64url_decode(parts[0]))
payload = json.loads(jwt.utils.base64url_decode(parts[1]))

print("Header:", json.dumps(header, indent=2))
print("Payload:", json.dumps(payload, indent=2))
```

---

## Webhook Delivery Failures

### Symptoms

```
WebhookDeliveryError: Failed to deliver webhook after 3 retries
SignatureVerificationError: Webhook signature mismatch
WebhookTimeoutError: Endpoint did not respond within 30 seconds
```

### Causes

1. Endpoint URL unreachable
2. Signature verification failing
3. Endpoint returning errors
4. SSL certificate issues

### Solutions

**1. Test endpoint reachability:**

```python
import httpx

async def test_webhook_endpoint(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json={"test": True},
                timeout=30.0,
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
        except httpx.ConnectError as e:
            print(f"Cannot connect: {e}")
        except httpx.TimeoutException:
            print("Request timed out")
```

**2. Verify signature computation:**

```python
import hmac
import hashlib

def compute_webhook_signature(payload: bytes, secret: str) -> str:
    """Compute webhook signature the same way svc-infra does."""
    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

# In your webhook handler:
def verify_webhook(request):
    received_sig = request.headers.get("X-Webhook-Signature")
    computed_sig = compute_webhook_signature(
        request.body,
        os.getenv("WEBHOOK_SECRET"),
    )

    if not hmac.compare_digest(received_sig, computed_sig):
        raise SignatureVerificationError("Signature mismatch")
```

**3. Check webhook logs:**

```python
from svc_infra.webhooks import get_webhook_deliveries

# Get recent delivery attempts
deliveries = await get_webhook_deliveries(
    webhook_id=webhook.id,
    limit=10,
)

for d in deliveries:
    print(f"Attempt: {d.attempt}")
    print(f"Status: {d.status_code}")
    print(f"Response: {d.response_body[:200]}")
    print(f"Error: {d.error}")
    print("---")
```

**4. Handle retries properly:**

```python
from svc_infra.webhooks import WebhookConfig

# Configure retry behavior
config = WebhookConfig(
    max_retries=5,
    retry_delays=[5, 30, 300, 3600, 86400],  # Escalating delays
    timeout=30.0,
    verify_ssl=True,  # Set False for self-signed certs (not recommended)
)
```

**5. Debug webhook payloads:**

```python
# Enable debug logging
import logging
logging.getLogger("svc_infra.webhooks").setLevel(logging.DEBUG)

# Or log manually in your handler
@app.post("/webhooks/receive")
async def receive_webhook(request: Request):
    body = await request.body()
    headers = dict(request.headers)

    print(f"Headers: {headers}")
    print(f"Body: {body.decode()}")

    # Process webhook...
```

---

## Common Environment Issues

### Issue: "No module named 'svc_infra'"

```bash
pip install svc-infra
# or
poetry add svc-infra
```

### Issue: Alembic Migration Errors

```bash
# Check current migration state
alembic current

# If out of sync, stamp to current
alembic stamp head

# Then run migrations
alembic upgrade head
```

### Issue: "Event loop is already running"

```python
# In Jupyter notebooks
import nest_asyncio
nest_asyncio.apply()
```

### Issue: CORS Errors in Browser

```python
from svc_infra.security import add_security

add_security(
    app,
    cors_origins=["http://localhost:3000", "https://myapp.com"],
    cors_credentials=True,
)
```

---

## Getting Help

If you're still stuck:

1. **Enable debug logging**: `logging.getLogger("svc_infra").setLevel(logging.DEBUG)`
2. **Check GitHub Issues**: [github.com/nfraxlab/svc-infra/issues](https://github.com/nfraxlab/svc-infra/issues)
3. **Open a new issue** with:
   - svc-infra version (`pip show svc-infra`)
   - Python version
   - Database type and version
   - Full error traceback
   - Minimal reproduction code
