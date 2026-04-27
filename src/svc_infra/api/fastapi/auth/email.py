from __future__ import annotations

import html
import logging
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from urllib.parse import quote

from fastapi import HTTPException, status

from svc_infra.email import EmailSender, easy_sender

logger = logging.getLogger(__name__)

AuthEmailKind = Literal["verification", "password_reset"]


@dataclass(frozen=True)
class AuthEmailContext:
    """Resolved context passed to auth email subject/context/render hooks."""

    kind: AuthEmailKind
    user: Any
    token: str
    request: Any | None
    recipient: str
    user_name: str | None
    action_url: str
    expires_in: str
    app_name: str
    app_url: str
    support_email: str
    unsubscribe_url: str
    templates_available: bool


@dataclass(frozen=True)
class AuthEmailMessage:
    """Fully rendered auth email payload."""

    subject: str
    template: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    html: str | None = None
    text: str | None = None
    from_addr: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    headers: dict[str, str] | None = None
    tags: list[str] | None = None
    metadata: dict[str, str] | None = None


class AuthEmailRenderer(Protocol):
    """Protocol for fully custom auth email renderers."""

    def __call__(self, context: AuthEmailContext) -> AuthEmailMessage: ...


@dataclass(frozen=True)
class AuthEmailTemplateConfig:
    """Per-email customization for auth flows."""

    path: str
    subject: str | Callable[[AuthEmailContext], str] | None = None
    template: str | None = None
    expires_in: str | None = None
    tags: list[str] | Callable[[AuthEmailContext], list[str]] | None = None
    metadata: dict[str, str] | Callable[[AuthEmailContext], dict[str, str]] | None = None
    context_builder: Callable[[AuthEmailContext], Mapping[str, Any]] | None = None
    render: AuthEmailRenderer | None = None


def _default_verification_config() -> AuthEmailTemplateConfig:
    return AuthEmailTemplateConfig(
        path="/verify",
        template="verification",
        expires_in="24 hours",
        tags=["verification", "transactional"],
    )


def _default_password_reset_config() -> AuthEmailTemplateConfig:
    return AuthEmailTemplateConfig(
        path="/reset-password",
        template="password_reset",
        expires_in="1 hour",
        tags=["password_reset", "transactional"],
    )


@dataclass(frozen=True)
class AuthEmailConfig:
    """Top-level auth email customization for add_auth_users/get_fastapi_users."""

    frontend_url: str | None = None
    app_name: str = "Our Service"
    app_url: str | None = None
    support_email: str = ""
    unsubscribe_url: str = ""
    sender: EmailSender | None = None
    sender_factory: Callable[[], EmailSender] | None = None
    verification: AuthEmailTemplateConfig = field(default_factory=_default_verification_config)
    password_reset: AuthEmailTemplateConfig = field(default_factory=_default_password_reset_config)


def _build_auth_action_url(
    *,
    path: str,
    token: str,
    request: Any | None = None,
    frontend_url: str | None = None,
) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"
    encoded_token = quote(token, safe="")

    resolved_frontend_url = (frontend_url or os.environ.get("FRONTEND_URL", "")).strip()
    if resolved_frontend_url:
        return f"{resolved_frontend_url.rstrip('/')}{normalized_path}?token={encoded_token}"

    if request is not None and getattr(request, "base_url", None) is not None:
        return f"{str(request.base_url).rstrip('/')}{normalized_path}?token={encoded_token}"

    return f"{normalized_path}?token={encoded_token}"


def _resolve_auth_email_sender(config: AuthEmailConfig | None) -> EmailSender:
    if config and config.sender is not None:
        return config.sender

    if config and config.sender_factory is not None:
        return config.sender_factory()

    frontend_url = (config.frontend_url if config else None) or os.environ.get("FRONTEND_URL", "")
    app_url = config.app_url if config and config.app_url is not None else frontend_url

    return easy_sender(
        app_name=config.app_name if config else "Our Service",
        app_url=app_url or "",
        support_email=config.support_email if config else "",
        unsubscribe_url=config.unsubscribe_url if config else "",
    )


def _resolve_subject(
    value: str | Callable[[AuthEmailContext], str] | None,
    *,
    context: AuthEmailContext,
) -> str:
    if callable(value):
        return value(context)
    if value is not None:
        return value
    if context.kind == "verification":
        return f"Verify Your Email - {context.app_name}"
    return f"Reset Your Password - {context.app_name}"


def _resolve_tags(
    value: list[str] | Callable[[AuthEmailContext], list[str]] | None,
    *,
    context: AuthEmailContext,
) -> list[str] | None:
    if callable(value):
        return value(context)
    return value


def _resolve_metadata(
    value: dict[str, str] | Callable[[AuthEmailContext], dict[str, str]] | None,
    *,
    context: AuthEmailContext,
) -> dict[str, str] | None:
    if callable(value):
        return value(context)
    return value


def _build_default_template_context(context: AuthEmailContext) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action_url": context.action_url,
        "token": context.token,
        "recipient": context.recipient,
        "user_name": context.user_name,
        "expires_in": context.expires_in,
        "app_name": context.app_name,
        "app_url": context.app_url,
        "support_email": context.support_email,
        "unsubscribe_url": context.unsubscribe_url,
    }
    if context.kind == "verification":
        payload["verification_url"] = context.action_url
    else:
        payload["reset_url"] = context.action_url
    return payload


def _build_fallback_message(
    *,
    context: AuthEmailContext,
    subject: str,
    tags: list[str] | None,
    metadata: dict[str, str] | None,
) -> AuthEmailMessage:
    display_name = html.escape(context.user_name or "there")
    escaped_url = html.escape(context.action_url, quote=True)

    if context.kind == "verification":
        html_body = f"""
            <p>Hi {display_name},</p>
            <p>Please verify your email address to finish setting up your account.</p>
            <p><a href="{escaped_url}">Verify Email Address</a></p>
            <p>If the button does not work, copy and paste this link into your browser:</p>
            <p><a href="{escaped_url}">{escaped_url}</a></p>
            <p>This link expires in {html.escape(context.expires_in)}.</p>
        """
        text_body = (
            f"Hi {context.user_name or 'there'},\n\n"
            "Please verify your email address to finish setting up your account.\n\n"
            f"Verify Email Address: {context.action_url}\n\n"
            f"This link expires in {context.expires_in}."
        )
    else:
        html_body = f"""
            <p>Hi {display_name},</p>
            <p>We received a request to reset your password.</p>
            <p><a href="{escaped_url}">Reset Your Password</a></p>
            <p>If the button does not work, copy and paste this link into your browser:</p>
            <p><a href="{escaped_url}">{escaped_url}</a></p>
            <p>This link expires in {html.escape(context.expires_in)}.</p>
            <p>If you did not request this, you can ignore this email.</p>
        """
        text_body = (
            f"Hi {context.user_name or 'there'},\n\n"
            "We received a request to reset your password.\n\n"
            f"Reset Your Password: {context.action_url}\n\n"
            f"This link expires in {context.expires_in}.\n\n"
            "If you did not request this, you can ignore this email."
        )

    return AuthEmailMessage(
        subject=subject,
        html=html_body,
        text=text_body,
        tags=tags,
        metadata=metadata,
    )


def _build_auth_email_message(
    *,
    kind: AuthEmailKind,
    user: Any,
    token: str,
    request: Any | None,
    config: AuthEmailConfig | None,
    sender: EmailSender,
) -> AuthEmailMessage:
    resolved_config = config or AuthEmailConfig()
    variant = (
        resolved_config.verification if kind == "verification" else resolved_config.password_reset
    )
    recipient = str(user.email)

    action_url = _build_auth_action_url(
        path=variant.path,
        token=token,
        request=request,
        frontend_url=resolved_config.frontend_url,
    )
    context = AuthEmailContext(
        kind=kind,
        user=user,
        token=token,
        request=request,
        recipient=recipient,
        user_name=getattr(user, "full_name", None),
        action_url=action_url,
        expires_in=variant.expires_in or ("24 hours" if kind == "verification" else "1 hour"),
        app_name=getattr(sender, "app_name", "Our Service") or "Our Service",
        app_url=getattr(sender, "app_url", "")
        or (resolved_config.app_url or resolved_config.frontend_url or ""),
        support_email=getattr(sender, "support_email", "") or resolved_config.support_email,
        unsubscribe_url=getattr(sender, "unsubscribe_url", "") or resolved_config.unsubscribe_url,
        templates_available=getattr(sender, "template_loader", None) is not None,
    )

    if variant.render is not None:
        return variant.render(context)

    subject = _resolve_subject(variant.subject, context=context)
    tags = _resolve_tags(variant.tags, context=context)
    metadata = _resolve_metadata(variant.metadata, context=context)

    template_context = _build_default_template_context(context)
    if variant.context_builder is not None:
        template_context.update(dict(variant.context_builder(context)))

    if context.templates_available and variant.template:
        return AuthEmailMessage(
            subject=subject,
            template=variant.template,
            context=template_context,
            tags=tags,
            metadata=metadata,
        )

    return _build_fallback_message(
        context=context,
        subject=subject,
        tags=tags,
        metadata=metadata,
    )


def _send_auth_email(
    *,
    kind: AuthEmailKind,
    user: Any,
    token: str,
    request: Any | None,
    config: AuthEmailConfig | None,
    unavailable_message: str,
) -> None:
    try:
        sender = _resolve_auth_email_sender(config)
        recipient = str(user.email)
        message = _build_auth_email_message(
            kind=kind,
            user=user,
            token=token,
            request=request,
            config=config,
            sender=sender,
        )
        sender.send_sync(
            to=recipient,
            subject=message.subject,
            html=message.html,
            text=message.text,
            template=message.template,
            context=message.context,
            from_addr=message.from_addr,
            reply_to=message.reply_to,
            cc=message.cc,
            bcc=message.bcc,
            headers=message.headers,
            tags=message.tags,
            metadata=message.metadata,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to send auth email",
            extra={
                "recipient": getattr(user, "email", None),
                "kind": kind,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "EMAIL_DELIVERY_UNAVAILABLE",
                "message": unavailable_message,
            },
        ) from None
