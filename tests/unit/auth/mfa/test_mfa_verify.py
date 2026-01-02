"""Tests for svc_infra.api.fastapi.auth.mfa.verify module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pyotp
import pytest

from svc_infra.api.fastapi.auth.mfa.models import EMAIL_OTP_STORE
from svc_infra.api.fastapi.auth.mfa.utils import _hash, _now_utc_ts
from svc_infra.api.fastapi.auth.mfa.verify import MFAProof, MFAResult, verify_mfa_for_user


class FakeUser:
    """Fake user object for testing."""

    def __init__(
        self,
        user_id: str = "user-123",
        mfa_enabled: bool = False,
        mfa_secret: str | None = None,
        mfa_recovery: list[str] | None = None,
    ):
        self.id = user_id
        self.mfa_enabled = mfa_enabled
        self.mfa_secret = mfa_secret
        self.mfa_recovery = mfa_recovery if mfa_recovery is not None else []


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mock session."""
    session = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def clear_email_store() -> None:
    """Clear email OTP store before each test."""
    EMAIL_OTP_STORE.clear()


class TestMFAProof:
    """Tests for MFAProof model."""

    def test_create_with_code(self) -> None:
        """Should create with code."""
        proof = MFAProof(code="123456")
        assert proof.code == "123456"
        assert proof.pre_token is None

    def test_create_empty(self) -> None:
        """Should allow empty."""
        proof = MFAProof()
        assert proof.code is None
        assert proof.pre_token is None


class TestMFAResult:
    """Tests for MFAResult model."""

    def test_default_result(self) -> None:
        """Should have sensible defaults."""
        result = MFAResult(ok=True)
        assert result.ok is True
        assert result.method == "none"
        assert result.attempts_left is None

    def test_totp_result(self) -> None:
        """Should represent TOTP success."""
        result = MFAResult(ok=True, method="totp")
        assert result.method == "totp"

    def test_recovery_result(self) -> None:
        """Should represent recovery code success."""
        result = MFAResult(ok=True, method="recovery")
        assert result.method == "recovery"


class TestVerifyMfaNoMFA:
    """Tests for verify_mfa_for_user when MFA is not enabled."""

    @pytest.mark.asyncio
    async def test_user_without_mfa_require_enabled_true(self, mock_session: AsyncMock) -> None:
        """Should return ok=False when require_enabled=True and no MFA."""
        user = FakeUser(mfa_enabled=False)
        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=None,
            require_enabled=True,
        )
        assert result.ok is False
        assert result.method == "none"

    @pytest.mark.asyncio
    async def test_user_without_mfa_require_enabled_false(self, mock_session: AsyncMock) -> None:
        """Should return ok=True when require_enabled=False and no MFA."""
        user = FakeUser(mfa_enabled=False)
        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=None,
            require_enabled=False,
        )
        assert result.ok is True
        assert result.method == "none"


class TestVerifyMfaWithTotp:
    """Tests for TOTP verification."""

    @pytest.mark.asyncio
    async def test_valid_totp_code(self, mock_session: AsyncMock) -> None:
        """Should verify valid TOTP code."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        user = FakeUser(mfa_enabled=True, mfa_secret=secret)
        proof = MFAProof(code=valid_code)

        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=proof,
            require_enabled=True,
        )
        assert result.ok is True
        assert result.method == "totp"

    @pytest.mark.asyncio
    async def test_invalid_totp_code(self, mock_session: AsyncMock) -> None:
        """Should reject invalid TOTP code."""
        secret = pyotp.random_base32()
        user = FakeUser(mfa_enabled=True, mfa_secret=secret)
        proof = MFAProof(code="000000")  # Invalid code

        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=proof,
            require_enabled=True,
        )
        assert result.ok is False

    @pytest.mark.asyncio
    async def test_no_code_provided(self, mock_session: AsyncMock) -> None:
        """Should fail when no code provided but MFA enabled."""
        secret = pyotp.random_base32()
        user = FakeUser(mfa_enabled=True, mfa_secret=secret)

        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=None,
            require_enabled=True,
        )
        assert result.ok is False
        assert result.method == "none"

    @pytest.mark.asyncio
    async def test_empty_proof(self, mock_session: AsyncMock) -> None:
        """Should fail with empty proof."""
        secret = pyotp.random_base32()
        user = FakeUser(mfa_enabled=True, mfa_secret=secret)
        proof = MFAProof()  # Empty proof

        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=proof,
            require_enabled=True,
        )
        assert result.ok is False


class TestVerifyMfaWithRecovery:
    """Tests for recovery code verification."""

    @pytest.mark.asyncio
    async def test_valid_recovery_code(self, mock_session: AsyncMock) -> None:
        """Should verify valid recovery code and burn it."""
        recovery_code = "ABCD-EFGH-1234-5678"
        code_hash = _hash(recovery_code)

        user = FakeUser(
            mfa_enabled=True,
            mfa_secret=pyotp.random_base32(),
            mfa_recovery=[code_hash],
        )
        proof = MFAProof(code=recovery_code)

        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=proof,
            require_enabled=True,
        )
        assert result.ok is True
        assert result.method == "recovery"
        # Recovery code should be burned (removed from list)
        assert code_hash not in user.mfa_recovery

    @pytest.mark.asyncio
    async def test_invalid_recovery_code(self, mock_session: AsyncMock) -> None:
        """Should reject invalid recovery code."""
        recovery_code = "ABCD-EFGH-1234-5678"
        code_hash = _hash(recovery_code)

        user = FakeUser(
            mfa_enabled=True,
            mfa_secret=pyotp.random_base32(),
            mfa_recovery=[code_hash],
        )
        proof = MFAProof(code="WRONG-CODE")  # Invalid

        result = await verify_mfa_for_user(
            user=user,
            session=mock_session,
            proof=proof,
            require_enabled=True,
        )
        assert result.ok is False
        # Recovery code should NOT be burned
        assert code_hash in user.mfa_recovery


class TestVerifyMfaWithEmail:
    """Tests for email OTP verification."""

    @pytest.mark.asyncio
    async def test_valid_email_otp(self, mock_session: AsyncMock) -> None:
        """Should verify valid email OTP."""
        user_id = "user-email-test"
        email_code = "123456"
        code_hash = _hash(email_code)
        now = _now_utc_ts()

        # Set up email OTP store
        EMAIL_OTP_STORE[user_id] = {
            "hash": code_hash,
            "exp": now + 300,  # 5 minutes from now
            "attempts_left": 3,
        }

        user = FakeUser(
            user_id=user_id,
            mfa_enabled=True,
            mfa_secret=None,  # No TOTP secret
        )

        # Mock pre_token reading
        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_writer.return_value.read = AsyncMock(return_value={"sub": user_id})
            proof = MFAProof(code=email_code, pre_token="valid-pre-token")

            result = await verify_mfa_for_user(
                user=user,
                session=mock_session,
                proof=proof,
                require_enabled=True,
            )

        assert result.ok is True
        assert result.method == "email"
        # Email OTP should be burned
        assert user_id not in EMAIL_OTP_STORE

    @pytest.mark.asyncio
    async def test_email_otp_wrong_code(self, mock_session: AsyncMock) -> None:
        """Should reject wrong email OTP and decrement attempts."""
        user_id = "user-wrong-code"
        email_code = "123456"
        code_hash = _hash(email_code)
        now = _now_utc_ts()

        EMAIL_OTP_STORE[user_id] = {
            "hash": code_hash,
            "exp": now + 300,
            "attempts_left": 3,
        }

        user = FakeUser(
            user_id=user_id,
            mfa_enabled=True,
            mfa_secret=None,
        )

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_writer.return_value.read = AsyncMock(return_value={"sub": user_id})
            proof = MFAProof(code="999999", pre_token="valid-pre-token")  # Wrong

            result = await verify_mfa_for_user(
                user=user,
                session=mock_session,
                proof=proof,
                require_enabled=True,
            )

        assert result.ok is False
        assert result.method == "email"
        # Attempts should be decremented
        assert EMAIL_OTP_STORE[user_id]["attempts_left"] == 2

    @pytest.mark.asyncio
    async def test_email_otp_expired(self, mock_session: AsyncMock) -> None:
        """Should reject expired email OTP."""
        user_id = "user-expired"
        email_code = "123456"
        code_hash = _hash(email_code)
        now = _now_utc_ts()

        EMAIL_OTP_STORE[user_id] = {
            "hash": code_hash,
            "exp": now - 100,  # Expired
            "attempts_left": 3,
        }

        user = FakeUser(
            user_id=user_id,
            mfa_enabled=True,
            mfa_secret=None,
        )

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_writer.return_value.read = AsyncMock(return_value={"sub": user_id})
            proof = MFAProof(code=email_code, pre_token="valid-pre-token")

            result = await verify_mfa_for_user(
                user=user,
                session=mock_session,
                proof=proof,
                require_enabled=True,
            )

        # Expired OTP should fail
        assert result.ok is False

    @pytest.mark.asyncio
    async def test_email_otp_no_attempts(self, mock_session: AsyncMock) -> None:
        """Should reject when no attempts left."""
        user_id = "user-no-attempts"
        email_code = "123456"
        code_hash = _hash(email_code)
        now = _now_utc_ts()

        EMAIL_OTP_STORE[user_id] = {
            "hash": code_hash,
            "exp": now + 300,
            "attempts_left": 0,  # No attempts left
        }

        user = FakeUser(
            user_id=user_id,
            mfa_enabled=True,
            mfa_secret=None,
        )

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_writer.return_value.read = AsyncMock(return_value={"sub": user_id})
            proof = MFAProof(code=email_code, pre_token="valid-pre-token")

            result = await verify_mfa_for_user(
                user=user,
                session=mock_session,
                proof=proof,
                require_enabled=True,
            )

        assert result.ok is False

    @pytest.mark.asyncio
    async def test_invalid_pre_token(self, mock_session: AsyncMock) -> None:
        """Should handle invalid pre_token gracefully."""
        user = FakeUser(
            user_id="user-invalid-token",
            mfa_enabled=True,
            mfa_secret=None,
        )

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_writer.return_value.read = AsyncMock(side_effect=Exception("Invalid token"))
            proof = MFAProof(code="123456", pre_token="invalid-token")

            result = await verify_mfa_for_user(
                user=user,
                session=mock_session,
                proof=proof,
                require_enabled=True,
            )

        assert result.ok is False
        assert result.method == "none"

    @pytest.mark.asyncio
    async def test_user_id_mismatch(self, mock_session: AsyncMock) -> None:
        """Should reject when user ID doesn't match token."""
        user_id = "user-mismatch"
        other_user_id = "other-user"
        email_code = "123456"
        code_hash = _hash(email_code)
        now = _now_utc_ts()

        EMAIL_OTP_STORE[other_user_id] = {
            "hash": code_hash,
            "exp": now + 300,
            "attempts_left": 3,
        }

        user = FakeUser(
            user_id=user_id,
            mfa_enabled=True,
            mfa_secret=None,
        )

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_writer.return_value.read = AsyncMock(return_value={"sub": other_user_id})
            proof = MFAProof(code=email_code, pre_token="valid-pre-token")

            result = await verify_mfa_for_user(
                user=user,
                session=mock_session,
                proof=proof,
                require_enabled=True,
            )

        assert result.ok is False
