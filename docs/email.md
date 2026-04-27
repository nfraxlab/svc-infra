# Email

`svc-infra` provides production-ready email delivery with pluggable backends, Jinja templates, and a high-level sender API that also powers authentication flows.

## Quick Start

### FastAPI Sender

```python
from fastapi import Depends, FastAPI

from svc_infra.email import EmailSender, add_sender, get_sender

app = FastAPI()

add_sender(
    app,
    app_name="Acme",
    app_url="https://app.acme.com",
    support_email="support@acme.com",
)


@app.post("/register")
async def register(email: str, sender: EmailSender = Depends(get_sender)):
    await sender.send_verification(
        to=email,
        verification_url="https://app.acme.com/verify?token=abc123",
        user_name="Avery",
        expires_in="24 hours",
    )
    return {"message": "Verification email sent"}
```

### Standalone Sender

```python
from svc_infra.email import easy_sender

sender = easy_sender(
    app_name="Acme",
    app_url="https://app.acme.com",
    support_email="support@acme.com",
)

result = await sender.send_password_reset(
    to="user@example.com",
    reset_url="https://app.acme.com/reset-password?token=reset123",
    user_name="Avery",
)
```

## Environment Configuration

Common settings:

```bash
EMAIL_BACKEND=console
EMAIL_FROM=hello@example.com
EMAIL_REPLY_TO=support@example.com
EMAIL_TEMPLATES_PATH=/absolute/path/to/templates
```

Provider-specific settings:

### Console

```bash
EMAIL_BACKEND=console
```

### SMTP

```bash
EMAIL_BACKEND=smtp
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=apikey
EMAIL_SMTP_PASSWORD=your-password
EMAIL_FROM=noreply@example.com
```

### Resend

```bash
EMAIL_BACKEND=resend
EMAIL_RESEND_API_KEY=re_xxx
EMAIL_FROM=noreply@example.com
```

### SendGrid

```bash
EMAIL_BACKEND=sendgrid
EMAIL_SENDGRID_API_KEY=SG.xxx
EMAIL_FROM=noreply@example.com
```

### AWS SES

```bash
EMAIL_BACKEND=ses
EMAIL_SES_REGION=us-east-1
EMAIL_FROM=noreply@example.com
```

### Postmark

```bash
EMAIL_BACKEND=postmark
EMAIL_POSTMARK_API_TOKEN=xxx
EMAIL_FROM=noreply@example.com
```

### Mailgun

```bash
EMAIL_BACKEND=mailgun
EMAIL_MAILGUN_API_KEY=key-xxx
EMAIL_MAILGUN_DOMAIN=mg.example.com
EMAIL_FROM=noreply@example.com
```

### Brevo

```bash
EMAIL_BACKEND=brevo
EMAIL_BREVO_API_KEY=xxx
EMAIL_FROM=noreply@example.com
```

## Built-In Templates

`EmailSender` ships with these templates:

| Template | Use case | Key context |
|----------|----------|-------------|
| `verification` | Email verification | `verification_url` or `code` |
| `password_reset` | Password reset | `reset_url` |
| `invitation` | Team/workspace invites | `invitation_url`, `inviter_name` |
| `welcome` | Post-signup onboarding | `user_name` |

These variables are available automatically in template rendering:

- `app_name`
- `app_url`
- `support_email`
- `unsubscribe_url`

Use `EMAIL_TEMPLATES_PATH` to provide a custom template directory. If your directory contains `base.html`, you own the full visual system. If it only contains `verification.html` or `password_reset.html`, `svc-infra` falls back to the built-in files for everything else.

## Auth Email Customization

Authentication flows can use the same email system through `AuthEmailConfig`.

```python
from svc_infra.api.fastapi.auth import (
    AuthEmailConfig,
    AuthEmailTemplateConfig,
    add_auth_users,
)

auth_email_config = AuthEmailConfig(
    frontend_url="https://accounts.acme.com",
    app_name="Acme",
    support_email="support@acme.com",
    verification=AuthEmailTemplateConfig(
        path="/verify",
        template="verification",
        subject="Verify your Acme account",
    ),
    password_reset=AuthEmailTemplateConfig(
        path="/reset-password",
        template="password_reset",
        subject="Reset your Acme password",
    ),
)

add_auth_users(
    app,
    user_model=User,
    schema_read=UserRead,
    schema_create=UserCreate,
    schema_update=UserUpdate,
    auth_email_config=auth_email_config,
)
```

What `AuthEmailConfig` can control:

- verification and reset URL paths
- app branding and support links
- subjects, tags, and metadata
- template context via `context_builder`
- full message rendering via `render`

If you need complete control over subject, HTML, text, headers, and tracking metadata, return an `AuthEmailMessage` from `AuthEmailTemplateConfig.render`.

## Ready-To-Copy Branded Auth Templates

The repo includes a ready-to-copy auth email set at:

```text
examples/email/auth_branding/templates
```

That example includes:

- a custom `base.html` for full UI override
- branded `verification.html`
- branded `password_reset.html`
- usage instructions in `examples/email/auth_branding/README.md`

Recommended rollout:

1. Copy the example `templates/` directory into your application repo.
2. Change colors, copy, support links, and footer treatment.
3. Set `EMAIL_TEMPLATES_PATH` to that copied directory.
4. Pass `AuthEmailConfig` into `add_auth_users(...)`.

## Generic Send API

Use `send()` when you want full control without a convenience helper.

```python
result = await sender.send(
    to="user@example.com",
    subject="Quarterly launch update",
    template="my_custom_template",
    context={"headline": "Spring release"},
    tags=["announcement"],
    metadata={"campaign": "spring-release"},
)
```

## Health Check

```python
from svc_infra.email import health_check_email


@app.get("/health/email")
async def email_health():
    return await health_check_email()
```

## Examples

See the example directory for working reference code:

- `examples/email/basic_send.py`
- `examples/email/with_templates.py`
- `examples/email/fastapi_integration.py`
- `examples/email/auth_branding/`
