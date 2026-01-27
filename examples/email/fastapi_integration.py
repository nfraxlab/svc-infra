#!/usr/bin/env python3
"""
FastAPI integration example.

Demonstrates how to integrate the email module with FastAPI:
- Application setup with add_sender()
- Dependency injection with get_sender()
- Health check endpoint
- Common email endpoints (verification, password reset, invitations)

Environment Variables:
    EMAIL_FROM: Sender email address (required for sending)
    EMAIL_BACKEND: Backend type (console, smtp, resend, sendgrid, ses, postmark)

Usage:
    EMAIL_FROM=noreply@example.com uvicorn fastapi_integration:app --reload

    # Test endpoints:
    curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d '{"email": "user@example.com", "name": "John"}'
    curl http://localhost:8000/health/email
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from svc_infra.email import (
    EmailSender,
    add_sender,
    get_sender,
    health_check_email,
)

# ─── Application Setup ─────────────────────────────────────────────────────

app = FastAPI(
    title="Email Integration Example",
    description="Demonstrates svc-infra email module integration with FastAPI",
    version="1.0.0",
)

# Initialize email sender on app startup
# This auto-detects the backend from environment variables
sender = add_sender(
    app,
    app_name="MyApp",
    app_url="https://myapp.com",
    support_email="support@myapp.com",
)


# ─── Request/Response Models ───────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    name: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""

    email: EmailStr


class InviteRequest(BaseModel):
    """Team invitation request."""

    email: EmailStr
    workspace_name: str
    role: str = "Member"
    message: str | None = None


class EmailResponse(BaseModel):
    """Generic email response."""

    success: bool
    message_id: str | None = None
    message: str


# ─── Health Check ──────────────────────────────────────────────────────────


@app.get("/health/email")
async def email_health():
    """
    Check email system health.

    Returns the email provider status and configuration state.
    """
    return await health_check_email()


# ─── Authentication Endpoints ──────────────────────────────────────────────


@app.post("/auth/register", response_model=EmailResponse)
async def register(
    request: RegisterRequest,
    email_sender: EmailSender = Depends(get_sender),
):
    """
    Register a new user and send verification email.

    In a real application, you would:
    1. Create the user in your database
    2. Generate a verification token
    3. Send the verification email
    """
    # In production, generate a real token and store it
    verification_token = "abc123xyz"

    try:
        result = await email_sender.send_verification(
            to=request.email,
            verification_url=f"https://myapp.com/verify?token={verification_token}",
            user_name=request.name,
            expires_in="24 hours",
        )

        return EmailResponse(
            success=True,
            message_id=result.message_id,
            message="Verification email sent. Please check your inbox.",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


@app.post("/auth/forgot-password", response_model=EmailResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    email_sender: EmailSender = Depends(get_sender),
):
    """
    Send password reset email.

    In a real application, you would:
    1. Verify the user exists
    2. Generate a reset token with expiration
    3. Send the reset email
    """
    # In production, verify user exists and generate a real token
    reset_token = "reset789xyz"

    try:
        result = await email_sender.send_password_reset(
            to=request.email,
            reset_url=f"https://myapp.com/reset-password?token={reset_token}",
            user_name="User",  # In production, get from database
            expires_in="1 hour",
        )

        return EmailResponse(
            success=True,
            message_id=result.message_id,
            message="Password reset email sent if account exists.",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


# ─── Team/Workspace Endpoints ──────────────────────────────────────────────


@app.post("/team/invite", response_model=EmailResponse)
async def invite_team_member(
    request: InviteRequest,
    email_sender: EmailSender = Depends(get_sender),
):
    """
    Invite a user to join a team/workspace.

    In a real application, you would:
    1. Verify the inviter has permission
    2. Create an invitation record
    3. Generate an invitation token
    4. Send the invitation email
    """
    invitation_token = "invite456abc"

    try:
        result = await email_sender.send_invitation(
            to=request.email,
            invitation_url=f"https://myapp.com/accept-invite?token={invitation_token}",
            inviter_name="Current User",  # In production, get from auth context
            workspace_name=request.workspace_name,
            role=request.role,
            message=request.message,
        )

        return EmailResponse(
            success=True,
            message_id=result.message_id,
            message=f"Invitation sent to {request.email}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


# ─── Generic Email Endpoint ────────────────────────────────────────────────


class SendEmailRequest(BaseModel):
    """Generic email request."""

    to: EmailStr
    subject: str
    html: str | None = None
    template: str | None = None
    context: dict | None = None


@app.post("/email/send", response_model=EmailResponse)
async def send_email(
    request: SendEmailRequest,
    email_sender: EmailSender = Depends(get_sender),
):
    """
    Send a custom email.

    Can use either raw HTML or a template name.
    """
    if not request.html and not request.template:
        raise HTTPException(
            status_code=400,
            detail="Either 'html' or 'template' must be provided",
        )

    try:
        result = await email_sender.send(
            to=request.to,
            subject=request.subject,
            html=request.html,
            template=request.template,
            context=request.context or {},
        )

        return EmailResponse(
            success=True,
            message_id=result.message_id,
            message="Email sent successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


# ─── Startup Event ─────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    """Log email configuration on startup."""
    health = await health_check_email()
    print(f"Email system: {health['status']} (provider: {health.get('provider', 'none')})")


# ─── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
