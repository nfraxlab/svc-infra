from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from svc_infra.connect.models import ConnectionToken
from svc_infra.connect.pkce import OAuthRefreshError
from svc_infra.connect.registry import ConnectRegistry, OAuthProvider
from svc_infra.connect.token_manager import ConnectionTokenManager

_KEY = Fernet.generate_key().decode()

_USER_ID = uuid4()
_CONN_ID = uuid4()
_PROVIDER = "github"


def _make_registry() -> ConnectRegistry:
    reg = ConnectRegistry()
    reg.register(
        OAuthProvider(
            name=_PROVIDER,
            client_id="cid",
            client_secret="csecret",
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            revoke_url="https://github.com/login/oauth/revoke",
            default_scopes=["repo"],
        )
    )
    return reg


def _make_manager(registry: ConnectRegistry | None = None) -> ConnectionTokenManager:
    return ConnectionTokenManager(_KEY, registry=registry)


def _make_token_row(
    manager: ConnectionTokenManager,
    *,
    access_token: str = "access",
    refresh_token: str | None = "refresh",
    expires_at: datetime | None = None,
) -> ConnectionToken:
    row = MagicMock(spec=ConnectionToken)
    row.id = uuid4()
    row.user_id = _USER_ID
    row.connection_id = _CONN_ID
    row.provider = _PROVIDER
    row.access_token = manager._encrypt(access_token)
    row.refresh_token = manager._encrypt(refresh_token) if refresh_token else None
    row.token_type = "Bearer"
    row.scopes = ["repo"]
    row.expires_at = expires_at
    row.raw_token = manager._encrypt_json({"access_token": access_token})
    return row


def _make_db(*execute_returns) -> MagicMock:
    """Return a mock db session whose sequential execute() calls yield the given scalars."""
    idx = [0]
    values = list(execute_returns)

    async def _execute(_stmt):
        result = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.first = MagicMock(
            return_value=values[idx[0]] if idx[0] < len(values) else None
        )
        scalars_mock.all = MagicMock(return_value=[values[idx[0]]] if idx[0] < len(values) else [])
        result.scalars = MagicMock(return_value=scalars_mock)
        idx[0] += 1
        return result

    db = MagicMock()
    db.execute = _execute
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    return db


class TestEncryptionRoundtrip:
    def test_encrypt_decrypt_string(self):
        manager = _make_manager()
        plaintext = "my-access-token"
        encrypted = manager._encrypt(plaintext)
        assert encrypted != plaintext
        assert manager._decrypt(encrypted) == plaintext

    def test_encrypt_decrypt_json(self):
        manager = _make_manager()
        data = {"access_token": "tok", "scopes": ["read", "write"]}
        encrypted = manager._encrypt_json(data)
        assert isinstance(encrypted, str)
        assert manager._decrypt_json(encrypted) == data


@pytest.mark.asyncio
class TestStore:
    async def test_creates_new_row_when_none_exists(self, mocker):
        manager = _make_manager()
        db = _make_db(None)  # get() returns None → create path

        fake_row = _make_token_row(manager)
        mock_create = mocker.patch.object(
            manager._repo, "create", new_callable=AsyncMock, return_value=fake_row
        )

        result = await manager.store(
            db,
            user_id=_USER_ID,
            connection_id=_CONN_ID,
            provider=_PROVIDER,
            token_response={"access_token": "access", "token_type": "Bearer"},
        )

        mock_create.assert_awaited_once()
        assert result is fake_row

    async def test_updates_existing_row(self, mocker):
        manager = _make_manager()
        existing_row = _make_token_row(manager)
        db = _make_db(existing_row)

        mock_update = mocker.patch.object(
            manager._repo, "update", new_callable=AsyncMock, return_value=existing_row
        )

        await manager.store(
            db,
            user_id=_USER_ID,
            connection_id=_CONN_ID,
            provider=_PROVIDER,
            token_response={"access_token": "new_access", "token_type": "Bearer"},
        )

        mock_update.assert_awaited_once()

    async def test_stores_encrypted_access_token(self, mocker):
        manager = _make_manager()
        db = _make_db(None)

        captured: dict = {}

        async def capture_create(_db, data: dict):
            captured.update(data)
            return _make_token_row(manager, access_token="plain_access")

        mocker.patch.object(manager._repo, "create", side_effect=capture_create)

        await manager.store(
            db,
            user_id=_USER_ID,
            connection_id=_CONN_ID,
            provider=_PROVIDER,
            token_response={"access_token": "plain_access", "token_type": "Bearer"},
        )

        # The stored access_token must be encrypted (not plaintext)
        stored_enc = captured["access_token"]
        assert stored_enc != "plain_access"
        assert manager._decrypt(stored_enc) == "plain_access"


@pytest.mark.asyncio
class TestGetValidToken:
    async def test_returns_valid_token(self, mocker):
        manager = _make_manager()
        row = _make_token_row(
            manager, access_token="my_token", expires_at=datetime.now(UTC) + timedelta(hours=1)
        )
        db = _make_db(row)

        token = await manager.get_valid_token(
            db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER
        )
        assert token == "my_token"

    async def test_returns_none_when_no_row(self):
        manager = _make_manager()
        db = _make_db(None)

        token = await manager.get_valid_token(
            db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER
        )
        assert token is None

    async def test_triggers_refresh_near_expiry(self, mocker):
        manager = _make_manager(registry=_make_registry())
        near_expiry = datetime.now(UTC) + timedelta(minutes=2)
        row = _make_token_row(
            manager, access_token="old", refresh_token="rt", expires_at=near_expiry
        )
        refreshed_row = _make_token_row(manager, access_token="new_tok")

        db = _make_db(row)

        mock_refresh = mocker.patch.object(
            manager, "_refresh_token", new_callable=AsyncMock, return_value=refreshed_row
        )

        token = await manager.get_valid_token(
            db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER
        )

        mock_refresh.assert_awaited_once_with(db, row)
        assert token == "new_tok"

    async def test_returns_none_when_refresh_fails(self, mocker):
        manager = _make_manager(registry=_make_registry())
        near_expiry = datetime.now(UTC) + timedelta(minutes=2)
        row = _make_token_row(
            manager, access_token="old", refresh_token="rt", expires_at=near_expiry
        )
        db = _make_db(row)

        mocker.patch.object(manager, "_refresh_token", new_callable=AsyncMock, return_value=None)

        token = await manager.get_valid_token(
            db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER
        )
        assert token is None

    async def test_does_not_raise_on_exception(self):
        """get_valid_token must never raise; return None instead."""
        manager = _make_manager()
        db = MagicMock()
        db.execute = AsyncMock(side_effect=RuntimeError("db error"))

        token = await manager.get_valid_token(
            db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER
        )
        assert token is None


@pytest.mark.asyncio
class TestRevoke:
    async def test_deletes_row(self, mocker):
        manager = _make_manager()
        row = _make_token_row(manager)
        db = _make_db(row)

        mock_delete = mocker.patch.object(manager._repo, "delete", new_callable=AsyncMock)

        await manager.revoke(db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER)

        mock_delete.assert_awaited_once_with(db, row.id)

    async def test_calls_revoke_url_when_configured(self, mocker):
        manager = _make_manager(registry=_make_registry())
        row = _make_token_row(manager)
        db = _make_db(row)

        mocker.patch.object(manager._repo, "delete", new_callable=AsyncMock)
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))

        with patch("svc_infra.connect.token_manager.httpx.AsyncClient", return_value=mock_client):
            await manager.revoke(db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER)

        mock_client.post.assert_awaited_once()

    async def test_no_op_when_no_row(self, mocker):
        manager = _make_manager()
        db = _make_db(None)

        mock_delete = mocker.patch.object(manager._repo, "delete", new_callable=AsyncMock)
        await manager.revoke(db, connection_id=_CONN_ID, user_id=_USER_ID, provider=_PROVIDER)

        mock_delete.assert_not_awaited()


@pytest.mark.asyncio
class TestDeleteAllForConnection:
    async def test_executes_bulk_delete(self):
        manager = _make_manager()
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock())
        db.flush = AsyncMock()

        await manager.delete_all_for_connection(db, _CONN_ID)

        db.execute.assert_awaited_once()
        db.flush.assert_awaited_once()


@pytest.mark.asyncio
class TestRefreshExpiringTokens:
    async def test_returns_count_of_refreshed_tokens(self, mocker):
        manager = _make_manager(registry=_make_registry())
        row1 = _make_token_row(manager)
        row2 = _make_token_row(manager)
        db = MagicMock()

        async def _execute(_stmt):
            result = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all = MagicMock(return_value=[row1, row2])
            result.scalars = MagicMock(return_value=scalars_mock)
            return result

        db.execute = _execute

        mocker.patch.object(
            manager, "_refresh_token", new_callable=AsyncMock, return_value=_make_token_row(manager)
        )

        count = await manager.refresh_expiring_tokens(db)
        assert count == 2

    async def test_skips_failed_refresh(self, mocker):
        manager = _make_manager(registry=_make_registry())
        row1 = _make_token_row(manager)
        db = MagicMock()

        async def _execute(_stmt):
            result = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all = MagicMock(return_value=[row1])
            result.scalars = MagicMock(return_value=scalars_mock)
            return result

        db.execute = _execute

        mocker.patch.object(
            manager,
            "_refresh_token",
            new_callable=AsyncMock,
            side_effect=OAuthRefreshError("failed"),
        )

        count = await manager.refresh_expiring_tokens(db)
        assert count == 0
