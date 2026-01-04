# Security Headers

svc-infra provides secure HTTP response headers out of the box via `SecurityHeadersMiddleware`. This document explains each header, its purpose, and how to customize them.

## Quick Start

```python
from fastapi import FastAPI
from svc_infra.security import add_security

app = FastAPI()
add_security(app)  # Adds all security headers with safe defaults
```

## Default Headers

The following headers are set by default on all HTTP responses:

| Header | Default Value | Purpose |
|--------|---------------|---------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | Forces HTTPS for 2 years |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `DENY` | Blocks all framing (clickjacking protection) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer leakage |
| `X-XSS-Protection` | `0` | Disabled (CSP is the modern protection) |
| `Content-Security-Policy` | See below | Controls resource loading |

## Content-Security-Policy

The default CSP is designed to work with most web applications including FastAPI's built-in docs (Swagger UI, ReDoc):

```
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
img-src 'self' data: https:;
connect-src 'self';
font-src 'self' https://cdn.jsdelivr.net;
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

### CSP Directive Reference

| Directive | Value | Purpose |
|-----------|-------|---------|
| `default-src` | `'self'` | Default policy for unlisted resource types |
| `script-src` | `'self' 'unsafe-inline' https://cdn.jsdelivr.net` | Allows inline scripts and jsdelivr (for Swagger/ReDoc) |
| `style-src` | `'self' 'unsafe-inline' https://cdn.jsdelivr.net` | Allows inline styles and jsdelivr |
| `img-src` | `'self' data: https:` | Allows same-origin, data URIs, and HTTPS images |
| `connect-src` | `'self'` | Restricts fetch/XHR to same origin |
| `font-src` | `'self' https://cdn.jsdelivr.net` | Allows same-origin and jsdelivr fonts |
| `frame-ancestors` | `'none'` | Prevents the page from being embedded in frames |
| `base-uri` | `'self'` | Prevents base tag injection attacks |
| `form-action` | `'self'` | Forms can only submit to same origin |

## Header Details

### Strict-Transport-Security (HSTS)

Forces browsers to only use HTTPS for your domain.

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

- `max-age=63072000`: Remember for 2 years (in seconds)
- `includeSubDomains`: Apply to all subdomains
- `preload`: Eligible for browser preload lists

**Control HSTS preload:**
```python
add_security(app, enable_hsts_preload=False)  # Remove preload directive
```

### X-Content-Type-Options

Prevents browsers from MIME-sniffing responses away from declared content type.

```
X-Content-Type-Options: nosniff
```

This stops attacks where a malicious file is served with a harmless MIME type but executed as JavaScript.

### X-Frame-Options

Prevents your site from being embedded in frames (clickjacking protection).

```
X-Frame-Options: DENY
```

Options:
- `DENY`: Block all framing
- `SAMEORIGIN`: Allow framing from same origin only

### Referrer-Policy

Controls how much referrer information is sent with requests.

```
Referrer-Policy: strict-origin-when-cross-origin
```

This sends the full URL for same-origin requests but only the origin for cross-origin requests, preventing URL path leakage.

### X-XSS-Protection

Legacy XSS filter in older browsers. Set to `0` to disable.

```
X-XSS-Protection: 0
```

Modern browsers have deprecated this in favor of CSP. The filter can actually introduce vulnerabilities in some edge cases.

## Customization

### Override Specific Headers

```python
add_security(
    app,
    headers_overrides={
        # Stricter CSP without inline scripts
        "Content-Security-Policy": "default-src 'self'; script-src 'self'",
        # Allow framing from same origin
        "X-Frame-Options": "SAMEORIGIN",
    }
)
```

### Use Middleware Directly

For full control, use `SecurityHeadersMiddleware`:

```python
from svc_infra.security import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    overrides={
        "Content-Security-Policy": "default-src 'self'",
    }
)
```

### Access Default Values

```python
from svc_infra.security import SECURE_DEFAULTS

print(SECURE_DEFAULTS)
# {
#     "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
#     "X-Content-Type-Options": "nosniff",
#     "X-Frame-Options": "DENY",
#     ...
# }
```

## Common Customizations

### API-Only Service (No Browser UI)

For services that only serve JSON APIs:

```python
add_security(
    app,
    headers_overrides={
        "Content-Security-Policy": "default-src 'none'",
    }
)
```

### Embedding in Iframes

If your app needs to be embedded (e.g., widget):

```python
add_security(
    app,
    headers_overrides={
        "X-Frame-Options": "SAMEORIGIN",
        "Content-Security-Policy": "...; frame-ancestors 'self' https://trusted-site.com",
    }
)
```

### External CDN Resources

If you use additional CDNs:

```python
add_security(
    app,
    headers_overrides={
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' https://cdn.example.com; "
            "style-src 'self' https://cdn.example.com; "
            "img-src 'self' https: data:; "
            "font-src 'self' https://fonts.gstatic.com"
        ),
    }
)
```

### Development Mode

During development, you may need a more permissive CSP:

```python
import os

if os.getenv("ENV") == "development":
    add_security(
        app,
        headers_overrides={
            "Content-Security-Policy": "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:",
        }
    )
else:
    add_security(app)  # Production defaults
```

## Testing Headers

Verify headers are correctly set:

```bash
curl -I https://your-api.example.com/health
```

Expected output includes:
```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; ...
```

## Security Scanning Tools

- [Mozilla Observatory](https://observatory.mozilla.org/) - Grades your security headers
- [Security Headers](https://securityheaders.com/) - Analyzes response headers
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/) - Google's CSP analysis tool

## See Also

- [Security Overview](security.md) - Full security documentation
- [CORS Configuration](security.md#cors-and-security-headers) - Cross-origin settings
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
