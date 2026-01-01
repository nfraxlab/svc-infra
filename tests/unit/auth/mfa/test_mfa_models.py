"""Tests for svc_infra.api.fastapi.auth.mfa.models module."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from svc_infra.api.fastapi.auth.mfa.models import (
    ConfirmSetupIn,
    DeleteAccountIn,
    DisableAccountIn,
    DisableMFAIn,
    MFAProof,
    MFAStatusOut,
    RecoveryCodesOut,
    SendEmailCodeIn,
    SendEmailCodeOut,
    StartSetupOut,
    VerifyMFAIn,
)


class TestStartSetupOut:
    """Tests for StartSetupOut model."""

    def test_create_with_required_fields(self) -> None:
        """Should create with required otpauth_url and secret."""
        out = StartSetupOut(
            otpauth_url="otpauth://totp/App:user@example.com?secret=ABC123",
            secret="ABC123",
        )
        assert out.otpauth_url.startswith("otpauth://")
        assert out.secret == "ABC123"
        assert out.qr_svg is None

    def test_create_with_qr_svg(self) -> None:
        """Should accept optional qr_svg."""
        out = StartSetupOut(
            otpauth_url="otpauth://totp/App:user@example.com?secret=ABC123",
            secret="ABC123",
            qr_svg="<svg>...</svg>",
        )
        assert out.qr_svg == "<svg>...</svg>"

    def test_missing_required_fields(self) -> None:
        """Should fail without required fields."""
        with pytest.raises(ValidationError):
            StartSetupOut()  # type: ignore[call-arg]


class TestConfirmSetupIn:
    """Tests for ConfirmSetupIn model."""

    def test_create_with_code(self) -> None:
        """Should create with code."""
        inp = ConfirmSetupIn(code="123456")
        assert inp.code == "123456"

    def test_missing_code(self) -> None:
        """Should fail without code."""
        with pytest.raises(ValidationError):
            ConfirmSetupIn()  # type: ignore[call-arg]


class TestVerifyMFAIn:
    """Tests for VerifyMFAIn model."""

    def test_create_with_required_fields(self) -> None:
        """Should create with code and pre_token."""
        inp = VerifyMFAIn(code="123456", pre_token="jwt-token-here")
        assert inp.code == "123456"
        assert inp.pre_token == "jwt-token-here"

    def test_missing_fields(self) -> None:
        """Should fail without required fields."""
        with pytest.raises(ValidationError):
            VerifyMFAIn(code="123456")  # type: ignore[call-arg]


class TestDisableMFAIn:
    """Tests for DisableMFAIn model."""

    def test_create_with_code(self) -> None:
        """Should create with TOTP code."""
        inp = DisableMFAIn(code="123456")
        assert inp.code == "123456"
        assert inp.recovery_code is None

    def test_create_with_recovery_code(self) -> None:
        """Should create with recovery code."""
        inp = DisableMFAIn(recovery_code="ABCD-EFGH-1234")
        assert inp.code is None
        assert inp.recovery_code == "ABCD-EFGH-1234"

    def test_create_empty(self) -> None:
        """Should allow empty (both optional)."""
        inp = DisableMFAIn()
        assert inp.code is None
        assert inp.recovery_code is None


class TestRecoveryCodesOut:
    """Tests for RecoveryCodesOut model."""

    def test_create_with_codes(self) -> None:
        """Should create with list of codes."""
        out = RecoveryCodesOut(codes=["ABC123", "DEF456", "GHI789"])
        assert len(out.codes) == 3
        assert "ABC123" in out.codes

    def test_empty_codes_list(self) -> None:
        """Should allow empty codes list."""
        out = RecoveryCodesOut(codes=[])
        assert out.codes == []


class TestSendEmailCodeIn:
    """Tests for SendEmailCodeIn model."""

    def test_create_with_pre_token(self) -> None:
        """Should create with pre_token."""
        inp = SendEmailCodeIn(pre_token="jwt-token-here")
        assert inp.pre_token == "jwt-token-here"

    def test_missing_pre_token(self) -> None:
        """Should fail without pre_token."""
        with pytest.raises(ValidationError):
            SendEmailCodeIn()  # type: ignore[call-arg]


class TestSendEmailCodeOut:
    """Tests for SendEmailCodeOut model."""

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        out = SendEmailCodeOut()
        assert out.sent is True
        assert out.cooldown_seconds == 60

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        out = SendEmailCodeOut(sent=False, cooldown_seconds=120)
        assert out.sent is False
        assert out.cooldown_seconds == 120


class TestMFAStatusOut:
    """Tests for MFAStatusOut model."""

    def test_mfa_disabled_status(self) -> None:
        """Should represent disabled MFA status."""
        status = MFAStatusOut(enabled=False, methods=[])
        assert status.enabled is False
        assert status.methods == []
        assert status.confirmed_at is None
        assert status.email_mask is None

    def test_mfa_enabled_with_totp(self) -> None:
        """Should represent enabled MFA with TOTP."""
        now = datetime.now()
        status = MFAStatusOut(
            enabled=True,
            methods=["totp"],
            confirmed_at=now,
        )
        assert status.enabled is True
        assert "totp" in status.methods
        assert status.confirmed_at == now

    def test_mfa_with_email_mask(self) -> None:
        """Should include email mask."""
        status = MFAStatusOut(
            enabled=True,
            methods=["email"],
            email_mask="u***@example.com",
        )
        assert status.email_mask == "u***@example.com"


class TestMFAProof:
    """Tests for MFAProof model."""

    def test_create_with_code(self) -> None:
        """Should create with TOTP code."""
        proof = MFAProof(code="123456")
        assert proof.code == "123456"
        assert proof.pre_token is None

    def test_create_with_pre_token(self) -> None:
        """Should create with pre_token for email OTP."""
        proof = MFAProof(pre_token="jwt-token")
        assert proof.code is None
        assert proof.pre_token == "jwt-token"

    def test_create_with_both(self) -> None:
        """Should create with both code and pre_token."""
        proof = MFAProof(code="123456", pre_token="jwt-token")
        assert proof.code == "123456"
        assert proof.pre_token == "jwt-token"

    def test_create_empty(self) -> None:
        """Should allow empty (both optional)."""
        proof = MFAProof()
        assert proof.code is None
        assert proof.pre_token is None


class TestDisableAccountIn:
    """Tests for DisableAccountIn model."""

    def test_create_with_reason(self) -> None:
        """Should create with reason."""
        inp = DisableAccountIn(reason="Taking a break")
        assert inp.reason == "Taking a break"
        assert inp.mfa is None

    def test_create_with_mfa_proof(self) -> None:
        """Should create with MFA proof."""
        inp = DisableAccountIn(mfa=MFAProof(code="123456"))
        assert inp.mfa is not None
        assert inp.mfa.code == "123456"

    def test_create_empty(self) -> None:
        """Should allow empty."""
        inp = DisableAccountIn()
        assert inp.reason is None
        assert inp.mfa is None


class TestDeleteAccountIn:
    """Tests for DeleteAccountIn model."""

    def test_create_with_mfa_proof(self) -> None:
        """Should create with MFA proof."""
        inp = DeleteAccountIn(mfa=MFAProof(code="123456"))
        assert inp.mfa is not None
        assert inp.mfa.code == "123456"

    def test_create_empty(self) -> None:
        """Should allow empty."""
        inp = DeleteAccountIn()
        assert inp.mfa is None
