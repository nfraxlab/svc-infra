from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from svc_infra.connect.pkce import (
    OAuthExchangeError,
    OAuthRefreshError,
    build_authorize_url,
    coerce_expires_at,
    exchange_code,
    exchange_refresh,
    generate_pkce_pair,
    generate_state,
    validate_redirect,
)
from svc_infra.connect.registry import OAuthProvider


def _make_provider(**kwargs) -> OAuthProvider:
    defaults = {
        "name": "github",
        "client_id": "cid",
        "client_secret": "csecret",
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "default_scopes": ["repo"],
        "pkce_required": True,
        "extra_authorize_params": {},
    }
    defaults.update(kwargs)
    return OAuthProvider(**defaults)


def _mock_http_response(status_code: int, json_data: dict) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = str(json_data)
    return resp


class TestGeneratePkcePair:
    def test_returns_two_strings(self):
        verifier, challenge = generate_pkce_pair()
        assert isinstance(verifier, str)
        assert isinstance(challenge, str)

    def test_verifier_and_challenge_are_different(self):
        verifier, challenge = generate_pkce_pair()
        assert verifier != challenge

    def test_challenge_is_s256_of_verifier(self):
        import base64
        import hashlib

        verifier, challenge = generate_pkce_pair()
        digest = hashlib.sha256(verifier.encode()).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        assert challenge == expected

    def test_each_call_produces_unique_pair(self):
        v1, _ = generate_pkce_pair()
        v2, _ = generate_pkce_pair()
        assert v1 != v2


class TestGenerateState:
    def test_returns_string(self):
        assert isinstance(generate_state(), str)

    def test_unique_on_each_call(self):
        assert generate_state() != generate_state()


class TestValidateRedirect:
    def test_allows_matching_host(self):
        validate_redirect(
            "https://example.com/callback",
            ["example.com"],
            require_https=True,
        )

    def test_rejects_disallowed_host(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_redirect(
                "https://evil.com/callback",
                ["example.com"],
                require_https=True,
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "redirect_not_allowed"

    def test_rejects_http_when_https_required(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_redirect(
                "http://example.com/callback",
                ["example.com"],
                require_https=True,
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "https_required"

    def test_allows_no_netloc(self):
        validate_redirect("pulse-app://callback", [], require_https=False)

    def test_allows_http_when_https_not_required(self):
        validate_redirect(
            "http://localhost:3000/callback",
            ["localhost:3000"],
            require_https=False,
        )


class TestCoerceExpiresAt:
    def test_none_input(self):
        assert coerce_expires_at(None) is None

    def test_non_dict_input(self):
        assert coerce_expires_at("string") is None  # type: ignore[arg-type]

    def test_expires_at_unix_timestamp(self):
        future = datetime.now(UTC) + timedelta(hours=1)
        ts = future.timestamp()
        result = coerce_expires_at({"expires_at": ts})
        assert result is not None
        assert abs((result - future).total_seconds()) < 2

    def test_expires_at_milliseconds(self):
        future = datetime.now(UTC) + timedelta(hours=1)
        ts_ms = future.timestamp() * 1000
        result = coerce_expires_at({"expires_at": ts_ms})
        assert result is not None
        assert abs((result - future).total_seconds()) < 2

    def test_expires_in_seconds(self):
        result = coerce_expires_at({"expires_in": 3600})
        assert result is not None
        expected = datetime.now(UTC) + timedelta(seconds=3600)
        assert abs((result - expected).total_seconds()) < 2

    def test_empty_dict_returns_none(self):
        assert coerce_expires_at({}) is None


class TestBuildAuthorizeUrl:
    def test_includes_required_params(self):
        provider = _make_provider()
        url = build_authorize_url(
            provider,
            state="s",
            pkce_challenge="ch",
            redirect_uri="https://example.com/callback",
        )
        assert "client_id=cid" in url
        assert "response_type=code" in url
        assert "state=s" in url
        assert "code_challenge=ch" in url
        assert "code_challenge_method=S256" in url

    def test_scope_override(self):
        provider = _make_provider()
        url = build_authorize_url(
            provider,
            state="s",
            pkce_challenge="ch",
            redirect_uri="https://example.com/callback",
            scopes=["read", "write"],
        )
        assert "read" in url and "write" in url

    def test_no_pkce_when_not_required(self):
        provider = _make_provider(pkce_required=False)
        url = build_authorize_url(
            provider,
            state="s",
            pkce_challenge="ch",
            redirect_uri="https://example.com/callback",
        )
        assert "code_challenge" not in url

    def test_extra_params_included(self):
        provider = _make_provider(extra_authorize_params={"allow_signup": "false"})
        url = build_authorize_url(
            provider,
            state="s",
            pkce_challenge="ch",
            redirect_uri="https://example.com/callback",
        )
        assert "allow_signup=false" in url


@pytest.mark.asyncio
class TestExchangeCode:
    async def test_success(self):
        provider = _make_provider()
        mock_resp = _mock_http_response(200, {"access_token": "tok", "token_type": "Bearer"})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("svc_infra.connect.pkce.httpx.AsyncClient", return_value=mock_client):
            result = await exchange_code(
                provider,
                code="code123",
                pkce_verifier="verifier",
                redirect_uri="https://example.com/callback",
            )
        assert result["access_token"] == "tok"

    async def test_raises_on_non_200(self):
        provider = _make_provider()
        mock_resp = _mock_http_response(400, {"error": "bad_request"})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("svc_infra.connect.pkce.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(OAuthExchangeError):
                await exchange_code(
                    provider, code="code", pkce_verifier="v", redirect_uri="https://x.com"
                )

    async def test_raises_on_error_field(self):
        provider = _make_provider()
        mock_resp = _mock_http_response(200, {"error": "invalid_grant"})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("svc_infra.connect.pkce.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(OAuthExchangeError):
                await exchange_code(
                    provider, code="code", pkce_verifier="v", redirect_uri="https://x.com"
                )


@pytest.mark.asyncio
class TestExchangeRefresh:
    async def test_success(self):
        provider = _make_provider()
        mock_resp = _mock_http_response(200, {"access_token": "new_tok", "token_type": "Bearer"})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("svc_infra.connect.pkce.httpx.AsyncClient", return_value=mock_client):
            result = await exchange_refresh(provider, "refresh_token_value")
        assert result["access_token"] == "new_tok"

    async def test_raises_on_non_200(self):
        provider = _make_provider()
        mock_resp = _mock_http_response(401, {"error": "invalid_token"})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("svc_infra.connect.pkce.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(OAuthRefreshError):
                await exchange_refresh(provider, "bad_refresh")

    async def test_raises_when_no_access_token(self):
        provider = _make_provider()
        mock_resp = _mock_http_response(200, {"token_type": "Bearer"})
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("svc_infra.connect.pkce.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(OAuthRefreshError):
                await exchange_refresh(provider, "refresh")
