"""Tests for auth security resolver functions and guards."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestResolveApiKey:
    """Tests for resolve_api_key function."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_api_key_header(self) -> None:
        """Should return None when X-API-Key header is missing."""
        from svc_infra.api.fastapi.auth.security import resolve_api_key

        request = MagicMock()
        request.headers.get.return_value = ""
        session = AsyncMock()

        result = await resolve_api_key(request, session)
        assert result is None

    @pytest.mark.asyncio
    async def test_raises_401_for_invalid_api_key(self) -> None:
        """Should raise 401 when API key not found."""
        from svc_infra.api.fastapi.auth.security import resolve_api_key

        request = MagicMock()
        request.headers.get.return_value = "ak_abc123_secretpart"
        session = AsyncMock()

        # Mock the query to return no results
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        # Mock both get_apikey_model and select to avoid SQLAlchemy validation
        with (
            patch("svc_infra.api.fastapi.auth.security.get_apikey_model") as mock_get_model,
            patch("svc_infra.api.fastapi.auth.security.select") as mock_select,
        ):
            mock_model = MagicMock()
            mock_model.key_prefix = "key_prefix"
            mock_get_model.return_value = mock_model
            mock_select.return_value.where.return_value = "mock_query"

            with pytest.raises(HTTPException) as exc_info:
                await resolve_api_key(request, session)

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "invalid_api_key"

    @pytest.mark.asyncio
    async def test_raises_401_for_wrong_api_key_hash(self) -> None:
        """Should raise 401 when API key hash doesn't match."""
        from svc_infra.api.fastapi.auth.security import resolve_api_key

        request = MagicMock()
        request.headers.get.return_value = "ak_abc123_secretpart"
        session = AsyncMock()

        # Mock the query to return an API key
        mock_apikey = MagicMock()
        mock_apikey.key_hash = "stored_hash"
        mock_apikey.active = True
        mock_apikey.expires_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_apikey
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("svc_infra.api.fastapi.auth.security.get_apikey_model") as mock_get_model,
            patch("svc_infra.api.fastapi.auth.security.select") as mock_select,
        ):
            mock_model = MagicMock()
            mock_model.key_prefix = "key_prefix"
            mock_model.hash.return_value = "wrong_hash"
            mock_get_model.return_value = mock_model
            mock_select.return_value.where.return_value = "mock_query"

            with pytest.raises(HTTPException) as exc_info:
                await resolve_api_key(request, session)

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "invalid_api_key"

    @pytest.mark.asyncio
    async def test_raises_401_for_revoked_api_key(self) -> None:
        """Should raise 401 when API key is revoked."""
        from svc_infra.api.fastapi.auth.security import resolve_api_key

        request = MagicMock()
        request.headers.get.return_value = "ak_abc123_secretpart"
        session = AsyncMock()

        # Mock the query to return an inactive API key
        mock_apikey = MagicMock()
        mock_apikey.key_hash = "correct_hash"
        mock_apikey.active = False
        mock_apikey.expires_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_apikey
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("svc_infra.api.fastapi.auth.security.get_apikey_model") as mock_get_model,
            patch("svc_infra.api.fastapi.auth.security.select") as mock_select,
            patch("hmac.compare_digest", return_value=True),
        ):
            mock_model = MagicMock()
            mock_model.key_prefix = "key_prefix"
            mock_model.hash.return_value = "correct_hash"
            mock_get_model.return_value = mock_model
            mock_select.return_value.where.return_value = "mock_query"

            with pytest.raises(HTTPException) as exc_info:
                await resolve_api_key(request, session)

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "api_key_revoked"

    @pytest.mark.asyncio
    async def test_raises_401_for_expired_api_key(self) -> None:
        """Should raise 401 when API key is expired."""
        from svc_infra.api.fastapi.auth.security import resolve_api_key

        request = MagicMock()
        request.headers.get.return_value = "ak_abc123_secretpart"
        session = AsyncMock()

        # Mock the query to return an expired API key
        mock_apikey = MagicMock()
        mock_apikey.key_hash = "correct_hash"
        mock_apikey.active = True
        mock_apikey.expires_at = datetime.now(UTC) - timedelta(days=1)  # Expired

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_apikey
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("svc_infra.api.fastapi.auth.security.get_apikey_model") as mock_get_model,
            patch("svc_infra.api.fastapi.auth.security.select") as mock_select,
            patch("hmac.compare_digest", return_value=True),
        ):
            mock_model = MagicMock()
            mock_model.key_prefix = "key_prefix"
            mock_model.hash.return_value = "correct_hash"
            mock_get_model.return_value = mock_model
            mock_select.return_value.where.return_value = "mock_query"

            with pytest.raises(HTTPException) as exc_info:
                await resolve_api_key(request, session)

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "api_key_expired"

    @pytest.mark.asyncio
    async def test_returns_principal_for_valid_api_key(self) -> None:
        """Should return Principal for valid API key."""
        from svc_infra.api.fastapi.auth.security import resolve_api_key

        request = MagicMock()
        request.headers.get.return_value = "ak_abc123_secretpart"
        session = AsyncMock()

        # Mock the query to return a valid API key
        mock_user = MagicMock()
        mock_user.id = "user-123"

        mock_apikey = MagicMock()
        mock_apikey.key_hash = "correct_hash"
        mock_apikey.active = True
        mock_apikey.expires_at = None
        mock_apikey.user = mock_user
        mock_apikey.scopes = ["read", "write"]

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_apikey
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("svc_infra.api.fastapi.auth.security.get_apikey_model") as mock_get_model,
            patch("svc_infra.api.fastapi.auth.security.select") as mock_select,
            patch("hmac.compare_digest", return_value=True),
        ):
            mock_model = MagicMock()
            mock_model.key_prefix = "key_prefix"
            mock_model.hash.return_value = "correct_hash"
            mock_get_model.return_value = mock_model
            mock_select.return_value.where.return_value = "mock_query"

            result = await resolve_api_key(request, session)

            assert result is not None
            assert result.user == mock_user
            assert result.via == "api_key"
            assert result.scopes == ["read", "write"]
            mock_apikey.mark_used.assert_called_once()


class TestResolveBearerOrCookiePrincipal:
    """Tests for resolve_bearer_or_cookie_principal function."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_token(self) -> None:
        """Should return None when no bearer token or cookie."""
        from svc_infra.api.fastapi.auth.security import resolve_bearer_or_cookie_principal

        request = MagicMock()
        request.headers.get.return_value = ""
        request.cookies.get.return_value = ""
        session = AsyncMock()

        with patch("svc_infra.api.fastapi.auth.security.get_auth_settings") as mock_settings:
            mock_settings.return_value.auth_cookie_name = "auth_token"

            result = await resolve_bearer_or_cookie_principal(request, session)
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_token(self) -> None:
        """Should return None when token is invalid."""
        from svc_infra.api.fastapi.auth.security import resolve_bearer_or_cookie_principal

        request = MagicMock()
        request.headers.get.return_value = "Bearer invalid_token"
        request.cookies.get.return_value = ""
        session = AsyncMock()

        with patch("svc_infra.api.fastapi.auth.security.get_auth_settings") as mock_settings:
            mock_settings.return_value.auth_cookie_name = "auth_token"

            with patch("svc_infra.api.fastapi.auth.security.get_auth_state") as mock_state:
                mock_user_model = MagicMock()
                mock_strategy = MagicMock()
                mock_strategy.read_token = AsyncMock(side_effect=Exception("Invalid token"))
                mock_state.return_value = (mock_user_model, lambda: mock_strategy, None)

                result = await resolve_bearer_or_cookie_principal(request, session)
                assert result is None

    @pytest.mark.asyncio
    async def test_raises_401_for_disabled_user(self) -> None:
        """Should raise 401 when user is disabled."""
        from svc_infra.api.fastapi.auth.security import resolve_bearer_or_cookie_principal

        request = MagicMock()
        request.headers.get.return_value = "Bearer valid_token"
        request.cookies.get.return_value = ""
        session = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = "user-123"

        mock_db_user = MagicMock()
        mock_db_user.is_active = False

        session.get = AsyncMock(return_value=mock_db_user)

        with patch("svc_infra.api.fastapi.auth.security.get_auth_settings") as mock_settings:
            mock_settings.return_value.auth_cookie_name = "auth_token"

            with patch("svc_infra.api.fastapi.auth.security.get_auth_state") as mock_state:
                mock_user_model = MagicMock()
                mock_strategy = MagicMock()
                mock_strategy.read_token = AsyncMock(return_value=mock_user)
                mock_state.return_value = (mock_user_model, lambda: mock_strategy, None)

                with patch("svc_infra.api.fastapi.auth.security.get_user_scope_resolver"):
                    with pytest.raises(HTTPException) as exc_info:
                        await resolve_bearer_or_cookie_principal(request, session)

                    assert exc_info.value.status_code == 401
                    assert exc_info.value.detail == "account_disabled"


class TestRequireRolesGuard:
    """Tests for RequireRoles guard function."""

    @pytest.mark.asyncio
    async def test_require_roles_passes_with_matching_roles(self) -> None:
        """Should pass when user has required roles."""
        from svc_infra.api.fastapi.auth.security import Principal, RequireRoles

        mock_user = MagicMock()
        mock_user.roles = ["admin", "user"]

        principal = Principal(user=mock_user, scopes=[], via="jwt")

        # Get the guard function
        guard_depends = RequireRoles("admin")
        # Extract the actual guard function from Depends
        guard_func = guard_depends.dependency

        result = await guard_func(principal)
        assert result == principal

    @pytest.mark.asyncio
    async def test_require_roles_fails_without_roles(self) -> None:
        """Should raise 403 when user lacks required roles."""
        from svc_infra.api.fastapi.auth.security import Principal, RequireRoles

        mock_user = MagicMock()
        mock_user.roles = ["user"]

        principal = Principal(user=mock_user, scopes=[], via="jwt")

        guard_depends = RequireRoles("admin")
        guard_func = guard_depends.dependency

        with pytest.raises(HTTPException) as exc_info:
            await guard_func(principal)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "forbidden"

    @pytest.mark.asyncio
    async def test_require_roles_with_custom_resolver(self) -> None:
        """Should use custom resolver for roles."""
        from svc_infra.api.fastapi.auth.security import Principal, RequireRoles

        mock_user = MagicMock()
        mock_user.custom_roles = ["superuser"]

        principal = Principal(user=mock_user, scopes=[], via="jwt")

        def custom_resolver(user):
            return user.custom_roles

        guard_depends = RequireRoles("superuser", resolver=custom_resolver)
        guard_func = guard_depends.dependency

        result = await guard_func(principal)
        assert result == principal


class TestRequireScopesGuard:
    """Tests for RequireScopes guard function."""

    @pytest.mark.asyncio
    async def test_require_scopes_passes_with_matching_scopes(self) -> None:
        """Should pass when principal has required scopes."""
        from svc_infra.api.fastapi.auth.security import Principal, RequireScopes

        principal = Principal(user=MagicMock(), scopes=["read", "write"], via="jwt")

        guard_depends = RequireScopes("read", "write")
        guard_func = guard_depends.dependency

        result = await guard_func(principal)
        assert result == principal

    @pytest.mark.asyncio
    async def test_require_scopes_fails_without_scopes(self) -> None:
        """Should raise 403 when principal lacks required scopes."""
        from svc_infra.api.fastapi.auth.security import Principal, RequireScopes

        principal = Principal(user=MagicMock(), scopes=["read"], via="jwt")

        guard_depends = RequireScopes("read", "write", "admin")
        guard_func = guard_depends.dependency

        with pytest.raises(HTTPException) as exc_info:
            await guard_func(principal)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "insufficient_scope"


class TestRequireAnyScopeGuard:
    """Tests for RequireAnyScope guard function."""

    @pytest.mark.asyncio
    async def test_require_any_scope_passes_with_one_scope(self) -> None:
        """Should pass when principal has at least one required scope."""
        from svc_infra.api.fastapi.auth.security import Principal, RequireAnyScope

        principal = Principal(user=MagicMock(), scopes=["read"], via="jwt")

        guard_depends = RequireAnyScope("read", "write", "admin")
        guard_func = guard_depends.dependency

        result = await guard_func(principal)
        assert result == principal

    @pytest.mark.asyncio
    async def test_require_any_scope_fails_without_any_scope(self) -> None:
        """Should raise 403 when principal has none of the required scopes."""
        from svc_infra.api.fastapi.auth.security import Principal, RequireAnyScope

        principal = Principal(user=MagicMock(), scopes=["other"], via="jwt")

        guard_depends = RequireAnyScope("read", "write", "admin")
        guard_func = guard_depends.dependency

        with pytest.raises(HTTPException) as exc_info:
            await guard_func(principal)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "insufficient_scope"


class TestPrincipalClass:
    """Tests for Principal class."""

    def test_principal_with_user(self) -> None:
        """Should create Principal with user."""
        from svc_infra.api.fastapi.auth.security import Principal

        mock_user = MagicMock()
        mock_user.id = "user-123"

        principal = Principal(user=mock_user, scopes=["read"], via="jwt")

        assert principal.user == mock_user
        assert principal.scopes == ["read"]
        assert principal.via == "jwt"
        assert principal.api_key is None

    def test_principal_with_api_key(self) -> None:
        """Should create Principal with API key."""
        from svc_infra.api.fastapi.auth.security import Principal

        mock_user = MagicMock()
        mock_api_key = MagicMock()

        principal = Principal(
            user=mock_user,
            scopes=["read", "write"],
            via="api_key",
            api_key=mock_api_key,
        )

        assert principal.user == mock_user
        assert principal.scopes == ["read", "write"]
        assert principal.via == "api_key"
        assert principal.api_key == mock_api_key

    def test_principal_defaults(self) -> None:
        """Should use default values."""
        from svc_infra.api.fastapi.auth.security import Principal

        principal = Principal()

        assert principal.user is None
        assert principal.scopes == []
        assert principal.via == "jwt"
        assert principal.api_key is None


class TestCurrentPrincipal:
    """Tests for _current_principal function."""

    @pytest.mark.asyncio
    async def test_returns_jwt_principal_when_present(self) -> None:
        """Should return JWT principal when available."""
        from svc_infra.api.fastapi.auth.security import Principal, _current_principal

        mock_user = MagicMock()
        jwt_principal = Principal(user=mock_user, scopes=["read"], via="jwt")

        result = await _current_principal(
            request=MagicMock(),
            session=AsyncMock(),
            jwt_or_cookie=jwt_principal,
            ak=None,
        )

        assert result == jwt_principal

    @pytest.mark.asyncio
    async def test_returns_api_key_principal_when_no_jwt(self) -> None:
        """Should return API key principal when no JWT."""
        from svc_infra.api.fastapi.auth.security import Principal, _current_principal

        mock_user = MagicMock()
        ak_principal = Principal(user=mock_user, scopes=["read"], via="api_key")

        result = await _current_principal(
            request=MagicMock(),
            session=AsyncMock(),
            jwt_or_cookie=None,
            ak=ak_principal,
        )

        assert result == ak_principal

    @pytest.mark.asyncio
    async def test_raises_401_when_no_principal(self) -> None:
        """Should raise 401 when no principal available."""
        from svc_infra.api.fastapi.auth.security import _current_principal

        with pytest.raises(HTTPException) as exc_info:
            await _current_principal(
                request=MagicMock(),
                session=AsyncMock(),
                jwt_or_cookie=None,
                ak=None,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Missing credentials"


class TestOptionalPrincipal:
    """Tests for _optional_principal function."""

    @pytest.mark.asyncio
    async def test_returns_jwt_principal_when_present(self) -> None:
        """Should return JWT principal when available."""
        from svc_infra.api.fastapi.auth.security import Principal, _optional_principal

        mock_user = MagicMock()
        jwt_principal = Principal(user=mock_user, scopes=["read"], via="jwt")

        result = await _optional_principal(
            request=MagicMock(),
            session=AsyncMock(),
            jwt_or_cookie=jwt_principal,
            ak=None,
        )

        assert result == jwt_principal

    @pytest.mark.asyncio
    async def test_returns_none_when_no_principal(self) -> None:
        """Should return None when no principal available."""
        from svc_infra.api.fastapi.auth.security import _optional_principal

        result = await _optional_principal(
            request=MagicMock(),
            session=AsyncMock(),
            jwt_or_cookie=None,
            ak=None,
        )

        assert result is None
