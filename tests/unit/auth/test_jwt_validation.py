"""
Tests for JWT token validation: expired, malformed, and invalid tokens.
"""

from __future__ import annotations

import base64
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from fastapi_users.authentication.strategy.jwt import JWTStrategy

from svc_infra.security.jwt_rotation import RotatingJWTStrategy


class TestExpiredTokens:
    """Test handling of expired JWT tokens."""

    @pytest.fixture
    def secret(self) -> str:
        return "test-secret-key-12345"

    @pytest.fixture
    def token_audience(self) -> list[str]:
        return ["fastapi-users:auth"]

    @pytest.fixture
    def strategy(self, secret: str, token_audience: list[str]) -> RotatingJWTStrategy:
        return RotatingJWTStrategy(
            secret=secret,
            lifetime_seconds=60,
            token_audience=token_audience,
        )

    def _create_expired_token(self, secret: str, audience: list[str]) -> str:
        """Create a token that has already expired."""
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "aud": audience,
            "exp": int((now - timedelta(hours=1)).timestamp()),
            "iat": int((now - timedelta(hours=2)).timestamp()),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    @pytest.mark.asyncio
    async def test_rejects_expired_token(
        self, strategy: RotatingJWTStrategy, secret: str, token_audience: list[str]
    ) -> None:
        """Should reject a token that has expired."""
        expired_token = self._create_expired_token(secret, token_audience)

        with pytest.raises((jwt.ExpiredSignatureError, ValueError)):
            await strategy.read_token(expired_token, audience=token_audience)

    @pytest.mark.asyncio
    async def test_rejects_token_expired_by_seconds(self, secret: str) -> None:
        """Should reject a token that expired just seconds ago."""
        # Create a strategy with very short lifetime
        short_strategy = RotatingJWTStrategy(
            secret=secret,
            lifetime_seconds=1,
            token_audience=["fastapi-users:auth"],
        )

        # Create a minimal user-like object
        user = type("U", (), {"id": "user-1"})()

        # Issue a token
        token = await short_strategy.write_token(user)

        # Wait for expiration
        time.sleep(2)

        # Token should now be rejected
        with pytest.raises((jwt.ExpiredSignatureError, ValueError)):
            await short_strategy.read_token(token, audience=["fastapi-users:auth"])

    @pytest.mark.asyncio
    async def test_accepts_valid_non_expired_token(
        self, strategy: RotatingJWTStrategy, secret: str, token_audience: list[str]
    ) -> None:
        """Should accept a token that has not expired."""
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "aud": token_audience,
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp()),
        }
        valid_token = jwt.encode(payload, secret, algorithm="HS256")

        result = await strategy.read_token(valid_token, audience=token_audience)
        assert result is not None
        assert result["sub"] == "user-123"


class TestMalformedTokens:
    """Test handling of malformed JWT tokens."""

    @pytest.fixture
    def strategy(self) -> RotatingJWTStrategy:
        return RotatingJWTStrategy(
            secret="test-secret",
            lifetime_seconds=3600,
            token_audience=["fastapi-users:auth"],
        )

    @pytest.mark.asyncio
    async def test_rejects_empty_string(self, strategy: RotatingJWTStrategy) -> None:
        """Should reject empty token string."""
        try:
            result = await strategy.read_token("", audience=["fastapi-users:auth"])
            # If no exception, result should be None
            assert result is None
        except ValueError:
            # ValueError is also acceptable
            pass

    @pytest.mark.asyncio
    async def test_rejects_none_token(self, strategy: RotatingJWTStrategy) -> None:
        """Should return None for None token."""
        result = await strategy.read_token(None, audience=["fastapi-users:auth"])
        assert result is None

    @pytest.mark.asyncio
    async def test_rejects_random_string(self, strategy: RotatingJWTStrategy) -> None:
        """Should reject a random non-JWT string."""
        with pytest.raises(ValueError):
            await strategy.read_token("not-a-jwt-token", audience=["fastapi-users:auth"])

    @pytest.mark.asyncio
    async def test_rejects_truncated_token(self, strategy: RotatingJWTStrategy) -> None:
        """Should reject a truncated/incomplete JWT."""
        # JWT has 3 parts separated by dots - provide incomplete
        truncated = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"

        with pytest.raises(ValueError):
            await strategy.read_token(truncated, audience=["fastapi-users:auth"])

    @pytest.mark.asyncio
    async def test_rejects_token_with_invalid_base64(self, strategy: RotatingJWTStrategy) -> None:
        """Should reject a token with invalid base64 encoding."""
        # Malformed base64 in payload
        invalid = "eyJhbGciOiJIUzI1NiJ9.!!!invalid!!!.signature"

        with pytest.raises(ValueError):
            await strategy.read_token(invalid, audience=["fastapi-users:auth"])

    @pytest.mark.asyncio
    async def test_rejects_token_missing_claims(self, strategy: RotatingJWTStrategy) -> None:
        """Should handle token missing required claims."""
        # Create token without standard claims
        payload: dict[str, Any] = {"custom": "data"}
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        # Should fail validation due to missing audience
        with pytest.raises(ValueError):
            await strategy.read_token(token, audience=["fastapi-users:auth"])


class TestInvalidSignatures:
    """Test handling of tokens with invalid signatures."""

    @pytest.fixture
    def valid_secret(self) -> str:
        return "correct-secret"

    @pytest.fixture
    def invalid_secret(self) -> str:
        return "wrong-secret"

    @pytest.fixture
    def strategy(self, valid_secret: str) -> RotatingJWTStrategy:
        return RotatingJWTStrategy(
            secret=valid_secret,
            lifetime_seconds=3600,
            token_audience=["fastapi-users:auth"],
        )

    @pytest.mark.asyncio
    async def test_rejects_token_signed_with_wrong_secret(
        self, strategy: RotatingJWTStrategy, invalid_secret: str
    ) -> None:
        """Should reject a token signed with a different secret."""
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "aud": ["fastapi-users:auth"],
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        wrong_token = jwt.encode(payload, invalid_secret, algorithm="HS256")

        with pytest.raises(ValueError):
            await strategy.read_token(wrong_token, audience=["fastapi-users:auth"])

    @pytest.mark.asyncio
    async def test_rejects_tampered_payload(
        self, strategy: RotatingJWTStrategy, valid_secret: str
    ) -> None:
        """Should reject a token with modified payload (invalid signature)."""
        # Create a valid token
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "aud": ["fastapi-users:auth"],
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        valid_token = jwt.encode(payload, valid_secret, algorithm="HS256")

        # Tamper with the payload (change user ID)
        parts = valid_token.split(".")
        import base64

        # Modify the payload part - decode, change, re-encode
        tampered_payload = base64.urlsafe_b64encode(
            b'{"sub":"hacker-999","aud":["fastapi-users:auth"],"exp":9999999999}'
        ).rstrip(b"=")
        tampered_token = f"{parts[0]}.{tampered_payload.decode()}.{parts[2]}"

        with pytest.raises(ValueError):
            await strategy.read_token(tampered_token, audience=["fastapi-users:auth"])

    @pytest.mark.asyncio
    async def test_rejects_alg_none_attack(self, strategy: RotatingJWTStrategy) -> None:
        """Should reject a token using 'none' algorithm (security attack)."""
        # Craft a token claiming to use 'none' algorithm
        header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=")
        payload = base64.urlsafe_b64encode(
            b'{"sub":"attacker","aud":["fastapi-users:auth"],"exp":9999999999}'
        ).rstrip(b"=")
        malicious_token = f"{header.decode()}.{payload.decode()}."

        with pytest.raises((ValueError, jwt.InvalidAlgorithmError)):
            await strategy.read_token(malicious_token, audience=["fastapi-users:auth"])


class TestAudienceValidation:
    """Test JWT audience claim validation."""

    @pytest.fixture
    def strategy(self) -> RotatingJWTStrategy:
        return RotatingJWTStrategy(
            secret="test-secret",
            lifetime_seconds=3600,
            token_audience=["app:auth"],
        )

    @pytest.mark.asyncio
    async def test_rejects_wrong_audience(self, strategy: RotatingJWTStrategy) -> None:
        """Should reject a token with wrong audience."""
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "aud": ["wrong:audience"],
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        with pytest.raises(ValueError):
            await strategy.read_token(token, audience=["app:auth"])

    @pytest.mark.asyncio
    async def test_rejects_missing_audience(self, strategy: RotatingJWTStrategy) -> None:
        """Should reject a token without audience claim."""
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        with pytest.raises(ValueError):
            await strategy.read_token(token, audience=["app:auth"])

    @pytest.mark.asyncio
    async def test_accepts_matching_audience(self, strategy: RotatingJWTStrategy) -> None:
        """Should accept a token with matching audience."""
        now = datetime.now(UTC)
        payload = {
            "sub": "user-123",
            "aud": ["app:auth"],
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        result = await strategy.read_token(token, audience=["app:auth"])
        assert result is not None
        assert result["sub"] == "user-123"


class TestRotatingSecretValidation:
    """Test validation with rotating secrets."""

    @pytest.mark.asyncio
    async def test_accepts_token_from_old_secret(self) -> None:
        """Should accept a token signed with an old (rotated) secret."""
        old_secret = "old-secret"
        new_secret = "new-secret"

        # Issue with old secret
        old_strategy = JWTStrategy(
            secret=old_secret,
            lifetime_seconds=3600,
            token_audience=["fastapi-users:auth"],
        )
        user = type("U", (), {"id": "user-1"})()
        token = await old_strategy.write_token(user)

        # Verify with rotating strategy
        rotating = RotatingJWTStrategy(
            secret=new_secret,
            lifetime_seconds=3600,
            old_secrets=[old_secret],
            token_audience=["fastapi-users:auth"],
        )

        result = await rotating.read_token(token, audience=["fastapi-users:auth"])
        assert result is not None

    @pytest.mark.asyncio
    async def test_rejects_token_from_unknown_old_secret(self) -> None:
        """Should reject a token signed with an unknown secret."""
        unknown_secret = "unknown-secret"
        new_secret = "new-secret"
        old_secret = "old-secret"

        # Issue with unknown secret
        unknown_strategy = JWTStrategy(
            secret=unknown_secret,
            lifetime_seconds=3600,
            token_audience=["fastapi-users:auth"],
        )
        user = type("U", (), {"id": "user-1"})()
        token = await unknown_strategy.write_token(user)

        # Verify with rotating strategy (doesn't know unknown_secret)
        rotating = RotatingJWTStrategy(
            secret=new_secret,
            lifetime_seconds=3600,
            old_secrets=[old_secret],
            token_audience=["fastapi-users:auth"],
        )

        with pytest.raises(ValueError):
            await rotating.read_token(token, audience=["fastapi-users:auth"])

    @pytest.mark.asyncio
    async def test_new_tokens_signed_with_current_secret(self) -> None:
        """Should sign new tokens with the current (not old) secret."""
        new_secret = "new-secret"
        old_secret = "old-secret"

        rotating = RotatingJWTStrategy(
            secret=new_secret,
            lifetime_seconds=3600,
            old_secrets=[old_secret],
            token_audience=["fastapi-users:auth"],
        )

        user = type("U", (), {"id": "user-1"})()
        token = await rotating.write_token(user)

        # Should be verifiable with new secret only
        JWTStrategy(
            secret=new_secret,
            lifetime_seconds=3600,
            token_audience=["fastapi-users:auth"],
        )
        # This should not raise
        claims = jwt.decode(
            token, new_secret, algorithms=["HS256"], audience=["fastapi-users:auth"]
        )
        assert claims is not None
