"""
Email backends.

This module provides email backend implementations:
- ConsoleBackend: Development backend that prints to console
- SMTPBackend: Standard SMTP with async (aiosmtplib) and sync (smtplib) support
- ResendBackend: Modern transactional email via Resend API
- SendGridBackend: Enterprise email via SendGrid API
- SESBackend: AWS Simple Email Service
- PostmarkBackend: Transactional email via Postmark API
"""

from __future__ import annotations

from .console import ConsoleBackend
from .postmark import PostmarkBackend
from .resend import ResendBackend
from .sendgrid import SendGridBackend
from .ses import SESBackend
from .smtp import SMTPBackend

__all__ = [
    "ConsoleBackend",
    "SMTPBackend",
    "ResendBackend",
    "SendGridBackend",
    "SESBackend",
    "PostmarkBackend",
]
