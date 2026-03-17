from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectSettings(BaseSettings):
    """Configuration for svc_infra.connect. All fields read from environment variables.

    Follows the same BaseSettings pattern as AuthSettings and EmailSettings.
    connect_token_encryption_key is SecretStr and is never logged or serialized.
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    connect_token_encryption_key: SecretStr
    """Fernet symmetric key used to encrypt tokens at rest.
    Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """

    connect_api_base: str = ""
    """Base URL of the API (e.g. https://api.example.com). Used to build callback URLs."""

    connect_default_redirect_uri: str = ""
    """Fallback redirect URI when OAuthState.redirect_uri is empty.
    Supports custom URL schemes for native apps (e.g. pulse-app://oauth/callback).
    """

    connect_state_ttl_seconds: int = 600
    """TTL for OAuthState rows in seconds. Default: 10 minutes."""

    connect_redirect_allow_hosts: str = ""
    """Comma-separated list of allowed redirect hosts.
    Validated via validate_redirect() from connect/pkce.py.
    Example: api.example.com,app.example.com
    """

    def allowed_hosts(self) -> list[str]:
        """Parse connect_redirect_allow_hosts into a list of host strings."""
        return [h.strip() for h in self.connect_redirect_allow_hosts.split(",") if h.strip()]
