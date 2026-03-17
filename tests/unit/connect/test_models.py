from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from svc_infra.connect.models import ConnectionToken, OAuthState


class TestConnectionTokenModel:
    def test_table_name(self):
        assert ConnectionToken.__tablename__ == "connection_tokens"

    def test_unique_constraint_name(self):
        constraints = {c.name for c in ConnectionToken.__table_args__ if hasattr(c, "name")}
        assert "uq_connection_token" in constraints

    def test_composite_index_exists(self):
        indexes = {i.name for i in ConnectionToken.__table_args__ if hasattr(i, "name")}
        assert "ix_connection_tokens_user_provider" in indexes

    def test_instantiation_with_required_fields(self):
        user_id = uuid.uuid4()
        connection_id = uuid.uuid4()
        token = ConnectionToken(
            user_id=user_id,
            connection_id=connection_id,
            provider="github",
            access_token="encrypted_token",
            token_type="Bearer",
        )
        assert token.provider == "github"
        assert token.token_type == "Bearer"
        assert token.refresh_token is None
        assert token.expires_at is None
        assert token.scopes is None
        assert token.raw_token is None

    def test_explicit_id_is_stored(self):
        custom_id = uuid.uuid4()
        token = ConnectionToken(
            id=custom_id,
            user_id=uuid.uuid4(),
            connection_id=uuid.uuid4(),
            provider="github",
            access_token="x",
        )
        assert token.id == custom_id
        assert isinstance(token.id, uuid.UUID)


class TestOAuthStateModel:
    def test_table_name(self):
        assert OAuthState.__tablename__ == "oauth_states"

    def test_instantiation_with_required_fields(self):
        user_id = uuid.uuid4()
        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        state = OAuthState(
            state="random_state_value",
            pkce_verifier="verifier",
            provider="github",
            user_id=user_id,
            redirect_uri="https://example.com/callback",
            expires_at=expires_at,
        )
        assert state.state == "random_state_value"
        assert state.connection_id is None

    def test_explicit_id_is_stored(self):
        custom_id = uuid.uuid4()
        state = OAuthState(
            id=custom_id,
            state="s",
            pkce_verifier="v",
            provider="github",
            user_id=uuid.uuid4(),
            redirect_uri="https://example.com/callback",
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        assert state.id == custom_id
        assert isinstance(state.id, uuid.UUID)
