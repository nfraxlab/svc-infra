# Performance Baselines

> **Last Updated**: January 4, 2026
>
> **Environment**: macOS, Python 3.11, Apple Silicon

This document establishes baseline performance metrics for svc-infra to track regressions and improvements.

---

## Import Time

| Metric | Value | Notes |
|--------|-------|-------|
| Full package import | ~490ms | `import svc_infra` |

The import time includes:
- FastAPI framework initialization
- Pydantic model compilation
- Database utilities loading

---

## FastAPI Startup

| Configuration | Startup Time | Notes |
|---------------|--------------|-------|
| `FastAPI()` base | <1ms | Minimal FastAPI app |
| `easy_service_app()` | ~20ms | Full svc-infra stack |

**Middleware overhead breakdown**:
- Security headers: ~2ms
- CORS configuration: ~1ms
- Health routes: ~3ms
- Error handlers: ~2ms
- Request logging: ~5ms
- Other middleware: ~7ms

---

## Cache Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Cache init (in-memory) | <1ms | `mem://` backend |
| Cache write | <0.01ms | Per operation |
| Cache read (hit) | <0.01ms | Per operation |
| Cache read (miss) | <0.01ms | Per operation |

**Redis backend** (when configured):
| Operation | Latency | Notes |
|-----------|---------|-------|
| Cache init | ~50ms | Redis connection setup |
| Cache write | ~1ms | Network round-trip |
| Cache read | ~1ms | Network round-trip |

---

## Auth Middleware Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| JWT validation | <1ms | Token parsing + signature |
| Session lookup (memory) | <1ms | In-memory session store |
| Session lookup (Redis) | ~2ms | Network round-trip |

**Note**: Auth overhead is minimal compared to business logic.

---

## Database Operations

| Operation | Latency | Notes |
|-----------|---------|-------|
| Connection acquisition | <1ms | From pool |
| Simple SELECT | ~1-5ms | Depends on query complexity |
| Transaction commit | ~5-10ms | Depends on isolation level |

---

## Webhook Delivery

| Operation | Latency | Notes |
|-----------|---------|-------|
| HMAC signature generation | <1ms | SHA-256 signing |
| Delivery attempt | Variable | Depends on target latency |
| Retry with backoff | Configured | Default: 1s, 5s, 30s |

---

## Request Throughput

Tested with `uvicorn` and `hypercorn`:

| Scenario | Requests/sec | Notes |
|----------|--------------|-------|
| Health check (`/health`) | ~10,000 | Minimal handler |
| Auth + JSON response | ~5,000 | JWT validation included |
| Full middleware stack | ~3,000 | All middleware enabled |

**Bottlenecks in order of impact**:
1. Database queries (if any)
2. External API calls
3. Auth middleware
4. JSON serialization

---

## Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Base import | ~80MB | Python + FastAPI + deps |
| Per-worker process | ~100MB | Typical production worker |
| Session cache (1000 sessions) | ~5MB | In-memory backend |

---

## Recommendations

### For Low Latency APIs

1. **Use connection pooling** for databases
2. **Enable response caching** for repeated requests
3. **Use async handlers** for I/O-bound operations

### For High Throughput APIs

1. **Run multiple workers** (CPU count + 1)
2. **Use Redis** for session/cache (shared across workers)
3. **Enable keep-alive connections**

### For Memory-Constrained Environments

1. **Limit worker count**
2. **Use Redis** instead of in-memory caching
3. **Configure session TTL** to evict stale sessions

---

## Running Your Own Benchmarks

```bash
# Install benchmark tools
pip install pytest-benchmark httpx

# Run benchmark suite
pytest benchmarks/ --benchmark-only

# Load testing with hey
hey -n 10000 -c 100 http://localhost:8000/health
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-04 | Initial baseline measurements |
