from __future__ import annotations

from svc_infra.connect.registry import ConnectRegistry, OAuthProvider


def _make_provider(name: str = "test") -> OAuthProvider:
    return OAuthProvider(
        name=name,
        client_id="cid",
        client_secret="csecret",
        authorize_url="https://example.com/auth",
        token_url="https://example.com/token",
        default_scopes=["read"],
    )


class TestConnectRegistry:
    def test_register_and_get(self):
        reg = ConnectRegistry()
        provider = _make_provider("github")
        reg.register(provider)
        assert reg.get("github") is provider

    def test_get_returns_none_for_unknown(self):
        reg = ConnectRegistry()
        assert reg.get("unknown") is None

    def test_list_returns_all(self):
        reg = ConnectRegistry()
        p1 = _make_provider("github")
        p2 = _make_provider("notion")
        reg.register(p1)
        reg.register(p2)
        names = {p.name for p in reg.list()}
        assert names == {"github", "notion"}

    def test_register_replaces_existing(self):
        reg = ConnectRegistry()
        p1 = _make_provider("github")
        p2 = OAuthProvider(
            name="github",
            client_id="new_cid",
            client_secret="new_secret",
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            default_scopes=["repo"],
        )
        reg.register(p1)
        reg.register(p2)
        assert reg.get("github").client_id == "new_cid"

    def test_list_empty_by_default(self):
        reg = ConnectRegistry()
        assert reg.list() == []

    def test_client_secret_is_masked(self):
        provider = _make_provider()
        # SecretStr should not expose secret in repr
        assert "csecret" not in repr(provider.client_secret)

    def test_pkce_required_defaults_true(self):
        provider = _make_provider()
        assert provider.pkce_required is True

    def test_token_placement_defaults_header(self):
        provider = _make_provider()
        assert provider.token_placement == "header"

    def test_login_enabled_defaults_false(self):
        provider = _make_provider()
        assert provider.login_enabled is False

    def test_login_enabled_can_be_set(self):
        provider = OAuthProvider(
            name="discord",
            client_id="cid",
            client_secret="sec",
            authorize_url="https://discord.com/oauth2/authorize",
            token_url="https://discord.com/api/oauth2/token",
            default_scopes=["identify"],
            login_enabled=True,
        )
        assert provider.login_enabled is True

    def test_oidc_discovery_url_defaults_none(self):
        provider = _make_provider()
        assert provider.oidc_discovery_url is None

    def test_oidc_discovery_url_can_be_set(self):
        provider = OAuthProvider(
            name="google",
            client_id="cid",
            client_secret="sec",
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            default_scopes=[],
            oidc_discovery_url="https://accounts.google.com",
        )
        assert provider.oidc_discovery_url == "https://accounts.google.com"

    def test_userinfo_kind_defaults_standard(self):
        provider = _make_provider()
        assert provider.userinfo_kind == "standard"

    def test_userinfo_kind_github(self):
        provider = OAuthProvider(
            name="github",
            client_id="cid",
            client_secret="sec",
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            default_scopes=["user:email"],
            userinfo_kind="github",
        )
        assert provider.userinfo_kind == "github"

    def test_extra_token_params_defaults_empty(self):
        provider = _make_provider()
        assert provider.extra_token_params == {}

    def test_extra_token_params_can_be_set(self):
        provider = OAuthProvider(
            name="notion",
            client_id="cid",
            client_secret="sec",
            authorize_url="https://api.notion.com/v1/oauth/authorize",
            token_url="https://api.notion.com/v1/oauth/token",
            default_scopes=[],
            extra_token_params={"grant_type": "authorization_code"},
        )
        assert provider.extra_token_params == {"grant_type": "authorization_code"}

    def test_list_filters_login_enabled(self):
        reg = ConnectRegistry()
        reg.register(_make_provider("tool-only"))
        reg.register(
            OAuthProvider(
                name="login-capable",
                client_id="cid",
                client_secret="sec",
                authorize_url="https://example.com/auth",
                token_url="https://example.com/token",
                default_scopes=[],
                login_enabled=True,
            )
        )
        login_providers = [p for p in reg.list() if p.login_enabled]
        assert len(login_providers) == 1
        assert login_providers[0].name == "login-capable"
