# Branded Auth Email Templates

This directory contains a ready-to-copy set of auth email templates for teams that want to fully control verification and password-reset email copy and UI.

Included files:

- `templates/base.html` overrides the full layout, typography, colors, and footer.
- `templates/verification.html` handles email verification.
- `templates/password_reset.html` handles password reset.

## Use It In Your App

1. Copy the `templates/` directory into your application repository.
2. Point `EMAIL_TEMPLATES_PATH` at that copied directory.
3. Pass `AuthEmailConfig` into `add_auth_users(...)`.

```python
from svc_infra.api.fastapi.auth import (
    AuthEmailConfig,
    AuthEmailTemplateConfig,
    add_auth_users,
)

auth_email_config = AuthEmailConfig(
    frontend_url="https://accounts.example.com",
    app_name="Northstar",
    support_email="support@example.com",
    verification=AuthEmailTemplateConfig(
        path="/verify",
        template="verification",
    ),
    password_reset=AuthEmailTemplateConfig(
        path="/reset-password",
        template="password_reset",
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

```bash
export EMAIL_TEMPLATES_PATH=/absolute/path/to/your/templates
export EMAIL_BACKEND=resend
export EMAIL_FROM=hello@example.com
```

## What You Can Customize

- Change copy directly in `verification.html` and `password_reset.html`.
- Override `base.html` when you want full control over the layout and visual system.
- Keep only one file if you want partial overrides. `svc-infra` falls back to the built-in templates for files you do not provide.
- Use `subject`, `context_builder`, or `render` in `AuthEmailTemplateConfig` when runtime logic needs to alter the message.

## Full-Control Rendering

If templates are still too limiting, use a custom renderer:

```python
from svc_infra.api.fastapi.auth import AuthEmailMessage

AuthEmailTemplateConfig(
    path="/reset-password",
    render=lambda ctx: AuthEmailMessage(
        subject=f"Reset your {ctx.app_name} password",
        html=f"<h1>Reset Password</h1><p><a href='{ctx.action_url}'>Continue</a></p>",
        text=ctx.action_url,
    ),
)
```
