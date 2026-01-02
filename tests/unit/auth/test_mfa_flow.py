"""
Tests for MFA flow: TOTP setup, verification, and recovery.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pyotp
import pytest

from svc_infra.api.fastapi.auth.mfa.models import EMAIL_OTP_STORE
from svc_infra.api.fastapi.auth.mfa.utils import (
    _gen_numeric_code,
    _gen_recovery_codes,
    _hash,
    _now_utc_ts,
    _random_base32,
)
from svc_infra.api.fastapi.auth.mfa.verify import MFAProof, MFAResult, verify_mfa_for_user


class FakeUser:
    """Fake user object for MFA testing."""

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


class FakeSession:
    """Fake database session."""

    async def flush(self) -> None:
        pass


class TestMFASetup:
    """Tests for MFA setup flow."""

    def test_generates_totp_secret(self) -> None:
        """Should generate a valid TOTP secret."""
        secret = _random_base32()

        assert len(secret) == 32
        # Should be valid base32
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
        assert all(c in valid_chars for c in secret)

    def test_secret_works_with_pyotp(self) -> None:
        """Should generate a secret compatible with pyotp."""
        secret = _random_base32()
        totp = pyotp.TOTP(secret)

        # Should generate valid codes
        code = totp.now()
        assert len(code) == 6
        assert code.isdigit()

    def test_generates_recovery_codes(self) -> None:
        """Should generate the requested number of recovery codes."""
        codes = _gen_recovery_codes(n=10, length=16)

        assert len(codes) == 10
        assert all(len(c) == 16 for c in codes)

    def test_recovery_codes_are_unique(self) -> None:
        """Should generate unique recovery codes."""
        codes = _gen_recovery_codes(n=100, length=16)
        assert len(set(codes)) == 100

    def test_recovery_codes_are_url_safe(self) -> None:
        """Should generate URL-safe recovery codes."""
        codes = _gen_recovery_codes(n=10, length=16)

        for code in codes:
            assert all(c.isalnum() or c in "-_" for c in code)

    def test_stores_hashed_recovery_codes(self) -> None:
        """Should store hashed versions of recovery codes."""
        plain_codes = _gen_recovery_codes(n=5, length=16)
        hashed_codes = [_hash(c) for c in plain_codes]

        # Hashes should be different from plain codes
        for plain, hashed in zip(plain_codes, hashed_codes):
            assert plain != hashed
            assert len(hashed) == 64  # SHA-256 hex


class TestTOTPVerification:
    """Tests for TOTP verification flow."""

    @pytest.fixture
    def session(self) -> FakeSession:
        return FakeSession()

    @pytest.fixture
    def totp_secret(self) -> str:
        return _random_base32()

    @pytest.fixture
    def mfa_user(self, totp_secret: str) -> FakeUser:
        return FakeUser(
            mfa_enabled=True,
            mfa_secret=totp_secret,
        )

    @pytest.mark.asyncio
    async def test_accepts_valid_totp_code(
        self, session: FakeSession, totp_secret: str, mfa_user: FakeUser
    ) -> None:
        """Should accept a valid TOTP code."""
        totp = pyotp.TOTP(totp_secret)
        valid_code = totp.now()

        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=valid_code),
        )

        assert result.ok is True
        assert result.method == "totp"

    @pytest.mark.asyncio
    async def test_rejects_invalid_totp_code(
        self, session: FakeSession, mfa_user: FakeUser
    ) -> None:
        """Should reject an invalid TOTP code."""
        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code="000000"),
        )

        assert result.ok is False

    @pytest.mark.asyncio
    async def test_rejects_old_totp_code(
        self, session: FakeSession, totp_secret: str, mfa_user: FakeUser
    ) -> None:
        """Should reject a TOTP code outside the valid window."""
        totp = pyotp.TOTP(totp_secret)
        # Generate code for a time far in the past
        old_code = totp.at(0)  # Code at Unix epoch

        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=old_code),
        )

        assert result.ok is False

    @pytest.mark.asyncio
    async def test_accepts_code_within_window(
        self, session: FakeSession, totp_secret: str, mfa_user: FakeUser
    ) -> None:
        """Should accept a code within the valid window (1 step)."""

        totp = pyotp.TOTP(totp_secret)
        # The verify with valid_window=1 allows current and previous code
        current_code = totp.now()

        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=current_code),
        )

        assert result.ok is True

    @pytest.mark.asyncio
    async def test_rejects_empty_code(self, session: FakeSession, mfa_user: FakeUser) -> None:
        """Should reject empty code."""
        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=""),
        )

        assert result.ok is False

    @pytest.mark.asyncio
    async def test_rejects_none_proof(self, session: FakeSession, mfa_user: FakeUser) -> None:
        """Should reject None proof when MFA is required."""
        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=None,
        )

        assert result.ok is False


class TestRecoveryCodeVerification:
    """Tests for recovery code verification flow."""

    @pytest.fixture
    def session(self) -> FakeSession:
        return FakeSession()

    @pytest.fixture
    def recovery_codes(self) -> list[str]:
        return _gen_recovery_codes(n=10, length=16)

    @pytest.fixture
    def mfa_user(self, recovery_codes: list[str]) -> FakeUser:
        hashed = [_hash(c) for c in recovery_codes]
        return FakeUser(
            mfa_enabled=True,
            mfa_secret=_random_base32(),
            mfa_recovery=hashed,
        )

    @pytest.mark.asyncio
    async def test_accepts_valid_recovery_code(
        self, session: FakeSession, recovery_codes: list[str], mfa_user: FakeUser
    ) -> None:
        """Should accept a valid recovery code."""
        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=recovery_codes[0]),
        )

        assert result.ok is True
        assert result.method == "recovery"

    @pytest.mark.asyncio
    async def test_burns_used_recovery_code(
        self, session: FakeSession, recovery_codes: list[str], mfa_user: FakeUser
    ) -> None:
        """Should remove (burn) a used recovery code."""
        initial_count = len(mfa_user.mfa_recovery)
        used_hash = _hash(recovery_codes[0])

        await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=recovery_codes[0]),
        )

        assert len(mfa_user.mfa_recovery) == initial_count - 1
        assert used_hash not in mfa_user.mfa_recovery

    @pytest.mark.asyncio
    async def test_rejects_reused_recovery_code(
        self, session: FakeSession, recovery_codes: list[str], mfa_user: FakeUser
    ) -> None:
        """Should reject a recovery code that was already used."""
        # Use the code once
        await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=recovery_codes[0]),
        )

        # Try to use it again
        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code=recovery_codes[0]),
        )

        assert result.ok is False

    @pytest.mark.asyncio
    async def test_rejects_invalid_recovery_code(
        self, session: FakeSession, mfa_user: FakeUser
    ) -> None:
        """Should reject an invalid recovery code."""
        result = await verify_mfa_for_user(
            user=mfa_user,
            session=session,
            proof=MFAProof(code="invalid-recovery-code"),
        )

        # Falls through to TOTP check which also fails
        assert result.ok is False

    @pytest.mark.asyncio
    async def test_can_use_all_recovery_codes(
        self, session: FakeSession, recovery_codes: list[str], mfa_user: FakeUser
    ) -> None:
        """Should allow using all recovery codes."""
        for code in recovery_codes:
            # Create fresh user with remaining codes
            result = await verify_mfa_for_user(
                user=mfa_user,
                session=session,
                proof=MFAProof(code=code),
            )
            assert result.ok is True

        # All codes used up
        assert len(mfa_user.mfa_recovery) == 0


class TestMFANotEnabled:
    """Tests for users without MFA enabled."""

    @pytest.fixture
    def session(self) -> FakeSession:
        return FakeSession()

    @pytest.fixture
    def non_mfa_user(self) -> FakeUser:
        return FakeUser(mfa_enabled=False)

    @pytest.mark.asyncio
    async def test_passes_when_not_required(
        self, session: FakeSession, non_mfa_user: FakeUser
    ) -> None:
        """Should pass when MFA is not required and not enabled."""
        result = await verify_mfa_for_user(
            user=non_mfa_user,
            session=session,
            proof=None,
            require_enabled=False,
        )

        assert result.ok is True
        assert result.method == "none"

    @pytest.mark.asyncio
    async def test_fails_when_required(self, session: FakeSession, non_mfa_user: FakeUser) -> None:
        """Should fail when MFA is required but not enabled."""
        result = await verify_mfa_for_user(
            user=non_mfa_user,
            session=session,
            proof=None,
            require_enabled=True,
        )

        assert result.ok is False
        assert result.method == "none"


class TestEmailOTPVerification:
    """Tests for email OTP verification flow."""

    @pytest.fixture
    def session(self) -> FakeSession:
        return FakeSession()

    @pytest.fixture(autouse=True)
    def clear_store(self) -> None:
        EMAIL_OTP_STORE.clear()

    @pytest.fixture
    def mfa_user(self) -> FakeUser:
        return FakeUser(
            user_id="email-mfa-user",
            mfa_enabled=True,
            mfa_secret=_random_base32(),
        )

    def _setup_email_otp(self, user_id: str, code: str, attempts: int = 3) -> None:
        """Set up email OTP in the store."""
        EMAIL_OTP_STORE[user_id] = {
            "hash": _hash(code),
            "exp": _now_utc_ts() + 300,  # 5 minutes
            "attempts_left": attempts,
        }

    @pytest.mark.asyncio
    async def test_accepts_valid_email_otp(self, session: FakeSession, mfa_user: FakeUser) -> None:
        """Should accept a valid email OTP code."""
        code = "123456"
        self._setup_email_otp(mfa_user.id, code)

        # Mock the pre-token reader to return our user
        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_instance = Mock()
            mock_instance.read = AsyncMock(return_value={"sub": mfa_user.id})
            mock_writer.return_value = mock_instance

            result = await verify_mfa_for_user(
                user=mfa_user,
                session=session,
                proof=MFAProof(code=code, pre_token="valid-pre-token"),
            )

        assert result.ok is True
        assert result.method == "email"

    @pytest.mark.asyncio
    async def test_burns_used_email_otp(self, session: FakeSession, mfa_user: FakeUser) -> None:
        """Should remove email OTP after successful use."""
        code = "654321"
        self._setup_email_otp(mfa_user.id, code)

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_instance = Mock()
            mock_instance.read = AsyncMock(return_value={"sub": mfa_user.id})
            mock_writer.return_value = mock_instance

            await verify_mfa_for_user(
                user=mfa_user,
                session=session,
                proof=MFAProof(code=code, pre_token="token"),
            )

        assert mfa_user.id not in EMAIL_OTP_STORE

    @pytest.mark.asyncio
    async def test_decrements_attempts_on_failure(
        self, session: FakeSession, mfa_user: FakeUser
    ) -> None:
        """Should decrement attempts on failed verification."""
        code = "111111"
        self._setup_email_otp(mfa_user.id, code, attempts=3)

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_instance = Mock()
            mock_instance.read = AsyncMock(return_value={"sub": mfa_user.id})
            mock_writer.return_value = mock_instance

            result = await verify_mfa_for_user(
                user=mfa_user,
                session=session,
                proof=MFAProof(code="wrong-code", pre_token="token"),
            )

        assert result.ok is False
        assert result.method == "email"
        assert result.attempts_left == 2

    @pytest.mark.asyncio
    async def test_rejects_expired_email_otp(
        self, session: FakeSession, mfa_user: FakeUser
    ) -> None:
        """Should reject expired email OTP."""
        code = "222222"
        # Set up expired OTP
        EMAIL_OTP_STORE[mfa_user.id] = {
            "hash": _hash(code),
            "exp": _now_utc_ts() - 10,  # expired
            "attempts_left": 3,
        }

        with patch("svc_infra.api.fastapi.auth.mfa.verify.get_mfa_pre_jwt_writer") as mock_writer:
            mock_instance = Mock()
            mock_instance.read = AsyncMock(return_value={"sub": mfa_user.id})
            mock_writer.return_value = mock_instance

            result = await verify_mfa_for_user(
                user=mfa_user,
                session=session,
                proof=MFAProof(code=code, pre_token="token"),
            )

        assert result.ok is False


class TestMFAProofModel:
    """Tests for MFAProof Pydantic model."""

    def test_creates_with_code_only(self) -> None:
        """Should create proof with code only."""
        proof = MFAProof(code="123456")

        assert proof.code == "123456"
        assert proof.pre_token is None

    def test_creates_with_pre_token(self) -> None:
        """Should create proof with pre_token."""
        proof = MFAProof(code="123456", pre_token="pre-jwt-token")

        assert proof.code == "123456"
        assert proof.pre_token == "pre-jwt-token"

    def test_creates_empty(self) -> None:
        """Should allow empty proof."""
        proof = MFAProof()

        assert proof.code is None
        assert proof.pre_token is None


class TestMFAResultModel:
    """Tests for MFAResult Pydantic model."""

    def test_default_method_is_none(self) -> None:
        """Should default method to 'none'."""
        result = MFAResult(ok=True)

        assert result.method == "none"

    def test_totp_result(self) -> None:
        """Should represent TOTP verification."""
        result = MFAResult(ok=True, method="totp")

        assert result.ok is True
        assert result.method == "totp"

    def test_recovery_result(self) -> None:
        """Should represent recovery code verification."""
        result = MFAResult(ok=True, method="recovery")

        assert result.method == "recovery"

    def test_email_result_with_attempts(self) -> None:
        """Should track attempts for email OTP."""
        result = MFAResult(ok=False, method="email", attempts_left=2)

        assert result.ok is False
        assert result.method == "email"
        assert result.attempts_left == 2


class TestNumericCodeGeneration:
    """Tests for numeric OTP code generation."""

    def test_generates_six_digits_by_default(self) -> None:
        """Should generate 6-digit code by default."""
        code = _gen_numeric_code()

        assert len(code) == 6
        assert code.isdigit()

    def test_generates_custom_length(self) -> None:
        """Should generate code of custom length."""
        code = _gen_numeric_code(n=8)

        assert len(code) == 8
        assert code.isdigit()

    def test_generates_random_codes(self) -> None:
        """Should generate random codes."""
        codes = [_gen_numeric_code() for _ in range(100)]

        # Should have variety (not all same)
        assert len(set(codes)) > 50
