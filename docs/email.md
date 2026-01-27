# Email Module

Production-ready email infrastructure with pluggable backends, templating, and FastAPI integration.

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from svc_infra.email import add_sender, get_sender, EmailSender

app = FastAPI()
add_sender(app, app_name="MyApp")

@app.post("/register")
async def register(email: str, sender: EmailSender = Depends(get_sender)):
    await sender.send_verification(
        to=email,
        token="abc123",
        base_url="https://myapp.com",
    )
    return {"message": "Verification email sent"}
```

### One-Line API

For simple scripts or one-off emails:

```python
from svc_infra.email import easy_email

await easy_email(
    to="user@example.com",
    subject="Hello!",
    html="<p>Welcome to our app!</p>",
)
```

---

## Provider Configuration

Configure email providers using environment variables.

### Console (Development)

Default backend - prints emails to stdout for development.

```bash
EMAIL_PROVIDER=console  # or omit entirely
```

### SMTP

Standard SMTP server.

```bash
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-password
EMAIL_FROM=noreply@example.com
```

### Resend

Modern email API with excellent deliverability.

```bash
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxx...
EMAIL_FROM=noreply@example.com
```

### SendGrid

Enterprise email delivery.

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxx...
EMAIL_FROM=noreply@example.com
```

### AWS SES

Amazon Simple Email Service.

```bash
EMAIL_PROVIDER=ses
AWS_REGION=us-east-1
# Uses default AWS credential chain (env vars, IAM role, etc.)
EMAIL_FROM=noreply@example.com
```

### Postmark

Transactional email with high deliverability.

```bash
EMAIL_PROVIDER=postmark
POSTMARK_SERVER_TOKEN=xxx...
EMAIL_FROM=noreply@example.com
```

---

## API Reference

### High-Level API

#### add_sender

Add email sender to FastAPI app.

```python
from svc_infra.email import add_sender

sender = add_sender(
    app,
    app_name="MyApp",              # Required for templates
    app_url="https://myapp.com",   # Optional: for links
    support_email="help@myapp.com", # Optional: for support links
)
```

#### get_sender

Dependency to get sender in routes.

```python
from svc_infra.email import get_sender, EmailSender

@app.post("/send")
async def send_email(sender: EmailSender = Depends(get_sender)):
    await sender.send(to="...", subject="...", html="...")
```

### EmailSender Methods

#### send

Send email with HTML or template.

```python
# With raw HTML
result = await sender.send(
    to="user@example.com",
    subject="Welcome!",
    html="<p>Hello, welcome to MyApp!</p>",
)

# With template
result = await sender.send(
    to="user@example.com",
    subject="Verify your email",
    template="verification",
    context={
        "verification_url": "https://...",
        "expires_in": "24 hours",
    },
)
```

#### Convenience Methods

```python
# Send verification email
await sender.send_verification(
    to="user@example.com",
    token="abc123",
    base_url="https://myapp.com",  # URL with /verify/{token}
    expires_in="24 hours",         # Optional
)

# Send password reset email
await sender.send_password_reset(
    to="user@example.com",
    token="reset123",
    base_url="https://myapp.com",
    expires_in="1 hour",
)

# Send invitation email
await sender.send_invitation(
    to="newuser@example.com",
    inviter_name="John Doe",
    token="invite123",
    base_url="https://myapp.com",
    message="Join us!",  # Optional custom message
)

# Send welcome email
await sender.send_welcome(
    to="user@example.com",
    user_name="Alice",
)
```

### Low-Level API

#### add_email

Add just the backend (no templates/convenience methods).

```python
from svc_infra.email import add_email, get_email

backend = add_email(app)

@app.post("/send")
async def send(email = Depends(get_email)):
    msg = EmailMessage(
        to=["user@example.com"],
        subject="Hello",
        html="<p>Hi</p>",
    )
    return await email.send(msg)
```

---

## Templates

### Built-in Templates

Four templates are included:

| Template | Purpose | Required Context |
|----------|---------|------------------|
| `verification` | Email verification | `verification_url` |
| `password_reset` | Password reset | `reset_url`, `expires_in` |
| `invitation` | Team/app invitation | `invitation_url`, `inviter_name` |
| `welcome` | Welcome after signup | `user_name` |

### Template Context

All templates receive these variables automatically:

- `app_name` - Your application name
- `app_url` - Your application URL
- `support_email` - Support contact email
- `current_year` - Current year for footer

### Custom Templates

You can use custom template directories:

```python
from svc_infra.email import EmailSender, EmailTemplateLoader

loader = EmailTemplateLoader(
    template_dirs=["/path/to/my/templates"],
    app_name="MyApp",
)
sender = EmailSender(backend, loader)

# Use custom template
await sender.send(
    to="user@example.com",
    subject="Custom Email",
    template="my_custom_template",
    context={"foo": "bar"},
)
```

Template files should be Jinja2 HTML:

```html
<!-- my_custom_template.html -->
<!DOCTYPE html>
<html>
<body>
  <h1>Hello from {{ app_name }}</h1>
  <p>Custom content: {{ foo }}</p>
</body>
</html>
```

---

## Health Check

Monitor email configuration:

```python
from svc_infra.email import health_check_email

@app.get("/health/email")
async def email_health():
    return await health_check_email()
```

Response:

```json
{
  "status": "healthy",
  "configured": true,
  "provider": "resend"
}
```

---

## Migration Guide

### From Old sender.py

If you were using the old `sender.py` module:

```python
# OLD - sender.py
from svc_infra.auth.sender import add_email, get_email, send_verification_email

add_email(app)

@app.post("/register")
async def register(email = Depends(get_email)):
    await send_verification_email(email, "user@...", "token", "https://...")
```

```python
# NEW - email module
from svc_infra.email import add_sender, get_sender

add_sender(app, app_name="MyApp")

@app.post("/register")
async def register(sender = Depends(get_sender)):
    await sender.send_verification(
        to="user@...",
        token="token",
        base_url="https://...",
    )
```

### Key Differences

1. **Unified sender**: Use `EmailSender` for all email types
2. **Branding**: Configure `app_name`, `app_url` once in `add_sender`
3. **Templates**: Rich HTML templates with consistent branding
4. **Convenience methods**: `send_verification`, `send_password_reset`, etc.
5. **Better typing**: Full type hints and Pydantic models

### Backward Compatibility

The old `sender.py` module still works but uses the new email module internally. Gradual migration is supported.

---

## Best Practices

### Error Handling

```python
from svc_infra.email import EmailSendResult

result = await sender.send(to="...", subject="...", html="...")

if result.status == "sent":
    logger.info(f"Email sent: {result.message_id}")
elif result.status == "queued":
    logger.info(f"Email queued: {result.message_id}")
else:
    logger.error(f"Email failed: {result.error}")
```

### Async Context

All send methods are async. For sync code:

```python
import asyncio
from svc_infra.email import easy_email

asyncio.run(easy_email(to="...", subject="...", html="..."))
```

### Testing

Use console backend in tests:

```python
import os

os.environ["EMAIL_PROVIDER"] = "console"

# Emails will be printed, not sent
```

Or mock the backend:

```python
from unittest.mock import AsyncMock

sender.backend.send = AsyncMock(return_value=EmailSendResult(...))
```

---

## Troubleshooting

### Email not sending

1. Check `EMAIL_PROVIDER` is set correctly
2. Verify API keys are valid
3. Check `EMAIL_FROM` is a verified sender address

### Template not found

1. Check template name matches file name (without `.html`)
2. Ensure template directory is accessible
3. Use `loader.get_available_templates()` to list available templates

### Health check shows "unconfigured"

1. Call `add_email` or `add_sender` before health check
2. Verify app startup order

---

## Complete Example

```python
from fastapi import Depends, FastAPI
from svc_infra.email import add_sender, get_sender, EmailSender, health_check_email

app = FastAPI()

# Configure on startup
add_sender(
    app,
    app_name="Acme Inc",
    app_url="https://acme.com",
    support_email="support@acme.com",
)


@app.get("/health/email")
async def email_health():
    return await health_check_email()


@app.post("/auth/register")
async def register(
    email: str,
    sender: EmailSender = Depends(get_sender),
):
    # Create user, generate token...
    token = "abc123"

    await sender.send_verification(
        to=email,
        token=token,
        base_url="https://acme.com",
    )

    return {"message": "Check your email to verify"}


@app.post("/auth/forgot-password")
async def forgot_password(
    email: str,
    sender: EmailSender = Depends(get_sender),
):
    # Lookup user, generate token...
    token = "reset456"

    await sender.send_password_reset(
        to=email,
        token=token,
        base_url="https://acme.com",
    )

    return {"message": "Check your email for reset link"}
```
