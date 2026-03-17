from __future__ import annotations

from svc_infra.connect.settings import ConnectSettings
from svc_infra.connect.token_manager import ConnectionTokenManager

_settings: ConnectSettings | None = None
_token_manager: ConnectionTokenManager | None = None


def set_connect_state(
    settings: ConnectSettings,
    token_manager: ConnectionTokenManager,
) -> None:
    global _settings, _token_manager
    _settings = settings
    _token_manager = token_manager


def get_connect_settings() -> ConnectSettings:
    if _settings is None:
        raise RuntimeError(
            "Connect module not initialised. Call add_connect(app) before starting the server."
        )
    return _settings


def get_connect_token_manager() -> ConnectionTokenManager:
    if _token_manager is None:
        raise RuntimeError(
            "Connect module not initialised. Call add_connect(app) before starting the server."
        )
    return _token_manager
