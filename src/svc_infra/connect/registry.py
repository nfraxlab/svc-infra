from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, SecretStr


class OAuthProvider(BaseModel):
    """Configuration for a third-party OAuth provider.

    This is the single source of truth for OAuth provider definitions.  It
    powers both svc_infra.connect (workspace tool connections that store tokens
    in the DB) and svc_infra.auth (user login that issues JWT sessions).

    client_secret is SecretStr and is never logged or serialized in API
    responses.
    """

    name: str
    client_id: str
    client_secret: SecretStr
    authorize_url: str
    token_url: str
    revoke_url: str | None = None
    default_scopes: list[str] = []
    pkce_required: bool = True
    extra_authorize_params: dict[str, str] = {}
    extra_token_params: dict[str, str] = {}
    token_placement: Literal["header", "query"] = "header"
    userinfo_url: str | None = None

    # --- Identity / login fields ---
    # login_enabled=True means this provider can authenticate users; the auth
    # module will include it in the social login registry automatically.
    login_enabled: bool = False
    # OIDC discovery issuer URL (e.g. "https://accounts.google.com").  When set
    # the auth module appends "/.well-known/openid-configuration" to fetch
    # provider metadata and negotiate the login flow via authlib's OIDC client.
    oidc_discovery_url: str | None = None
    # Governs how the auth module extracts the user's identity after the OAuth
    # code exchange.  "oidc" uses the id_token/userinfo endpoint, "github" and
    # "linkedin" require provider-specific API calls, "standard" fetches
    # userinfo_url with a plain bearer token.
    userinfo_kind: Literal["oidc", "github", "linkedin", "standard"] = "standard"


class ConnectRegistry:
    """Module-level registry for OAuth providers.

    Providers are registered at startup. Built-in providers are loaded from the
    providers/ subpackage when their required env vars are present.
    """

    def __init__(self) -> None:
        self._providers: dict[str, OAuthProvider] = {}

    def register(self, provider: OAuthProvider) -> None:
        """Register a provider by name, replacing any existing registration."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> OAuthProvider | None:
        """Return provider by name, or None if not registered."""
        return self._providers.get(name)

    def list(self) -> list[OAuthProvider]:
        """Return all registered providers."""
        return list(self._providers.values())


registry = ConnectRegistry()
