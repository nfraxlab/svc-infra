#!/usr/bin/env python3
"""
Basic email sending example.

Demonstrates how to send simple HTML emails using svc-infra's email module.
The backend is auto-detected from environment variables.

Environment Variables:
    EMAIL_FROM: Sender email address (required)
    EMAIL_BACKEND: Backend type (console, smtp, resend, sendgrid, ses, postmark)

    For production, also set provider-specific variables:
    - SMTP: EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
    - Resend: EMAIL_RESEND_API_KEY
    - SendGrid: EMAIL_SENDGRID_API_KEY
    - SES: AWS_REGION (or EMAIL_SES_REGION), AWS credentials
    - Postmark: EMAIL_POSTMARK_API_TOKEN

Usage:
    # Development (prints to console)
    EMAIL_FROM=noreply@example.com python basic_send.py

    # Production with Resend
    EMAIL_FROM=noreply@example.com EMAIL_RESEND_API_KEY=re_xxx python basic_send.py
"""

from __future__ import annotations

import asyncio
import os


async def main() -> None:
    """Send a basic HTML email."""
    # Import here to ensure environment is set up first
    from svc_infra.email import easy_email

    # Ensure EMAIL_FROM is set
    if not os.environ.get("EMAIL_FROM"):
        print("Please set EMAIL_FROM environment variable")
        print("Example: EMAIL_FROM=noreply@example.com python basic_send.py")
        return

    # Create email backend (auto-detects from environment)
    email = easy_email()

    print(f"Using {email.provider_name} backend")

    # Send a simple HTML email
    result = await email.send(
        to="recipient@example.com",
        subject="Welcome to Our Service!",
        html="""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333;">Welcome!</h1>
            <p>Thank you for signing up for our service.</p>
            <p>We're excited to have you on board!</p>
            <hr style="border: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                This is an automated message. Please do not reply.
            </p>
        </body>
        </html>
        """,
    )

    print("Email sent successfully!")
    print(f"  Message ID: {result.message_id}")
    print(f"  Status: {result.status.value}")
    print(f"  Provider: {result.provider}")


async def send_to_multiple_recipients() -> None:
    """Send email to multiple recipients."""
    from svc_infra.email import easy_email

    email = easy_email()

    # Send to multiple recipients
    result = await email.send(
        to=["user1@example.com", "user2@example.com", "user3@example.com"],
        subject="Team Update",
        html="<p>Hello team! Here's your weekly update.</p>",
    )

    print(f"Sent to multiple recipients: {result.message_id}")


async def send_with_attachments() -> None:
    """Send email with attachments."""
    from svc_infra.email import easy_email
    from svc_infra.email.base import Attachment

    email = easy_email()

    # Create an attachment
    attachment = Attachment(
        filename="report.txt",
        content=b"This is the report content",
        content_type="text/plain",
    )

    result = await email.send(
        to="recipient@example.com",
        subject="Monthly Report",
        html="<p>Please find the attached report.</p>",
        attachments=[attachment],
    )

    print(f"Email with attachment sent: {result.message_id}")


def send_sync() -> None:
    """Synchronous email sending (for non-async contexts)."""
    from svc_infra.email import easy_email

    email = easy_email()

    # Use send_sync for synchronous code
    result = email.send_sync(
        to="recipient@example.com",
        subject="Sync Email",
        html="<p>This email was sent synchronously.</p>",
    )

    print(f"Sync email sent: {result.message_id}")


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())

    # Uncomment to try other examples:
    # asyncio.run(send_to_multiple_recipients())
    # asyncio.run(send_with_attachments())
    # send_sync()
