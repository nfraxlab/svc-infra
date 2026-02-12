"""Auto-mounted service status endpoint.

Returns service metadata useful for debugging: name, version,
environment, uptime, Python version, and git commit.

Only mounted in non-production environments (local, dev, test).
For production health checks, use /ping (always mounted) or
/_health/* routes (HealthRegistry).
"""

from __future__ import annotations

import os
import platform
import time
from datetime import UTC, datetime

from starlette.responses import JSONResponse

from svc_infra.api.fastapi.dual.public import public_router
from svc_infra.api.fastapi.paths.generic import STATUS_PATH
from svc_infra.app.env import CURRENT_ENVIRONMENT, PROD_ENV

# Exclude from production — status leaks deployment details
ROUTER_EXCLUDED_ENVIRONMENTS = {PROD_ENV}

router = public_router(tags=["Status"])

# Capture startup time at module load
_START_TIME = time.monotonic()
_START_UTC = datetime.now(UTC)


def _get_commit() -> str | None:
    """Git commit hash from CI/CD environment variables.

    Only populated in deployed environments (preview, staging, etc.)
    where the CI/CD platform sets the commit SHA. Not shown in local
    development since the local HEAD doesn't represent a deployment.
    """
    for var in (
        "GIT_COMMIT",
        "RAILWAY_GIT_COMMIT_SHA",
        "VERCEL_GIT_COMMIT_SHA",
        "RENDER_GIT_COMMIT",
        "HEROKU_SLUG_COMMIT",
    ):
        val = os.getenv(var)
        if val:
            return val[:12]
    return None


def _format_uptime(seconds: float) -> str:
    """Format uptime as human-readable string."""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


@router.get(STATUS_PATH)
async def status() -> JSONResponse:
    """Service status and deployment metadata (non-production only)."""
    # Import lazily to avoid circular imports — app is set up after routers load
    from svc_infra.api.fastapi.setup import get_root_app

    root = get_root_app()
    service_name = root.title if root else "unknown"
    version = root.version if root else "unknown"

    uptime_secs = time.monotonic() - _START_TIME

    body: dict[str, object] = {
        "status": "ok",
        "service": service_name,
        "version": version,
        "env": str(CURRENT_ENVIRONMENT),
        "python": platform.python_version(),
        "uptime": _format_uptime(uptime_secs),
        "started_at": _START_UTC.isoformat(),
        "timestamp": datetime.now(UTC).isoformat(),
    }

    commit = _get_commit()
    if commit:
        body["commit"] = commit

    return JSONResponse(body)
