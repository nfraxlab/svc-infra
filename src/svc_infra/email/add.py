"""
FastAPI integration for email system.

Provides helpers to integrate email backends with FastAPI applications.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, FastAPI, Request

from .base import ConfigurationError, EmailBackend

if TYPE_CHECKING:
    from .sender import EmailSender

logger = logging.getLogger(__name__)


_app_email_backend: EmailBackend | None = None
_app_email_sender: EmailSender | None = None


def add_email(
    app: FastAPI,
    backend: EmailBackend | None = None,
) -> EmailBackend:
    """
    Add email backend to FastAPI application.

    This function:
    - Stores backend in app.state.email
    - Registers startup/shutdown hooks
    - Adds health check integration

    Args:
        app: FastAPI application instance
        backend: Email backend instance (auto-detected if None)

    Returns:
        Email backend instance

    Example:
        >>> from fastapi import FastAPI
        >>> from svc_infra.email import add_email, easy_email
        >>>
        >>> app = FastAPI()
        >>>
        >>> # Auto-detect backend from environment
        >>> email = add_email(app)
        >>>
        >>> # Explicit backend
        >>> from svc_infra.email.backends import ResendBackend
        >>> backend = ResendBackend(api_key="re_xxx")
        >>> email = add_email(app, backend)

    Note:
        In production, ensure EMAIL_FROM is set for the default sender.
    """
    global _app_email_backend

    # Auto-detect backend if not provided
    if backend is None:
        from .easy import easy_email

        backend = easy_email()

    # Store in app state and module-level for dependency injection
    app.state.email = backend
    _app_email_backend = backend

    # Get existing lifespan or create new one
    existing_lifespan = getattr(app.router, "lifespan_context", None)

    @asynccontextmanager
    async def email_lifespan(app: FastAPI):
        # Startup
        logger.info(f"Email backend initialized: {backend.provider_name}")

        # Call existing lifespan if present
        if existing_lifespan is not None:
            async with existing_lifespan(app):
                yield
        else:
            yield

        # Shutdown
        logger.info("Email backend shutdown")

    # Replace lifespan
    app.router.lifespan_context = email_lifespan

    return backend


def get_email_from_request(request: Request) -> EmailBackend:
    """
    Get email backend from FastAPI request.

    This is used internally by the get_email dependency.

    Args:
        request: FastAPI request object

    Returns:
        Email backend from app state

    Raises:
        ConfigurationError: If email not configured via add_email()
    """
    email = getattr(request.app.state, "email", None)
    if email is None:
        raise ConfigurationError(
            "Email backend not configured. Call add_email(app) during startup."
        )
    return email


def get_email() -> EmailBackend:
    """
    FastAPI dependency to get the email backend.

    Use this as a dependency in your route handlers to access the
    configured email backend.

    Returns:
        Email backend instance

    Raises:
        ConfigurationError: If email not configured via add_email()

    Example:
        >>> from fastapi import Depends
        >>> from svc_infra.email import get_email, EmailBackend, EmailMessage
        >>>
        >>> @router.post("/notify")
        >>> async def notify_user(
        ...     user_email: str,
        ...     email: EmailBackend = Depends(get_email),
        ... ):
        ...     result = await email.send(EmailMessage(
        ...         to=user_email,
        ...         subject="Notification",
        ...         html="<p>You have a new notification.</p>",
        ...     ))
        ...     return {"message_id": result.message_id}
    """
    global _app_email_backend

    if _app_email_backend is None:
        raise ConfigurationError(
            "Email backend not configured. Call add_email(app) during startup."
        )
    return _app_email_backend


# Type alias for dependency injection
EmailDep = Annotated[EmailBackend, Depends(get_email)]


async def health_check_email() -> dict:
    """
    Health check for email backend.

    Returns status information about the email system. Can be integrated
    with FastAPI health check endpoints.

    Returns:
        Dict with email health status

    Example:
        >>> from svc_infra.email import health_check_email
        >>>
        >>> @app.get("/health/email")
        >>> async def email_health():
        ...     return await health_check_email()

    Response:
        {
            "status": "healthy",
            "provider": "resend",
            "configured": True
        }
    """
    global _app_email_backend

    if _app_email_backend is None:
        return {
            "status": "unconfigured",
            "provider": None,
            "configured": False,
        }

    return {
        "status": "healthy",
        "provider": _app_email_backend.provider_name,
        "configured": True,
    }


def add_sender(
    app: FastAPI,
    backend: EmailBackend | None = None,
    *,
    app_name: str = "Our Service",
    app_url: str = "",
    support_email: str = "",
    unsubscribe_url: str = "",
) -> EmailSender:
    """
    Add EmailSender to FastAPI application.

    This is the recommended high-level API that provides:
    - Template rendering with built-in templates
    - Convenience methods (send_verification, send_password_reset, etc.)
    - Recipient validation
    - Settings-based defaults

    Args:
        app: FastAPI application instance
        backend: Email backend instance (auto-detected if None)
        app_name: Application name for templates
        app_url: Application URL for templates
        support_email: Support email for templates
        unsubscribe_url: Unsubscribe URL for templates

    Returns:
        EmailSender instance

    Example:
        >>> from fastapi import FastAPI, Depends
        >>> from svc_infra.email import add_sender, get_sender, EmailSender
        >>>
        >>> app = FastAPI()
        >>> sender = add_sender(app, app_name="MyApp", app_url="https://myapp.com")
        >>>
        >>> @app.post("/send-welcome")
        >>> async def send_welcome(
        ...     email: str,
        ...     sender: EmailSender = Depends(get_sender),
        ... ):
        ...     result = await sender.send_welcome(to=email, user_name="New User")
        ...     return {"message_id": result.message_id}
    """
    global _app_email_sender, _app_email_backend

    from .sender import EmailSender

    # Auto-detect backend if not provided
    if backend is None:
        from .easy import easy_email

        backend = easy_email()

    # Store backend for backward compatibility
    app.state.email = backend
    _app_email_backend = backend

    # Create sender wrapper
    sender = EmailSender(
        backend=backend,
        app_name=app_name,
        app_url=app_url,
        support_email=support_email,
        unsubscribe_url=unsubscribe_url,
    )

    # Store sender in app state
    app.state.email_sender = sender
    _app_email_sender = sender

    # Get existing lifespan or create new one
    existing_lifespan = getattr(app.router, "lifespan_context", None)

    @asynccontextmanager
    async def email_lifespan(app: FastAPI):
        # Startup
        logger.info(f"Email sender initialized: {backend.provider_name}")

        # Call existing lifespan if present
        if existing_lifespan is not None:
            async with existing_lifespan(app):
                yield
        else:
            yield

        # Shutdown
        logger.info("Email sender shutdown")

    # Replace lifespan
    app.router.lifespan_context = email_lifespan

    return sender


def get_sender() -> EmailSender:
    """
    FastAPI dependency to get the EmailSender.

    Use this as a dependency in your route handlers to access the
    configured email sender with template support.

    Returns:
        EmailSender instance

    Raises:
        ConfigurationError: If email not configured via add_sender()

    Example:
        >>> from fastapi import Depends
        >>> from svc_infra.email import get_sender, EmailSender
        >>>
        >>> @router.post("/send-verification")
        >>> async def send_verification(
        ...     user_email: str,
        ...     sender: EmailSender = Depends(get_sender),
        ... ):
        ...     result = await sender.send_verification(
        ...         to=user_email,
        ...         code="123456",
        ...     )
        ...     return {"message_id": result.message_id}
    """
    global _app_email_sender

    if _app_email_sender is None:
        raise ConfigurationError(
            "Email sender not configured. Call add_sender(app) during startup."
        )
    return _app_email_sender


# Type alias for high-level dependency injection
SenderDep = Annotated["EmailSender", Depends(get_sender)]
