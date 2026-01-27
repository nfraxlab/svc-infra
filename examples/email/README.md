# Email Examples

This directory contains working examples for the svc-infra email module.

## Examples

### basic_send.py

Simple HTML email sending with auto-detection of email backend.

```bash
EMAIL_FROM=noreply@example.com python basic_send.py
```

### with_templates.py

Template-based emails for common use cases:
- Email verification (with code or URL)
- Password reset
- Team invitations
- Welcome emails

```bash
EMAIL_FROM=noreply@example.com python with_templates.py
```

### fastapi_integration.py

Full FastAPI application with email integration:
- Application setup with `add_sender()`
- Dependency injection with `get_sender()`
- Health check endpoint
- Authentication endpoints (register, forgot password)
- Team invitation endpoint

```bash
EMAIL_FROM=noreply@example.com uvicorn fastapi_integration:app --reload
```

## Environment Variables

### Required

- `EMAIL_FROM`: Default sender email address

### Backend Selection

Set `EMAIL_BACKEND` to explicitly choose a backend, or let it auto-detect:

- `console`: Print emails to stdout (development)
- `smtp`: Standard SMTP server
- `resend`: Resend API
- `sendgrid`: SendGrid API
- `ses`: AWS Simple Email Service
- `postmark`: Postmark API

### Provider-Specific Variables

**SMTP:**
```bash
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=user@gmail.com
EMAIL_SMTP_PASSWORD=app-password
```

**Resend:**
```bash
EMAIL_RESEND_API_KEY=re_xxx
```

**SendGrid:**
```bash
EMAIL_SENDGRID_API_KEY=SG.xxx
```

**AWS SES:**
```bash
EMAIL_SES_REGION=us-east-1
# Uses default AWS credential chain
```

**Postmark:**
```bash
EMAIL_POSTMARK_API_TOKEN=xxx
EMAIL_POSTMARK_MESSAGE_STREAM=outbound
```

## Quick Start

1. Install dependencies:
   ```bash
   pip install svc-infra[email]
   # Or for templates:
   pip install svc-infra[email-templates]
   ```

2. Set environment variables:
   ```bash
   export EMAIL_FROM=noreply@example.com
   # For production, set EMAIL_BACKEND and provider credentials
   ```

3. Run an example:
   ```bash
   python basic_send.py
   ```
