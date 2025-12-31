"""Unit tests for svc_infra.api.fastapi.auth.mfa.verify module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from svc_infra.api.fastapi.auth.mfa.verify import MFAProof, MFAResult


class TestMFAProof:
    """Tests for MFAProof model."""

    def test_default_values(self) -> None:
        """Test default values are None."""
        proof = MFAProof()

        assert proof.code is None
        assert proof.pre_token is None

    def test_with_code(self) -> None:
        """Test with code only."""
        proof = MFAProof(code="123456")

        assert proof.code == "123456"
        assert proof.pre_token is None

    def test_with_pre_token(self) -> None:
        """Test with pre_token only."""
        proof = MFAProof(pre_token="jwt-token-here")

        assert proof.code is None
        assert proof.pre_token == "jwt-token-here"

    def test_with_both(self) -> None:
        """Test with both code and pre_token."""
        proof = MFAProof(code="654321", pre_token="token123")

        assert proof.code == "654321"
        assert proof.pre_token == "token123"


class TestMFAResult:
    """Tests for MFAResult model."""

    def test_default_values(self) -> None:
        """Test default values."""
        result = MFAResult(ok=True)

        assert result.ok is True
        assert result.method == "none"
        assert result.attempts_left is None

    def test_with_method(self) -> None:
        """Test with method specified."""
        result = MFAResult(ok=True, method="totp")

        assert result.method == "totp"

    def test_with_attempts_left(self) -> None:
        """Test with attempts_left."""
        result = MFAResult(ok=False, method="email", attempts_left=2)

        assert result.ok is False
        assert result.method == "email"
        assert result.attempts_left == 2

    def test_valid_methods(self) -> None:
        """Test all valid method values."""
        for method in ["totp", "recovery", "email", "none"]:
            result = MFAResult(ok=True, method=method)
            assert result.method == method


class TestVerifyMfaForUser:
    """Tests for verify_mfa_for_user function."""

    @pytest.mark.asyncio
    async def test_returns_ok_when_mfa_disabled_and_not_required(self) -> None:
        """Test returns ok when user has MFA disabled and not required."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        user = MagicMock()
        user.mfa_enabled = False
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=None,
            require_enabled=False,
        )

        assert result.ok is True
        assert result.method == "none"

    @pytest.mark.asyncio
    async def test_returns_not_ok_when_mfa_disabled_but_required(self) -> None:
        """Test returns not ok when MFA is required but disabled."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        user = MagicMock()
        user.mfa_enabled = False
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=None,
            require_enabled=True,
        )

        assert result.ok is False
        assert result.method == "none"

    @pytest.mark.asyncio
    async def test_returns_not_ok_when_no_proof_provided(self) -> None:
        """Test returns not ok when MFA enabled but no proof."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        user = MagicMock()
        user.mfa_enabled = True
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=None,
        )

        assert result.ok is False
        assert result.method == "none"

    @pytest.mark.asyncio
    async def test_returns_not_ok_when_empty_code(self) -> None:
        """Test returns not ok when proof has empty code."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        user = MagicMock()
        user.mfa_enabled = True
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=MFAProof(code=""),
        )

        assert result.ok is False

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.mfa.verify.pyotp.TOTP")
    async def test_totp_verification_success(self, mock_totp_class: MagicMock) -> None:
        """Test successful TOTP verification."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        mock_totp = MagicMock()
        mock_totp.verify.return_value = True
        mock_totp_class.return_value = mock_totp

        user = MagicMock()
        user.mfa_enabled = True
        user.mfa_secret = "JBSWY3DPEHPK3PXP"
        user.mfa_recovery = []
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=MFAProof(code="123456"),
        )

        assert result.ok is True
        assert result.method == "totp"
        mock_totp.verify.assert_called_once_with("123456", valid_window=1)

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.mfa.verify.pyotp.TOTP")
    async def test_totp_verification_failure(self, mock_totp_class: MagicMock) -> None:
        """Test failed TOTP verification falls through."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        mock_totp = MagicMock()
        mock_totp.verify.return_value = False
        mock_totp_class.return_value = mock_totp

        user = MagicMock()
        user.mfa_enabled = True
        user.mfa_secret = "JBSWY3DPEHPK3PXP"
        user.mfa_recovery = []
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=MFAProof(code="wrong-code"),
        )

        assert result.ok is False

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.mfa.verify._hash")
    async def test_recovery_code_success(self, mock_hash: MagicMock) -> None:
        """Test successful recovery code verification."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        mock_hash.return_value = "hashed-recovery-code"

        user = MagicMock()
        user.mfa_enabled = True
        user.mfa_secret = None  # No TOTP
        user.mfa_recovery = ["hashed-recovery-code", "another-hash"]
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=MFAProof(code="my-recovery-code"),
        )

        assert result.ok is True
        assert result.method == "recovery"
        # Recovery code should be burned (removed)
        assert "hashed-recovery-code" not in user.mfa_recovery
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    @patch("svc_infra.api.fastapi.auth.mfa.verify._hash")
    async def test_invalid_recovery_code(self, mock_hash: MagicMock) -> None:
        """Test invalid recovery code fails."""
        from svc_infra.api.fastapi.auth.mfa.verify import verify_mfa_for_user

        mock_hash.return_value = "wrong-hash"

        user = MagicMock()
        user.mfa_enabled = True
        user.mfa_secret = None
        user.mfa_recovery = ["correct-hash"]
        session = AsyncMock()

        result = await verify_mfa_for_user(
            user=user,
            session=session,
            proof=MFAProof(code="wrong-recovery"),
        )

        assert result.ok is False
