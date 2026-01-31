#!/usr/bin/env python3
"""
Template-based email sending example.

Demonstrates how to send emails using built-in templates for common use cases:
- Email verification
- Password reset
- Team/workspace invitations
- Welcome emails

The email module includes professional HTML templates with automatic
plain text generation.

Environment Variables:
    EMAIL_FROM: Sender email address (required)
    EMAIL_BACKEND: Backend type (console, smtp, resend, sendgrid, ses, postmark)

Usage:
    EMAIL_FROM=noreply@example.com python with_templates.py
"""

from __future__ import annotations

import asyncio
import os


async def send_verification_email() -> None:
    """Send email verification with a code."""
    from svc_infra.email import easy_sender

    # easy_sender includes template support
    sender = easy_sender(
        app_name="MyApp",
        app_url="https://myapp.com",
        support_email="support@myapp.com",
    )

    print(f"Using {sender.backend.provider_name} backend")

    # Send verification email with a 6-digit code
    result = await sender.send_verification(
        to="user@example.com",
        code="123456",
        user_name="John Doe",
        expires_in="24 hours",
    )

    print(f"Verification email sent: {result.message_id}")


async def send_verification_with_url() -> None:
    """Send email verification with a clickable URL."""
    from svc_infra.email import easy_sender

    sender = easy_sender(
        app_name="MyApp",
        app_url="https://myapp.com",
    )

    # Send verification email with a URL instead of code
    result = await sender.send_verification(
        to="user@example.com",
        verification_url="https://myapp.com/verify?token=abc123xyz",
        user_name="Jane Smith",
    )

    print(f"Verification URL email sent: {result.message_id}")


async def send_password_reset() -> None:
    """Send password reset email."""
    from svc_infra.email import easy_sender

    sender = easy_sender(
        app_name="MyApp",
        app_url="https://myapp.com",
        support_email="support@myapp.com",
    )

    result = await sender.send_password_reset(
        to="user@example.com",
        reset_url="https://myapp.com/reset-password?token=xyz789",
        user_name="John Doe",
        expires_in="1 hour",
    )

    print(f"Password reset email sent: {result.message_id}")


async def send_invitation() -> None:
    """Send team/workspace invitation email."""
    from svc_infra.email import easy_sender

    sender = easy_sender(
        app_name="MyApp",
        app_url="https://myapp.com",
    )

    result = await sender.send_invitation(
        to="newuser@example.com",
        invitation_url="https://myapp.com/accept-invite?token=invite123",
        inviter_name="Alice Johnson",
        workspace_name="Engineering Team",
        role="Developer",
        message="We'd love to have you join our team!",
    )

    print(f"Invitation email sent: {result.message_id}")


async def send_welcome() -> None:
    """Send welcome email after signup."""
    from svc_infra.email import easy_sender

    sender = easy_sender(
        app_name="MyApp",
        app_url="https://myapp.com",
        support_email="support@myapp.com",
    )

    result = await sender.send_welcome(
        to="user@example.com",
        user_name="John Doe",
        features=[
            "Unlimited projects",
            "Team collaboration",
            "Advanced analytics",
            "24/7 support",
        ],
        getting_started_url="https://myapp.com/docs/getting-started",
    )

    print(f"Welcome email sent: {result.message_id}")


async def send_with_custom_template() -> None:
    """Send email using a custom template."""
    from svc_infra.email import easy_sender

    sender = easy_sender(
        app_name="MyApp",
        app_url="https://myapp.com",
    )

    # Use the generic send() with a built-in template
    result = await sender.send(
        to="user@example.com",
        subject="Verify Your Email - MyApp",
        template="verification",
        context={
            "code": "ABC123",
            "user_name": "Custom User",
            "expires_in": "30 minutes",
        },
    )

    print(f"Custom template email sent: {result.message_id}")


async def main() -> None:
    """Run all template examples."""
    # Ensure EMAIL_FROM is set
    if not os.environ.get("EMAIL_FROM"):
        print("Please set EMAIL_FROM environment variable")
        print("Example: EMAIL_FROM=noreply@example.com python with_templates.py")
        return

    print("=" * 50)
    print("Template Email Examples")
    print("=" * 50)

    print("\n1. Verification Email (with code):")
    await send_verification_email()

    print("\n2. Verification Email (with URL):")
    await send_verification_with_url()

    print("\n3. Password Reset Email:")
    await send_password_reset()

    print("\n4. Invitation Email:")
    await send_invitation()

    print("\n5. Welcome Email:")
    await send_welcome()

    print("\n6. Custom Template Usage:")
    await send_with_custom_template()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
