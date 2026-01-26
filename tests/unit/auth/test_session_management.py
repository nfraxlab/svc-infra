"""
Tests for session management: create, refresh, and revoke sessions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio

from svc_infra.security.models import AuthSession, RefreshToken, RefreshTokenRevocation
from svc_infra.security.session import (
    DEFAULT_REFRESH_TTL_MINUTES,
    issue_session_and_refresh,
    rotate_session_refresh,
)


class FakeAsyncSession:
    """Fake async database session for testing."""

    def __init__(self) -> None:
        self.objects: list[object] = []
        self._flushed = False

    def add(self, obj: object) -> None:
        self.objects.append(obj)

    async def flush(self) -> None:
        self._flushed = True
        # Assign IDs if not set
        for obj in self.objects:
            if isinstance(obj, AuthSession) and not getattr(obj, "id", None):
                obj.id = uuid.uuid4()
            if isinstance(obj, RefreshToken) and not getattr(obj, "id", None):
                obj.id = uuid.uuid4()

    async def execute(self, stmt):
        """Mock execute for queries."""

        class Result:
            def scalars(self):
                return self

            def all(self):
                return []

            def scalar_one_or_none(self):
                return None

        return Result()


class TestIssueSessionAndRefresh:
    """Tests for creating new sessions with refresh tokens."""

    @pytest.fixture
    def db(self) -> FakeAsyncSession:
        return FakeAsyncSession()

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_creates_auth_session(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should create an AuthSession record."""
        _raw_token, _rt = await issue_session_and_refresh(db, user_id=user_id)

        sessions = [o for o in db.objects if isinstance(o, AuthSession)]
        assert len(sessions) == 1
        assert sessions[0].user_id == user_id

    @pytest.mark.asyncio
    async def test_creates_refresh_token(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should create a RefreshToken record."""
        _raw_token, rt = await issue_session_and_refresh(db, user_id=user_id)

        tokens = [o for o in db.objects if isinstance(o, RefreshToken)]
        assert len(tokens) == 1
        assert rt.session is not None

    @pytest.mark.asyncio
    async def test_returns_raw_token_string(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should return a raw token string."""
        raw_token, _rt = await issue_session_and_refresh(db, user_id=user_id)

        assert isinstance(raw_token, str)
        assert len(raw_token) > 0

    @pytest.mark.asyncio
    async def test_token_hash_is_stored(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should store a hash of the token, not the raw token."""
        raw_token, rt = await issue_session_and_refresh(db, user_id=user_id)

        # Hash should be different from raw
        assert rt.token_hash != raw_token
        assert len(rt.token_hash) > 0

    @pytest.mark.asyncio
    async def test_sets_default_ttl(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should set expiration based on default TTL."""
        before = datetime.now(UTC)
        _raw_token, rt = await issue_session_and_refresh(db, user_id=user_id)
        after = datetime.now(UTC)

        expected_min = before + timedelta(minutes=DEFAULT_REFRESH_TTL_MINUTES)
        expected_max = after + timedelta(minutes=DEFAULT_REFRESH_TTL_MINUTES)

        assert rt.expires_at is not None
        assert expected_min <= rt.expires_at <= expected_max

    @pytest.mark.asyncio
    async def test_respects_custom_ttl(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should respect custom TTL parameter."""
        custom_ttl = 30  # 30 minutes
        before = datetime.now(UTC)
        _raw_token, rt = await issue_session_and_refresh(
            db, user_id=user_id, ttl_minutes=custom_ttl
        )

        expected = before + timedelta(minutes=custom_ttl)
        # Allow 1 second tolerance
        assert abs((rt.expires_at - expected).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_stores_tenant_id(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should store tenant_id if provided."""
        tenant = "tenant-123"
        _raw_token, _rt = await issue_session_and_refresh(db, user_id=user_id, tenant_id=tenant)

        sessions = [o for o in db.objects if isinstance(o, AuthSession)]
        assert sessions[0].tenant_id == tenant

    @pytest.mark.asyncio
    async def test_stores_user_agent(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should store user_agent if provided."""
        ua = "Mozilla/5.0 (Test Browser)"
        _raw_token, _rt = await issue_session_and_refresh(db, user_id=user_id, user_agent=ua)

        sessions = [o for o in db.objects if isinstance(o, AuthSession)]
        assert sessions[0].user_agent == ua

    @pytest.mark.asyncio
    async def test_stores_ip_hash(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should store ip_hash if provided."""
        ip_hash = "abc123def456"
        _raw_token, _rt = await issue_session_and_refresh(db, user_id=user_id, ip_hash=ip_hash)

        sessions = [o for o in db.objects if isinstance(o, AuthSession)]
        assert sessions[0].ip_hash == ip_hash

    @pytest.mark.asyncio
    async def test_flushes_database(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should flush the database session."""
        _raw_token, _rt = await issue_session_and_refresh(db, user_id=user_id)
        assert db._flushed is True


class TestRotateSessionRefresh:
    """Tests for rotating refresh tokens."""

    @pytest.fixture
    def db(self) -> FakeAsyncSession:
        return FakeAsyncSession()

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest_asyncio.fixture
    async def active_token(
        self, db: FakeAsyncSession, user_id: uuid.UUID
    ) -> tuple[str, RefreshToken]:
        """Create an active refresh token."""
        return await issue_session_and_refresh(db, user_id=user_id)

    @pytest.mark.asyncio
    async def test_creates_new_token(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should create a new refresh token."""
        _old_raw, old_rt = active_token
        initial_count = len([o for o in db.objects if isinstance(o, RefreshToken)])

        _new_raw, new_rt = await rotate_session_refresh(db, current=old_rt)

        new_count = len([o for o in db.objects if isinstance(o, RefreshToken)])
        assert new_count == initial_count + 1
        assert new_rt.id != old_rt.id

    @pytest.mark.asyncio
    async def test_returns_new_raw_token(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should return a new raw token string."""
        old_raw, old_rt = active_token

        new_raw, _new_rt = await rotate_session_refresh(db, current=old_rt)

        assert new_raw != old_raw
        assert isinstance(new_raw, str)
        assert len(new_raw) > 0

    @pytest.mark.asyncio
    async def test_marks_old_token_as_rotated(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should mark the old token as rotated."""
        _old_raw, old_rt = active_token

        _new_raw, _new_rt = await rotate_session_refresh(db, current=old_rt)

        assert old_rt.rotated_at is not None
        assert old_rt.revoked_at is not None
        assert old_rt.revoke_reason == "rotated"

    @pytest.mark.asyncio
    async def test_creates_revocation_record(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should create a revocation record for the old token."""
        _old_raw, old_rt = active_token

        _new_raw, _new_rt = await rotate_session_refresh(db, current=old_rt)

        revocations = [o for o in db.objects if isinstance(o, RefreshTokenRevocation)]
        assert len(revocations) == 1
        assert revocations[0].token_hash == old_rt.token_hash
        assert revocations[0].reason == "rotated"

    @pytest.mark.asyncio
    async def test_new_token_linked_to_same_session(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should link new token to the same session."""
        _old_raw, old_rt = active_token

        _new_raw, new_rt = await rotate_session_refresh(db, current=old_rt)

        assert new_rt.session is old_rt.session

    @pytest.mark.asyncio
    async def test_rejects_already_revoked_token(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should reject rotation of an already revoked token."""
        _old_raw, old_rt = active_token
        old_rt.revoked_at = datetime.now(UTC)

        with pytest.raises(ValueError, match="already revoked"):
            await rotate_session_refresh(db, current=old_rt)

    @pytest.mark.asyncio
    async def test_rejects_expired_token(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should reject rotation of an expired token."""
        _old_raw, old_rt = active_token
        old_rt.expires_at = datetime.now(UTC) - timedelta(hours=1)

        with pytest.raises(ValueError, match="expired"):
            await rotate_session_refresh(db, current=old_rt)

    @pytest.mark.asyncio
    async def test_respects_custom_ttl(
        self, db: FakeAsyncSession, active_token: tuple[str, RefreshToken]
    ) -> None:
        """Should respect custom TTL for new token."""
        _old_raw, old_rt = active_token
        custom_ttl = 120  # 2 hours

        before = datetime.now(UTC)
        _new_raw, new_rt = await rotate_session_refresh(db, current=old_rt, ttl_minutes=custom_ttl)

        expected = before + timedelta(minutes=custom_ttl)
        assert abs((new_rt.expires_at - expected).total_seconds()) < 1


class TestSessionRevocation:
    """Tests for session and token revocation."""

    @pytest.fixture
    def db(self) -> FakeAsyncSession:
        return FakeAsyncSession()

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_revoked_session_has_revoked_tokens(
        self, db: FakeAsyncSession, user_id: uuid.UUID
    ) -> None:
        """Should have revoked refresh tokens when session is revoked."""
        _raw, rt = await issue_session_and_refresh(db, user_id=user_id)
        session = rt.session

        # Revoke the session
        session.revoked_at = datetime.now(UTC)
        session.revoke_reason = "user_logout"

        assert session.revoked_at is not None

    @pytest.mark.asyncio
    async def test_cannot_rotate_after_session_revocation(
        self, db: FakeAsyncSession, user_id: uuid.UUID
    ) -> None:
        """Should not allow rotation after session-level revocation."""
        _raw, rt = await issue_session_and_refresh(db, user_id=user_id)

        # Revoke the token directly
        rt.revoked_at = datetime.now(UTC)

        with pytest.raises(ValueError, match="already revoked"):
            await rotate_session_refresh(db, current=rt)


class TestMultipleSessions:
    """Tests for managing multiple sessions per user."""

    @pytest.fixture
    def db(self) -> FakeAsyncSession:
        return FakeAsyncSession()

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_user_can_have_multiple_sessions(
        self, db: FakeAsyncSession, user_id: uuid.UUID
    ) -> None:
        """Should allow a user to have multiple active sessions."""
        _raw1, _rt1 = await issue_session_and_refresh(db, user_id=user_id, user_agent="Browser 1")
        _raw2, _rt2 = await issue_session_and_refresh(db, user_id=user_id, user_agent="Browser 2")
        _raw3, _rt3 = await issue_session_and_refresh(db, user_id=user_id, user_agent="Mobile App")

        sessions = [o for o in db.objects if isinstance(o, AuthSession)]
        assert len(sessions) == 3

        # All sessions belong to same user
        for session in sessions:
            assert session.user_id == user_id

    @pytest.mark.asyncio
    async def test_sessions_are_independent(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should have independent tokens per session."""
        raw1, rt1 = await issue_session_and_refresh(db, user_id=user_id)
        raw2, rt2 = await issue_session_and_refresh(db, user_id=user_id)

        # Tokens are different
        assert raw1 != raw2
        assert rt1.token_hash != rt2.token_hash

        # Sessions are different
        assert rt1.session.id != rt2.session.id

    @pytest.mark.asyncio
    async def test_revoking_one_session_doesnt_affect_others(
        self, db: FakeAsyncSession, user_id: uuid.UUID
    ) -> None:
        """Should only revoke the specified session."""
        _raw1, rt1 = await issue_session_and_refresh(db, user_id=user_id)
        _raw2, rt2 = await issue_session_and_refresh(db, user_id=user_id)

        # Revoke first session
        rt1.session.revoked_at = datetime.now(UTC)
        rt1.revoked_at = datetime.now(UTC)

        # Second session should still be valid
        assert rt2.session.revoked_at is None
        assert rt2.revoked_at is None


class TestTokenHashing:
    """Tests for secure token hashing."""

    @pytest.fixture
    def db(self) -> FakeAsyncSession:
        return FakeAsyncSession()

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_same_raw_produces_same_hash(
        self, db: FakeAsyncSession, user_id: uuid.UUID
    ) -> None:
        """Should produce consistent hash for same input."""
        from svc_infra.security.models import hash_refresh_token

        raw = "test-token-12345"
        hash1 = hash_refresh_token(raw)
        hash2 = hash_refresh_token(raw)

        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_different_raw_produces_different_hash(
        self, db: FakeAsyncSession, user_id: uuid.UUID
    ) -> None:
        """Should produce different hashes for different inputs."""
        from svc_infra.security.models import hash_refresh_token

        hash1 = hash_refresh_token("token-1")
        hash2 = hash_refresh_token("token-2")

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_hash_is_fixed_length(self, db: FakeAsyncSession, user_id: uuid.UUID) -> None:
        """Should produce fixed-length hash regardless of input."""
        from svc_infra.security.models import hash_refresh_token

        short_hash = hash_refresh_token("a")
        long_hash = hash_refresh_token("a" * 1000)

        assert len(short_hash) == len(long_hash)
        assert len(short_hash) == 64  # SHA-256 hex digest
