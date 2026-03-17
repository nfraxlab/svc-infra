"""Basic OAuth integration using svc_infra.connect.

Demonstrates how to mount the connect module on a FastAPI application and
allow users to authorize third-party services (GitHub shown here).

Required environment variables:
    CONNECT_TOKEN_ENCRYPTION_KEY  (generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    CONNECT_API_BASE              (e.g. https://api.example.com)
    CONNECT_DEFAULT_REDIRECT_URI  (e.g. https://app.example.com/done)
    GITHUB_CLIENT_ID
    GITHUB_CLIENT_SECRET

After startup, the connect module exposes three endpoints:
    GET /connect/authorize?provider=github&connection_id=<uuid>
        → {"authorize_url": "https://github.com/login/oauth/authorize?..."}
    GET /connect/callback/github?code=...&state=...
        → 302 redirect to CONNECT_DEFAULT_REDIRECT_URI
    GET /connect/token/<connection_id>?provider=github
        → {"token": "<access_token>", "expires_at": "..."}
"""

from __future__ import annotations

from fastapi import FastAPI

from svc_infra.app import add_sql_db
from svc_infra.connect import add_connect

app = FastAPI(title="Connect Example")

# add_sql_db must be called before add_connect because the connect module
# relies on the database session and ConnectionToken/OAuthState tables.
add_sql_db(app)
add_connect(app)
