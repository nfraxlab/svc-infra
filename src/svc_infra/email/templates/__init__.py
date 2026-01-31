"""
Email template system.

Provides Jinja2-based email templating with built-in templates for common
authentication and notification flows.

Quick Start:
    >>> from svc_infra.email.templates import EmailTemplateLoader
    >>>
    >>> # Use built-in templates
    >>> loader = EmailTemplateLoader()
    >>> html, text = loader.render("verification", code="123456", user_name="John")
    >>>
    >>> # Use custom templates directory
    >>> loader = EmailTemplateLoader(template_dir="/path/to/templates")
    >>> html, text = loader.render("welcome", **context)

Built-in Templates:
    - base: Base responsive layout (used by all others)
    - verification: Email verification with code
    - password_reset: Password reset link
    - invitation: Team/workspace invitation
    - welcome: Welcome/onboarding email
"""

from __future__ import annotations

from svc_infra.email.templates.loader import EmailTemplateLoader

__all__ = [
    "EmailTemplateLoader",
]
