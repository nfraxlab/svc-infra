"""
Email backends.

This module provides email backend implementations:
- ConsoleBackend: Development backend that prints to console
- SMTPBackend: Standard SMTP with async (aiosmtplib) and sync (smtplib) support
- ResendBackend: Modern transactional email via Resend API
- SendGridBackend: Enterprise email via SendGrid API
- SESBackend: AWS Simple Email Service
- PostmarkBackend: Transactional email via Postmark API
- MailgunBackend: Transactional email via Mailgun API (EU data residency)
- BrevoBackend: Transactional email via Brevo API (formerly Sendinblue)
"""

from __future__ import annotations

from .brevo import BrevoBackend
from .console import ConsoleBackend
from .mailgun import MailgunBackend
from .postmark import PostmarkBackend
from .resend import ResendBackend
from .sendgrid import SendGridBackend
from .ses import SESBackend
from .smtp import SMTPBackend

__all__ = [
    "BrevoBackend",
    "ConsoleBackend",
    "MailgunBackend",
    "PostmarkBackend",
    "ResendBackend",
    "SendGridBackend",
    "SESBackend",
    "SMTPBackend",
]
