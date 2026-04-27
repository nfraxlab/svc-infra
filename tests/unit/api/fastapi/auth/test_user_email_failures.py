from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from svc_infra.api.fastapi.auth.email import (
    AuthEmailConfig,
    AuthEmailMessage,
    AuthEmailTemplateConfig,
    _build_auth_action_url,
    _build_auth_email_message,
    _send_auth_email,
)


def test_send_auth_email_calls_sender() -> None:
    sender = MagicMock()
    sender.app_name = "Acme"
    sender.app_url = "https://app.acme.com"
    sender.support_email = "support@acme.com"
    sender.unsubscribe_url = ""
    sender.template_loader = None
    user = SimpleNamespace(email="user@example.com", full_name="Jane Doe")

    with patch("svc_infra.api.fastapi.auth.email._resolve_auth_email_sender", return_value=sender):
        _send_auth_email(
            kind="verification",
            user=user,
            token="abc123",
            request=None,
            config=None,
            unavailable_message="Verification email is temporarily unavailable.",
        )

    sender.send_sync.assert_called_once()
    send_kwargs = sender.send_sync.call_args.kwargs
    assert send_kwargs["to"] == "user@example.com"
    assert send_kwargs["subject"] == "Verify Your Email - Acme"
    assert send_kwargs["template"] is None
    assert "Verify Email Address" in send_kwargs["html"]
    assert send_kwargs["text"] is not None


def test_send_auth_email_uses_custom_template_config() -> None:
    sender = MagicMock()
    sender.app_name = "Acme"
    sender.app_url = "https://app.acme.com"
    sender.support_email = "support@acme.com"
    sender.unsubscribe_url = ""
    sender.template_loader = object()
    user = SimpleNamespace(email="user@example.com", full_name="Jane Doe")
    config = AuthEmailConfig(
        frontend_url="https://auth.acme.com",
        verification=AuthEmailTemplateConfig(
            path="/welcome/verify",
            subject=lambda ctx: f"Welcome to {ctx.app_name}",
            template="company_verify",
            expires_in="3 days",
            tags=lambda ctx: [ctx.kind, "brand"],
            context_builder=lambda ctx: {"headline": f"Hello {ctx.user_name}"},
        ),
    )

    with patch("svc_infra.api.fastapi.auth.email._resolve_auth_email_sender", return_value=sender):
        _send_auth_email(
            kind="verification",
            user=user,
            token="abc123",
            request=None,
            config=config,
            unavailable_message="Verification email is temporarily unavailable.",
        )

    sender.send_sync.assert_called_once_with(
        to="user@example.com",
        subject="Welcome to Acme",
        html=None,
        text=None,
        template="company_verify",
        context={
            "action_url": "https://auth.acme.com/welcome/verify?token=abc123",
            "token": "abc123",
            "recipient": "user@example.com",
            "user_name": "Jane Doe",
            "expires_in": "3 days",
            "app_name": "Acme",
            "app_url": "https://app.acme.com",
            "support_email": "support@acme.com",
            "unsubscribe_url": "",
            "verification_url": "https://auth.acme.com/welcome/verify?token=abc123",
            "headline": "Hello Jane Doe",
        },
        from_addr=None,
        reply_to=None,
        cc=None,
        bcc=None,
        headers=None,
        tags=["verification", "brand"],
        metadata=None,
    )


def test_send_auth_email_wraps_sender_failures() -> None:
    sender = MagicMock()
    sender.app_name = "Acme"
    sender.app_url = "https://app.acme.com"
    sender.support_email = "support@acme.com"
    sender.unsubscribe_url = ""
    sender.template_loader = None
    sender.send_sync.side_effect = RuntimeError("boom")
    user = SimpleNamespace(email="user@example.com", full_name="Jane Doe")

    with patch("svc_infra.api.fastapi.auth.email._resolve_auth_email_sender", return_value=sender):
        with pytest.raises(HTTPException) as exc_info:
            _send_auth_email(
                kind="verification",
                user=user,
                token="abc123",
                request=None,
                config=None,
                unavailable_message="Verification email is temporarily unavailable.",
            )

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail == {
        "code": "EMAIL_DELIVERY_UNAVAILABLE",
        "message": "Verification email is temporarily unavailable.",
    }


def test_build_auth_action_url_prefers_frontend_url() -> None:
    with patch.dict("os.environ", {"FRONTEND_URL": "https://pulse.nfrax.com/"}, clear=False):
        url = _build_auth_action_url(path="/verify", token="abc+123")

    assert url == "https://pulse.nfrax.com/verify?token=abc%2B123"


def test_build_auth_action_url_falls_back_to_request_base_url() -> None:
    request = SimpleNamespace(base_url="https://preview.api.pulse.nfrax.com/")

    with patch.dict("os.environ", {}, clear=True):
        url = _build_auth_action_url(path="/reset-password", token="abc123", request=request)

    assert url == "https://preview.api.pulse.nfrax.com/reset-password?token=abc123"


def test_build_auth_action_url_prefers_configured_frontend_url() -> None:
    request = SimpleNamespace(base_url="https://preview.api.pulse.nfrax.com/")

    url = _build_auth_action_url(
        path="/verify",
        token="abc123",
        request=request,
        frontend_url="https://accounts.acme.com",
    )

    assert url == "https://accounts.acme.com/verify?token=abc123"


def test_build_auth_email_message_uses_custom_renderer() -> None:
    sender = MagicMock()
    sender.app_name = "Acme"
    sender.app_url = "https://app.acme.com"
    sender.support_email = "support@acme.com"
    sender.unsubscribe_url = ""
    sender.template_loader = object()
    user = SimpleNamespace(email="user@example.com", full_name="Jane Doe")
    config = AuthEmailConfig(
        frontend_url="https://auth.acme.com",
        password_reset=AuthEmailTemplateConfig(
            path="/security/reset",
            render=lambda ctx: AuthEmailMessage(
                subject=f"Reset for {ctx.user_name}",
                html=f"<strong>{ctx.action_url}</strong>",
                text=ctx.action_url,
                headers={"X-Customer": "acme"},
                metadata={"flow": ctx.kind},
                tags=["custom-reset"],
            ),
        ),
    )

    message = _build_auth_email_message(
        kind="password_reset",
        user=user,
        token="abc123",
        request=None,
        config=config,
        sender=sender,
    )

    assert message.subject == "Reset for Jane Doe"
    assert message.html == "<strong>https://auth.acme.com/security/reset?token=abc123</strong>"
    assert message.text == "https://auth.acme.com/security/reset?token=abc123"
    assert message.headers == {"X-Customer": "acme"}
    assert message.metadata == {"flow": "password_reset"}
    assert message.tags == ["custom-reset"]
