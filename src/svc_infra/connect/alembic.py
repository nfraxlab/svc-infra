from __future__ import annotations


def discover_packages() -> list[str]:
    """Return model packages for Alembic autogenerate discovery."""
    return ["svc_infra.connect.models"]
