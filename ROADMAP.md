# svc-infra Development Roadmap

> **Current Version**: 1.1.0
> **Target v1.0.0**: Phase 0 completion (Email Infrastructure)
> **Target v1.5.0**: Phase 1 completion (`svc_infra.connect` — Connection OAuth module)
> **Target v2.0.0**: Phase 1-6 completion

---

## Phase 1: Connection OAuth Module — `svc_infra.connect` (v1.5.x)

**Goal**: Build a first-class `svc_infra.connect` module that brings Nango-equivalent OAuth token
management into svc-infra, plus full support for the MCP Authorization spec (RFC 9728 + OAuth 2.1
+ PKCE). Any nfrax application (pulse, folio, aspect) mounts this with one line and gets complete
OAuth flows for third-party service connections — with tokens stored, encrypted, and auto-refreshed
inside the app's own database. For MCP-specific operations, the module delegates to `ai-infra`'s
`MCPClient` where applicable rather than reimplementing MCP protocol logic.

**Why not Nango (hosted)?** Token custody stays on your infrastructure. No per-connection pricing.
No vendor dependency.

**Why not Nango (self-hosted)?** Same functionality, zero new infrastructure, shared DB with the
rest of app state, and the MCP Authorization spec layer that Nango does not model.

**Existing svc-infra infrastructure reused by this module:**

| What | Where | How it is reused |
|---|---|---|
| `ModelBase` | `svc_infra.db.sql.base` | Base class for every new model in this module |
| `GUID()` | `svc_infra.db.sql.types` | Portable UUID column, consistent with all other models |
| `SqlRepository` | `svc_infra.db.sql.repository` | `ConnectionTokenManager` wraps it for upsert / lookup |
| `SqlSessionDep` | `svc_infra.api.fastapi.db.sql.session` | Typed `Annotated[AsyncSession, Depends(get_session)]` used in all router endpoints |
| `_gen_pkce_pair()` | `oauth_router.py` | Implementation moved verbatim to `connect/pkce.py` as public `generate_pkce_pair()` |
| `_validate_redirect()` | `oauth_router.py` | Copied to `connect/pkce.py` for redirect URI allow-list enforcement |
| `_coerce_expires_at()` | `oauth_router.py` | Copied to `connect/pkce.py` to normalise `expires_at`/`expires_in` from provider token responses |
| `discover_packages()` | `apf_payments/alembic.py` | Same pattern: `connect/alembic.py` exports `discover_packages()` listing `svc_infra.connect.models` |
| `init_alembic()` | `svc_infra.db.sql.core` | Alembic init + migration commands just pass `"svc_infra.connect.models"` to the existing CLI |
| `BaseSettings` / `pydantic_settings` | `email/settings.py`, `auth/settings.py` | `ConnectSettings` follows the exact same pattern |
| Lifespan wrapping | `api/fastapi/db/sql/add.py` `add_sql_db()` | `add_connect()` uses the same `existing_lifespan` wrap idiom |
| `InMemoryScheduler` | `svc_infra.jobs` | Background token-refresh and `OAuthState` cleanup registered via `easy_jobs()` |

---

### 1.1 Data Models

> Foundational DB models for connection tokens and provider configuration.
> Follows the exact same SQLAlchemy conventions as `ProviderAccount` (`security/oauth_models.py`)
> and `AuthSession` (`security/models.py`) — `ModelBase`, `GUID()`, `DateTime(timezone=True)`,
> `text("CURRENT_TIMESTAMP")` server defaults, `onupdate` lambda for `updated_at`.

**Files to create:**
- `src/svc_infra/connect/models.py`
- `src/svc_infra/connect/alembic.py` — Alembic package discovery; same pattern as
  `src/svc_infra/apf_payments/alembic.py`; exports `discover_packages() -> list[str]`
  returning `["svc_infra.connect.models"]`; no custom env.py or separate migrations folder

**`ConnectionToken` model** — inherits `ModelBase`; keyed to a `(user_id, connection_id)` pair;
distinct from `ProviderAccount` which is keyed to a login provider account:

- [x] `id: Mapped[uuid.UUID]` — `GUID()` primary key, `default=uuid.uuid4`
- [x] `connection_id: Mapped[uuid.UUID]` — `GUID()`; logical FK to consuming app's connection
  table; not enforced at DB level so the connect module has no hard dep on app schemas
- [x] `user_id: Mapped[uuid.UUID]` — `GUID()`, `ForeignKey("users.id", ondelete="CASCADE")`,
  `index=True`; mirrors `ProviderAccount.user_id` convention exactly
- [x] `provider: Mapped[str]` — `String(255)`, `index=True`; `"github"`, `"notion"`, or
  `"mcp:https://api.example.com/mcp/"` for dynamically discovered MCP servers
- [x] `access_token: Mapped[str]` — `Text`; Fernet-encrypted at rest; never logged
- [x] `refresh_token: Mapped[str | None]` — `Text`; Fernet-encrypted; `None` for non-refreshable
  tokens (e.g. PATs)
- [x] `token_type: Mapped[str]` — `String(32)`, default `"Bearer"`
- [x] `expires_at: Mapped[datetime | None]` — `DateTime(timezone=True)`; `None` = non-expiring
- [x] `scopes: Mapped[list | None]` — `JSON` column; list of scope strings
- [x] `raw_token: Mapped[dict | None]` — `JSON`; full provider response; Fernet-encrypted JSON
  blob; preserves provider-specific fields (`installation_id`, `bot_id`, etc.)
- [x] `created_at` — `DateTime(timezone=True)`, `server_default=text("CURRENT_TIMESTAMP")`
- [x] `updated_at` — `DateTime(timezone=True)`, `server_default=text("CURRENT_TIMESTAMP")`,
  `onupdate=lambda: datetime.now(UTC)` — same pattern as `ProviderAccount.updated_at`
- [x] `UniqueConstraint("connection_id", "user_id", "provider")` — named
  `uq_connection_token`
- [x] `Index("ix_connection_tokens_user_provider", "user_id", "provider")`

**`OAuthState` model** — inherits `ModelBase`; short-lived PKCE/state store; replaces the
`SessionMiddleware`-based state that `oauth_router.py` uses, enabling stateless API servers:

- [x] `id: Mapped[uuid.UUID]` — `GUID()` primary key, `default=uuid.uuid4`
- [x] `state: Mapped[str]` — `String(128)`, `index=True`; 32-byte URL-safe random value;
  SHA-256 verified on callback to prevent timing oracle attacks
- [x] `pkce_verifier: Mapped[str]` — `Text`; stored server-side; sent to token endpoint
- [x] `provider: Mapped[str]` — `String(255)`
- [x] `connection_id: Mapped[uuid.UUID | None]` — `GUID()`; pre-linked before redirect
- [x] `user_id: Mapped[uuid.UUID]` — `GUID()`, `ForeignKey("users.id", ondelete="CASCADE")`
- [x] `redirect_uri: Mapped[str]` — `Text`; validated against allow-list using
  `_validate_redirect()` from `oauth_router.py` before storage
- [x] `expires_at: Mapped[datetime]` — `DateTime(timezone=True)`, `index=True`; 10-minute TTL;
  background `InMemoryScheduler` job purges expired rows
- [x] `created_at` — `DateTime(timezone=True)`, `server_default=text("CURRENT_TIMESTAMP")`

---

### 1.2 Provider Registry

> Static provider configuration; apps register providers at startup.

**Files to create:**
- `src/svc_infra/connect/registry.py`
- `src/svc_infra/connect/providers/` (built-in provider definitions)
  - `__init__.py`
  - `github.py`
  - `notion.py`
  - `google.py`
  - `microsoft.py`
  - `slack.py`
  - `linear.py`
  - `atlassian.py`

**`OAuthProvider` dataclass** — follows `OIDCProvider` / `PasswordClient` Pydantic model
conventions from `auth/settings.py`; use `pydantic.BaseModel` (not `dataclass`) to stay
consistent with the rest of the auth module:

- [x] `name: str` — unique identifier
- [x] `client_id: str`
- [x] `client_secret: SecretStr` — `pydantic.SecretStr`; never logged or serialized in
  responses; same as `OIDCProvider.client_secret`
- [x] `authorize_url: str`
- [x] `token_url: str`
- [x] `revoke_url: str | None` — default `None`
- [x] `default_scopes: list[str]`
- [x] `pkce_required: bool` — default `True` (all modern providers)
- [x] `extra_authorize_params: dict[str, str]` — provider-specific params
  (e.g. GitHub needs `allow_signup=false` for org installs)
- [x] `token_placement: Literal["header", "query"]` — default `"header"`
- [x] `userinfo_url: str | None` — for fetching account metadata after auth

**`ConnectRegistry` (module-level singleton):**

- [x] `register(provider: OAuthProvider) -> None`
- [x] `get(name: str) -> OAuthProvider | None`
- [x] `list() -> list[OAuthProvider]`
- [x] Built-in providers loaded from `providers/` at import time if env vars present

**Built-in provider implementations:**

- [x] `github.py` — `authorize_url`, `token_url`, scope options (`repo`, `copilot`, `user:email`)
- [x] `notion.py` — Notion OAuth 2.0 (non-PKCE, but module adds PKCE layer)
- [x] `google.py` — reuses the OIDC issuer URL from `OIDCProvider` in `auth/settings.py`;
  maps Google's `openid email profile` scopes to connection-appropriate drive/calendar scopes
- [x] `microsoft.py` — reuses Entra tenant config from `AuthSettings.ms_tenant` in
  `auth/settings.py`; separate `OAuthProvider` instance for connection scope (not login)
- [x] `slack.py` — Slack v2 OAuth with bot/user token distinction
- [x] `linear.py` — Linear OAuth 2.0
- [x] `atlassian.py` — Atlassian OAuth 2.0 (Jira, Confluence)

---

### 1.3 MCP Authorization Spec Discovery

> RFC 9728 resource metadata → OAuth authorization server metadata → dynamic provider config.
> Delegates MCP protocol operations to `ai_infra.mcp.client.MCPClient`.

**Files to create:**
- `src/svc_infra/connect/mcp_discovery.py`

**`MCPOAuthDiscovery` class:**

- [x] `discover(mcp_server_url: str) -> OAuthProvider`
  - Fetches `{mcp_server_url}/.well-known/oauth-protected-resource` (RFC 9728)
  - Parses `authorization_servers[0]` from the resource metadata
  - Fetches `{auth_server}/.well-known/oauth-authorization-server` (RFC 8414)
  - Extracts `authorization_endpoint`, `token_endpoint`, `revocation_endpoint`,
    `code_challenge_methods_supported`
  - Returns a fully-populated `OAuthProvider` with `name = "mcp:{mcp_server_url}"`
  - Caches results in-process (TTL 1 hour) — MCP server metadata rarely changes
  - Raises `MCPOAuthNotSupported` if server returns no `www-authenticate` header or
    no `resource_metadata` field

- [x] `MCPOAuthNotSupported` exception — raised when a server does not implement the spec;
  callers fall back to the manual-token UX

- [x] `parse_www_authenticate(header: str) -> dict[str, str]`
  — parses `Bearer resource_metadata="..."` header format

- [x] `is_mcp_oauth_supported(mcp_server_url: str) -> bool`
  — lightweight check before full discovery; probes with a bare POST and inspects 401 headers

**Integration with `ai-infra`:**

- [x] After token acquisition, `ConnectionToken.access_token` is injected into the `headers`
  config of the MCP connection; `ai_infra.mcp.client.MCPClient` picks it up through the
  standard `Authorization: Bearer` header path — no changes needed in ai-infra
- [x] `svc_infra.connect` is not aware of MCP protocol internals; it is only responsible for
  obtaining and refreshing the OAuth token; tool discovery and invocation remain in ai-infra

---

### 1.4 PKCE Flow Engine

> Core OAuth 2.1 + PKCE flow. Pulls three private helpers out of `oauth_router.py` and
> exposes them as a public module so the connect router and token manager can import them
> without depending on the auth router internals.

**Files to create:**
- `src/svc_infra/connect/pkce.py`

- [x] `generate_pkce_pair() -> tuple[str, str]` — moves `_gen_pkce_pair()` from
  `oauth_router.py` verbatim; same `base64.urlsafe_b64encode` + SHA-256 implementation
- [x] `validate_redirect(url, allow_hosts, *, require_https) -> None` — moves
  `_validate_redirect()` from `oauth_router.py` verbatim; raises `HTTPException(400)` on
  disallowed or non-HTTPS URIs
- [x] `coerce_expires_at(token_dict) -> datetime | None` — moves `_coerce_expires_at()` from
  `oauth_router.py` verbatim; handles both `expires_at` (unix timestamp) and `expires_in`
  (seconds) fields from provider token responses
- [x] `generate_state() -> str` — 32-byte URL-safe random state value
- [x] `build_authorize_url(provider, state, pkce_challenge, redirect_uri, scopes, extra) -> str`
  — constructs the full redirect URL with all required OAuth parameters
- [x] `exchange_code(provider, code, pkce_verifier, redirect_uri) -> dict`
  — async; exchanges authorization code for token using `httpx`; raises `OAuthExchangeError`
  on non-200 or error JSON
- [x] `exchange_refresh(provider, refresh_token_str) -> dict`
  — async; `refresh_token` grant; raises `OAuthRefreshError` if refresh fails or
  refresh token field is absent

---

### 1.5 Token Lifecycle Manager

> Storage, retrieval, and background refresh of `ConnectionToken` rows.
> Wraps `SqlRepository` for all DB access; uses `Fernet` for encryption (new to this module;
> no existing encryption utility in svc-infra — this is the first one).

**Files to create:**
- `src/svc_infra/connect/token_manager.py`

**`ConnectionTokenManager` class** — wraps `SqlRepository(model=ConnectionToken)` from
`svc_infra.db.sql.repository`; session parameter is always `AsyncSession` obtained via
`SqlSessionDep` in routers or passed directly in background tasks:

- [x] `__init__(self, encryption_key: str)` — initialises `Fernet(encryption_key.encode())`;
  validates key format at construction time

- [x] `store(db, user_id, connection_id, provider, token_response) -> ConnectionToken`
  — upserts on `(connection_id, user_id, provider)` conflict; encrypts `access_token`,
  `refresh_token`, and `raw_token` via Fernet before writing; calls `coerce_expires_at()`
  from `connect/pkce.py` to normalise `expires_at`

- [x] `get(db, connection_id, user_id, provider) -> ConnectionToken | None`

- [x] `get_valid_token(db, connection_id, user_id, provider) -> str | None`
  — returns decrypted access token; auto-refreshes if `expires_at < now + 5 minutes`;
  returns `None` if no token or refresh fails; never raises (logs warning instead)

- [x] `revoke(db, connection_id, user_id, provider) -> None`
  — calls provider `revoke_url` if present; deletes DB row

- [x] `delete_all_for_connection(db, connection_id) -> None`
  — used when a connection is deleted by the consuming app

- [x] Background refresh task: `refresh_expiring_tokens(db) -> int`
  — refreshes all tokens expiring in the next 10 minutes; registered as a periodic
  `InMemoryScheduler` job via `easy_jobs()` from `svc_infra.jobs`; returns count of
  refreshed tokens

---

### 1.6 FastAPI Router

> Three endpoints mounted by consuming apps via `add_connect(app)`.
> All authenticated endpoints use `SqlSessionDep` from `svc_infra.api.fastapi.db.sql.session`
> and the `Identity` / `current_user` dependency from the auth module — same pattern as
> `apikey_router.py` and `account.py`.

**Files to create:**
- `src/svc_infra/connect/router.py`
- `src/svc_infra/connect/add.py`
- `src/svc_infra/connect/settings.py`

**Endpoints:**

- [x] `GET /connect/authorize`
  - Dependencies: `db: SqlSessionDep`, authenticated `Identity`
  - Query params: `connection_id`, `provider` (static) or `mcp_server_url` (dynamic discovery)
  - If `mcp_server_url` given: runs `MCPOAuthDiscovery.discover()`, registers provider
    in-process
  - Validates `redirect_uri` (if provided) via `validate_redirect()` from `connect/pkce.py`
  - Generates PKCE pair + state; persists `OAuthState` row with 10-min TTL
  - Returns `{"authorize_url": "..."}` — client opens this URL; does not redirect server-side
    (avoids CORS issues with API-first apps)

- [x] `GET /connect/callback/{provider}`
  - Public endpoint; state param carries identity — no auth header required
  - `db: SqlSessionDep` dependency for OAuthState + ConnectionToken writes
  - Validates `state` param against `OAuthState` row; rejects replayed/expired states
  - Exchanges code via `pkce.exchange_code()`
  - Stores `ConnectionToken` via `token_manager.store()`
  - Deletes consumed `OAuthState` row (atomic with token store)
  - Redirects to `OAuthState.redirect_uri` with `?success=true&connection_id=<id>`
    or `?error=<reason>` on failure
  - Registered callback URL shape: `{CONNECT_API_BASE}/connect/callback/{provider}`

- [x] `GET /connect/token/{connection_id}`
  - Dependencies: `db: SqlSessionDep`, authenticated `Identity`
  - Returns `{"token": "<access_token>", "expires_at": "..."}` for the calling user
  - Returns 404 if no token stored; 502 if refresh fails

**`ConnectSettings`** — `pydantic_settings.BaseSettings` subclass; same pattern as
`AuthSettings` and `EmailSettings`; all fields read from env vars automatically:

- [x] `connect_token_encryption_key: SecretStr` — required; Fernet key; never logged or
  serialized; generate with
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- [x] `connect_api_base: str` — base URL of the API; used to construct callback URLs
- [x] `connect_default_redirect_uri: str` — fallback if `OAuthState.redirect_uri` is empty;
  supports custom URL schemes for native apps (e.g. `pulse-app://oauth/callback`)
- [x] `connect_state_ttl_seconds: int` — default 600 (10 minutes)
- [x] `connect_redirect_allow_hosts: str` — comma-separated allow-list; validated via
  `validate_redirect()` from `connect/pkce.py`

**`add_connect(app, *, prefix="/connect") -> None`** — follows the lifespan wrapping idiom
from `add_sql_db()` in `api/fastapi/db/sql/add.py`:

- [x] Reads `ConnectSettings()` and validates `connect_token_encryption_key` at startup;
  raises `RuntimeError` if missing (same guard pattern as `add_sql_db()` URL check)
- [x] Wraps any existing `app.router.lifespan_context` with startup/shutdown hooks
- [x] Mounts `connect.router` under `prefix`
- [x] Calls `easy_jobs()` from `svc_infra.jobs` to obtain `(queue, scheduler)`; registers
  `refresh_expiring_tokens` as a 5-minute interval job and `OAuthState` cleanup as a
  10-minute interval job on `InMemoryScheduler`

---

### 1.7 `__init__.py` Public API

**Files to create:**
- `src/svc_infra/connect/__init__.py`

```python
from svc_infra.connect.add import add_connect
from svc_infra.connect.mcp_discovery import MCPOAuthDiscovery, MCPOAuthNotSupported
from svc_infra.connect.models import ConnectionToken, OAuthState
from svc_infra.connect.registry import ConnectRegistry, OAuthProvider
from svc_infra.connect.settings import ConnectSettings
from svc_infra.connect.token_manager import ConnectionTokenManager

__all__ = [
    "add_connect",
    "MCPOAuthDiscovery",
    "MCPOAuthNotSupported",
    "ConnectionToken",
    "OAuthState",
    "ConnectRegistry",
    "OAuthProvider",
    "ConnectSettings",
    "ConnectionTokenManager",
]
```

---

### 1.8 pulse Integration

> How pulse consumes `svc_infra.connect` after the module is built.

**Changes in pulse:**

- [x] `api/src/pulse/main.py` — call `add_connect(app)` alongside existing `add_*` calls;
  register `github` provider with Copilot scope
- [x] `connections/client.py` — `_headers()` calls
  `await token_manager.get_valid_token(db, connection_id, user_id, provider)`; injects
  result as `Authorization: Bearer` header; existing config-based headers remain as fallback
- [x] `routers/v0/connections.py` — sync endpoint: when `MCPOAuthNotSupported` is not raised,
  include `{"oauth_supported": true, "authorize_url": "/connect/authorize?..."}` in 502
  response body so Swift client can offer "Sign in" instead of "Paste token"
- [x] `ConnectionsSettingsView.swift` — detects `oauth_supported: true` in error response;
  opens `ASWebAuthenticationSession` with the `authorize_url`; on callback deep link
  `pulse-app://oauth/callback?success=true&connection_id=<id>`, triggers sync automatically
- [x] Manual token sheet (currently implemented) stays as fallback for servers that do not
  support OAuth spec

---

### 1.9 Tests

**Files to create:**
- `tests/unit/connect/test_models.py`
- `tests/unit/connect/test_registry.py`
- `tests/unit/connect/test_mcp_discovery.py`
- `tests/unit/connect/test_pkce.py`
- `tests/unit/connect/test_token_manager.py`
- `tests/unit/connect/test_router.py`
- `tests/integration/connect/test_oauth_flow.py`

- [x] Unit tests for token encryption/decryption round-trip
- [x] Unit tests for PKCE pair generation + URL construction
- [x] Unit tests for `MCPOAuthDiscovery` with mocked HTTP responses
  - Valid resource metadata → valid auth server metadata → populated `OAuthProvider`
  - Server returns 200 (no 401) → `MCPOAuthNotSupported`
  - Malformed `www-authenticate` header → `MCPOAuthNotSupported`
- [x] Unit tests for `ConnectionTokenManager` with in-memory SQLite
  - Store + retrieve round-trip with encryption
  - Auto-refresh triggers when token within 5-minute expiry window
  - `get_valid_token` returns `None` gracefully on refresh failure (no raise)
- [x] Unit tests for `OAuthState` TTL expiry and cleanup
- [x] Integration test for full authorize → callback → token retrieval flow
  (mocked provider HTTP; real DB; real PKCE verification)
- [x] Integration test for MCP discovery → authorize → callback with GitHub Copilot
  endpoint shapes mocked

---

### 1.10 Documentation

**Files to create:**
- `docs/connect.md`
- `docs/connect-mcp-oauth.md`
- `examples/connect/basic_oauth.py`
- `examples/connect/mcp_oauth.py`
- `examples/connect/fastapi_integration.py`

- [x] **`docs/connect.md`** — module overview, quickstart, provider configuration reference,
  env vars, callback URL registration guide
- [x] **`docs/connect-mcp-oauth.md`** — MCP Authorization spec explained, how discovery works,
  which servers currently support it (GitHub Copilot confirmed), fallback behavior
- [x] **`examples/connect/basic_oauth.py`** — static GitHub provider, full flow in one file
- [x] **`examples/connect/mcp_oauth.py`** — dynamic MCP discovery flow
- [x] **`examples/connect/fastapi_integration.py`** — `add_connect()` in a full FastAPI app with
  token injection into httpx client

---

### Phase 1 Success Criteria

| Deliverable | Status |
|---|---|
| `ConnectionToken` + `OAuthState` DB models | [x] |
| `ConnectRegistry` with 7 built-in providers | [x] |
| `MCPOAuthDiscovery` (RFC 9728 + RFC 8414) | [x] |
| PKCE flow engine (generate, authorize URL, exchange, refresh) | [x] |
| `ConnectionTokenManager` (store, retrieve, auto-refresh) | [x] |
| FastAPI router (`/connect/authorize`, `/connect/callback`, `/connect/token`) | [x] |
| `add_connect(app)` one-line mount | [x] |
| Token encryption at rest | [x] |
| `OAuthState` TTL + cleanup job | [x] |
| pulse integration plan documented | [x] |
| Tests: unit + integration, ≥80% coverage for `connect/` | [x] |
| `docs/connect.md` + `docs/connect-mcp-oauth.md` | [x] |
| Examples working | [x] |

---

## Phase 0: Email Infrastructure Module (v1.0.x)

**Goal**: Create a first-class email module following the same DX patterns as `storage`, `webhooks`, and other svc-infra capabilities. Unified API across multiple providers with zero-config setup.

**Current State**:
- Email exists but is buried in `api/fastapi/auth/sender.py`
- SMTP only, no modern providers
- Tightly coupled to auth settings
- Not exposed in public API
- Synchronous (blocking)

**Target State**:
- Top-level `svc_infra.email` module
- Multiple backend support (Console, SMTP, Resend, SendGrid, AWS SES, Postmark)
- Unified `send()` API across all providers
- Async-first with sync fallback
- Template support (Jinja2)
- `add_email(app)` / `easy_email()` / `get_email()` pattern
- Auth module migrated to use new email infrastructure

---

### 0.1 Core Email Infrastructure

> Create the foundational email module structure.

**Files to create:**
- `src/svc_infra/email/__init__.py`
- `src/svc_infra/email/base.py`
- `src/svc_infra/email/settings.py`
- `src/svc_infra/email/add.py`
- `src/svc_infra/email/easy.py`

- [x] **base.py - Email Backend Protocol**
  - [x] `EmailBackend` protocol with `send()` and `send_sync()` methods
  - [x] `EmailMessage` dataclass: `to`, `subject`, `html`, `text`, `from_addr`, `reply_to`, `cc`, `bcc`, `attachments`, `headers`, `tags`
  - [x] `EmailResult` dataclass: `message_id`, `provider`, `status`, `error`
  - [x] `EmailError` base exception with subclasses: `ConfigurationError`, `DeliveryError`, `RateLimitError`, `InvalidRecipientError`

- [x] **settings.py - Email Configuration**
  - [x] `EmailSettings(BaseSettings)` with `EMAIL_*` env prefix
  - [x] `EMAIL_BACKEND`: console, smtp, resend, sendgrid, ses, postmark
  - [x] `EMAIL_FROM`: default sender address
  - [x] `EMAIL_REPLY_TO`: optional default reply-to
  - [x] Provider-specific settings (lazy-loaded based on backend)

- [x] **add.py - FastAPI Integration**
  - [x] `add_email(app, backend=None)` - add email to FastAPI app state
  - [x] `get_email() -> EmailBackend` - FastAPI dependency
  - [x] `health_check_email()` - health check probe
  - [x] Lifespan integration for async backends

- [x] **easy.py - Zero-Config Setup**
  - [x] `easy_email(backend=None, **kwargs)` - auto-detect from env
  - [x] Auto-detect provider from available env vars
  - [x] Sensible defaults (console in dev, warning in prod if not configured)

- [x] **__init__.py - Public API**
  - [x] Export: `add_email`, `easy_email`, `get_email`, `EmailBackend`, `EmailMessage`, `EmailResult`, `EmailSettings`, `EmailError`

**Bonus (completed early):**
- [x] `backends/__init__.py` - Backend module structure
- [x] `backends/console.py` - Console backend for development

---

### 0.2 Console & SMTP Backends

> Built-in backends that require no external dependencies.

**Files to create:**
- `src/svc_infra/email/backends/__init__.py`
- `src/svc_infra/email/backends/console.py`
- `src/svc_infra/email/backends/smtp.py`

- [x] **console.py - Development Backend**
  - [x] `ConsoleBackend` - prints emails to stdout/logger
  - [x] Pretty-print with sender, recipient, subject, truncated body
  - [x] Configurable log level
  - [x] Always returns success

- [x] **smtp.py - Standard SMTP Backend**
  - [x] `SMTPBackend` - async SMTP via `aiosmtplib`
  - [x] Settings: `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_USERNAME`, `EMAIL_SMTP_PASSWORD`, `EMAIL_SMTP_USE_TLS`
  - [x] Connection pooling for high-volume (via aiosmtplib)
  - [x] Sync fallback via `smtplib`
  - [x] StartTLS and SSL/TLS support

---

### 0.3 Modern Provider Backends

> Integration with modern transactional email providers.

**Files to create:**
- `src/svc_infra/email/backends/resend.py`
- `src/svc_infra/email/backends/sendgrid.py`
- `src/svc_infra/email/backends/ses.py`
- `src/svc_infra/email/backends/postmark.py`

- [x] **resend.py - Resend Backend**
  - [x] `ResendBackend` using httpx (no SDK dependency)
  - [x] Settings: `EMAIL_RESEND_API_KEY`
  - [x] Async HTTP via httpx
  - [x] Tag and metadata support
  - [x] Attachment support with base64 encoding

- [x] **sendgrid.py - SendGrid Backend**
  - [x] `SendGridBackend` using httpx (no SDK dependency)
  - [x] Settings: `EMAIL_SENDGRID_API_KEY`
  - [x] Dynamic template support via `send_template()`
  - [x] Category and custom args
  - [x] Sandbox mode for testing

- [x] **ses.py - AWS SES Backend**
  - [x] `SESBackend` using boto3/aioboto3
  - [x] Settings: `EMAIL_SES_REGION`, `EMAIL_SES_ACCESS_KEY`, `EMAIL_SES_SECRET_KEY`
  - [x] Falls back to default AWS credentials chain
  - [x] Configuration set support
  - [x] Raw MIME email support for attachments

- [x] **postmark.py - Postmark Backend**
  - [x] `PostmarkBackend` using httpx
  - [x] Settings: `EMAIL_POSTMARK_API_TOKEN`, `EMAIL_POSTMARK_MESSAGE_STREAM`
  - [x] Template support via `send_template()`
  - [x] Track opens/clicks configuration

---

### 0.4 Template System

> Built-in email templating with Jinja2.

**Files to create:**
- `src/svc_infra/email/templates/__init__.py`
- `src/svc_infra/email/templates/loader.py`
- `src/svc_infra/email/templates/base.html`

- [x] **loader.py - Template Engine**
  - [x] `EmailTemplateLoader` class
  - [x] Load templates from package resources or custom path
  - [x] `render(template_name, **context) -> tuple[str, str]` returns (html, text)
  - [x] Auto-generate text from HTML if not provided
  - [x] Base template with unsubscribe footer, branding

- [x] **Built-in Templates**
  - [x] `base.html` - responsive email base layout
  - [x] `verification.html` - email verification
  - [x] `password_reset.html` - password reset
  - [x] `invitation.html` - workspace/team invitation
  - [x] `welcome.html` - welcome email

---

### 0.5 High-Level Send API

> Unified send method that works across all backends.

**Files created:**
- `src/svc_infra/email/sender.py` - EmailSender class with high-level API

**Files updated:**
- `src/svc_infra/email/__init__.py` - exports EmailSender, easy_sender, add_sender, get_sender
- `src/svc_infra/email/easy.py` - added easy_sender() function
- `src/svc_infra/email/add.py` - added add_sender() and get_sender() for FastAPI

- [x] **Unified send() method**
  ```python
  async def send(
      to: str | list[str],
      subject: str,
      *,
      html: str | None = None,
      text: str | None = None,
      template: str | None = None,
      context: dict | None = None,
      from_addr: str | None = None,
      reply_to: str | None = None,
      cc: list[str] | None = None,
      bcc: list[str] | None = None,
      attachments: list[Attachment] | None = None,
      tags: list[str] | None = None,
      metadata: dict | None = None,
  ) -> EmailResult:
  ```
  - [x] Validate recipient addresses
  - [x] Load template if specified
  - [x] Fall back to settings for from_addr
  - [x] Return consistent `EmailResult`

- [x] **Convenience Methods**
  - [x] `send_verification(to, code, verification_url, user_name)` - uses verification template
  - [x] `send_password_reset(to, reset_url, user_name)` - uses password_reset template
  - [x] `send_invitation(to, invitation_url, inviter_name, workspace_name, role)` - uses invitation template
  - [x] `send_welcome(to, user_name, features)` - uses welcome template

---

### 0.6 Auth Module Migration

> Migrate existing auth sender to use new email infrastructure.

**Files updated:**
- `src/svc_infra/api/fastapi/auth/sender.py` - Now wraps new email module
- `tests/unit/api/fastapi/auth/test_sender_coverage.py` - Updated tests

**Note:** `users.py` and `mfa/router.py` require no changes - they use the same
`get_sender().send()` interface which is now backed by the new email infrastructure.

- [x] **Replace old sender.py**
  - [x] Update `sender.py` to use new `svc_infra.email` module via `_EmailSenderAdapter`
  - [x] Keep `Sender` protocol for backward compatibility
  - [x] Keep `SMTPSender` and `ConsoleSender` classes for legacy usage

- [x] **Update auth consumers**
  - [x] `users.py`: No changes needed - same interface
  - [x] `mfa/router.py`: No changes needed - same interface
  - [x] Support both `AUTH_SMTP_*` and `EMAIL_*` env vars via `_sync_auth_env_to_email_env()`

---

### 0.7 Testing & Documentation ✅

> Comprehensive tests and documentation.

**Files created:**
- `tests/unit/email/test_email_backends.py` ✅
- `tests/unit/email/test_email_templates.py` ✅
- `tests/unit/email/test_email_send.py` ✅
- `tests/unit/email/test_email_integration.py` ✅
- `docs/email.md` ✅

- [x] **Unit Tests**
  - [x] Test ConsoleBackend output format
  - [x] Test SMTPBackend connection and send
  - [x] Test each provider backend with mocked responses
  - [x] Test template rendering
  - [x] Test email validation
  - [x] Test error handling

- [x] **Integration Tests**
  - [x] Test `add_email()` FastAPI integration
  - [x] Test `get_email()` dependency injection
  - [x] Test health check endpoint

- [x] **Documentation**
  - [x] Quick start guide
  - [x] Provider configuration reference
  - [x] Template customization guide
  - [x] Migration guide from old sender

---

### 0.8 Examples ✅

> Working examples for common use cases.

**Files created:**
- `examples/email/basic_send.py` ✅
- `examples/email/with_templates.py` ✅
- `examples/email/fastapi_integration.py` ✅
- `examples/email/README.md` ✅

- [x] **basic_send.py** - Simple HTML email sending with auto-detection
- [x] **with_templates.py** - Template-based emails (verification, password reset, invitation, welcome)
- [x] **fastapi_integration.py** - Full FastAPI app with health check, auth endpoints, team invitations

---

### Phase 0 Success Criteria ✅

| Deliverable | Status |
|-------------|--------|
| `svc_infra.email` module created | [x] |
| Console + SMTP backends | [x] |
| Resend backend | [x] |
| SendGrid backend | [x] |
| AWS SES backend | [x] |
| Postmark backend | [x] |
| Template system | [x] |
| Unified `send()` API | [x] |
| Auth module migrated | [x] |
| Tests (>80% coverage for email module) | [x] |
| Documentation complete | [x] |
| Examples working | [x] |

---

### Environment Variables Reference

```bash
# Backend selection (auto-detected if not set)
EMAIL_BACKEND=resend  # console, smtp, resend, sendgrid, ses, postmark

# Common settings
EMAIL_FROM=noreply@example.com
EMAIL_REPLY_TO=support@example.com

# SMTP
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=user@gmail.com
EMAIL_SMTP_PASSWORD=app-password
EMAIL_SMTP_USE_TLS=true

# Resend
EMAIL_RESEND_API_KEY=re_xxxxx

# SendGrid
EMAIL_SENDGRID_API_KEY=SG.xxxxx

# AWS SES
EMAIL_SES_REGION=us-east-1
EMAIL_SES_ACCESS_KEY=AKIA...
EMAIL_SES_SECRET_KEY=xxxxx

# Postmark
EMAIL_POSTMARK_API_TOKEN=xxxxx
EMAIL_POSTMARK_MESSAGE_STREAM=outbound

# Templates
EMAIL_TEMPLATES_PATH=/app/templates/email  # Optional custom path
```

---

## Overview

This roadmap outlines the path from current state to v1.0.0 (production-ready release) and v2.0.0 (feature-complete platform). Each phase is designed to be independently shippable.

### Current State Summary

**Fully Implemented:**
- [OK] Auth (JWT, sessions, OAuth/OIDC, MFA, API keys, lockout)
- [OK] Database (PostgreSQL, MongoDB, migrations, repositories, multi-tenancy)
- [OK] Jobs (Redis/memory queue, retries, DLQ, scheduling)
- [OK] Cache (Redis/memory, decorators, namespacing)
- [OK] Webhooks (outbox pattern, HMAC signing, delivery retries)
- [OK] Billing (usage tracking, metering, invoices, subscriptions)
- [OK] Storage (S3, local, memory backends, signed URLs)
- [OK] Observability (Prometheus, OTEL, Grafana dashboards, health probes)
- [OK] Security (CORS, CSP, HIBP, lockout, rate limiting)
- [OK] Multi-tenancy (soft-tenant isolation, automatic scoping)
- [OK] Admin Operations (impersonation, role-gated routes)
- [OK] Resilience (retries, circuit breakers, timeouts)
- [OK] Idempotency (request deduplication)
- [OK] SDK Generation (TypeScript, Python, Postman)
- [OK] WebSocket (real-time, Redis pub/sub scaling)
- [OK] Data Lifecycle (backup, retention, GDPR erasure)

---

## Phase 2: Admin Dashboard UI

**Goal**: Provide a framework-agnostic admin dashboard for managing svc-infra resources.

### 2.1 Architecture Design

> Design an admin UI that works with FastAPI, Django, Litestar, and potentially standalone.

- [x] **Define admin dashboard scope**
 - [ ] User management (CRUD, search, sessions)
 - [ ] Tenant management (list, switch, usage)
 - [ ] Billing dashboard (usage graphs, invoices)
 - [ ] Job queue monitoring (pending, failed, DLQ)
 - [ ] Webhook delivery status (success rate, retries)
 - [ ] Cache management (stats, invalidation)
 - [ ] Health/metrics overview

- [x] **Choose UI approach**
 - [ ] Option A: Server-rendered (HTMX + Tailwind) - recommended
 - [ ] Option B: Standalone SPA (talks to API)
 - [ ] Option C: Embeddable components
 - [ ] Document decision in ADR

- [x] **Design API endpoints**
 - [ ] `GET /admin/api/users` - List users with pagination
 - [ ] `GET /admin/api/users/{id}` - User details
 - [ ] `GET /admin/api/tenants` - List tenants
 - [ ] `GET /admin/api/billing/usage` - Usage stats
 - [ ] `GET /admin/api/jobs/status` - Queue status
 - [ ] `GET /admin/api/webhooks/stats` - Delivery stats
 - [ ] `GET /admin/api/health` - Health overview

### 2.2 Create Admin Module Structure

> Build the `admin/` module following existing patterns.

- [x] **Create directory structure**
 ```
 src/svc_infra/admin/
 ├── __init__.py
 ├── add.py # add_admin_dashboard()
 ├── settings.py # AdminSettings
 ├── router.py # Admin API routes
 ├── templates/ # HTMX templates (if server-rendered)
 │ ├── base.html
 │ ├── dashboard.html
 │ ├── users/
 │ ├── tenants/
 │ ├── billing/
 │ ├── jobs/
 │ └── webhooks/
 ├── static/ # CSS, JS assets
 │ ├── admin.css
 │ └── htmx.min.js
 └── services/
 ├── user_service.py
 ├── tenant_service.py
 ├── billing_service.py
 ├── job_service.py
 └── webhook_service.py
 ```

- [x] **Create `admin/__init__.py`**
 - [ ] Export `add_admin_dashboard`
 - [ ] Export `AdminSettings`
 - [ ] Add module docstring

- [x] **Create `admin/settings.py`**
 - [ ] `ADMIN_ENABLED` - Enable/disable admin
 - [ ] `ADMIN_BASE_PATH` - Mount path (default: `/_admin`)
 - [ ] `ADMIN_REQUIRE_SUPERUSER` - Require superuser role
 - [ ] `ADMIN_THEME` - Light/dark theme
 - [ ] `ADMIN_LOGO_URL` - Custom logo
 - [ ] `ADMIN_TITLE` - Dashboard title

- [x] **Create `admin/add.py`**
 - [ ] Follow `add_*` pattern
 - [ ] Mount admin routes
 - [ ] Add static file serving
 - [ ] Register admin services

### 2.3 Implement Admin Services

> Create service layer for admin operations.

- [x] **Create `admin/services/user_service.py`**
 - [ ] `list_users(page, per_page, search)` - Paginated user list
 - [ ] `get_user(user_id)` - User details with sessions
 - [ ] `update_user(user_id, data)` - Update user fields
 - [ ] `delete_user(user_id)` - Soft delete
 - [ ] `list_sessions(user_id)` - Active sessions
 - [ ] `revoke_session(session_id)` - Revoke session

- [x] **Create `admin/services/tenant_service.py`**
 - [ ] `list_tenants(page, per_page, search)` - Tenant list
 - [ ] `get_tenant(tenant_id)` - Tenant details
 - [ ] `get_tenant_usage(tenant_id)` - Usage summary
 - [ ] `get_tenant_users(tenant_id)` - Users in tenant

- [x] **Create `admin/services/billing_service.py`**
 - [ ] `get_usage_summary(tenant_id, period)` - Usage stats
 - [ ] `list_invoices(tenant_id, page)` - Invoice list
 - [ ] `get_invoice(invoice_id)` - Invoice details
 - [ ] `get_subscription(tenant_id)` - Current plan

- [x] **Create `admin/services/job_service.py`**
 - [ ] `get_queue_status()` - Pending/processing/failed counts
 - [ ] `list_failed_jobs(page)` - Failed job list
 - [ ] `retry_job(job_id)` - Retry single job
 - [ ] `retry_all_failed()` - Retry all failed
 - [ ] `purge_dlq()` - Clear dead letter queue

- [x] **Create `admin/services/webhook_service.py`**
 - [ ] `get_delivery_stats()` - Success/failure rates
 - [ ] `list_subscriptions(tenant_id)` - Webhook subscriptions
 - [ ] `list_deliveries(subscription_id, status)` - Delivery log
 - [ ] `retry_delivery(delivery_id)` - Retry delivery

### 2.4 Implement Admin API Routes

> Create FastAPI routes for admin operations.

- [x] **Create `admin/router.py`**
 - [ ] Mount under `/_admin/api`
 - [ ] Apply admin role guard
 - [ ] Implement all endpoints from 1.1

- [x] **Add pagination support**
 - [ ] Use existing `svc_infra.api.fastapi.pagination` module
 - [ ] Consistent page/per_page/cursor pattern

- [x] **Add search support**
 - [ ] Filter parameters for list endpoints
 - [ ] Full-text search where applicable

### 2.5 Implement Admin UI (HTMX)

> Build server-rendered templates with HTMX for interactivity.

- [x] **Create base template**
 - [ ] Sidebar navigation
 - [ ] Header with user info
 - [ ] Dark/light mode toggle
 - [ ] Responsive layout

- [x] **Create dashboard page**
 - [ ] Quick stats (users, tenants, jobs, webhooks)
 - [ ] Recent activity feed
 - [ ] Health status indicators

- [x] **Create users pages**
 - [ ] User list with search/filter
 - [ ] User detail/edit form
 - [ ] Session management
 - [ ] Impersonation button

- [x] **Create tenants pages**
 - [ ] Tenant list
 - [ ] Tenant detail with usage
 - [ ] Switch tenant context

- [x] **Create billing pages**
 - [ ] Usage graphs (Chart.js or similar)
 - [ ] Invoice list
 - [ ] Subscription management

- [x] **Create jobs pages**
 - [ ] Queue status overview
 - [ ] Failed jobs list
 - [ ] Retry/purge actions
 - [ ] Job detail view

- [x] **Create webhooks pages**
 - [ ] Delivery stats dashboard
 - [ ] Subscription list
 - [ ] Delivery log viewer
 - [ ] Retry failed deliveries

### 2.6 Documentation and Tests

- [x] **Create `docs/admin-dashboard.md`**
 - [ ] Setup and configuration
 - [ ] Customization options
 - [ ] Extending with custom pages
 - [ ] Security considerations
 - [ ] Screenshots

- [x] **Add tests**
 - [ ] Unit tests for admin services
 - [ ] Integration tests for API routes
 - [ ] E2E tests for UI flows (optional)

---

## Phase 3: Framework Adapters

**Goal**: Enable svc-infra to work with Django, Litestar, and Flask in addition to FastAPI.

### 3.1 Abstraction Layer Design

> Create framework-agnostic core with framework-specific adapters.

- [x] **Identify framework-coupled code**
 - [ ] Audit all `add_*` functions
 - [ ] List FastAPI-specific imports
 - [ ] Document required abstractions

- [x] **Design adapter protocol**
 - [ ] `AppAdapter` protocol for lifecycle hooks
 - [ ] `RouterAdapter` protocol for route registration
 - [ ] `MiddlewareAdapter` protocol for middleware
 - [ ] `DependencyAdapter` protocol for DI

- [x] **Document adapter architecture**
 - [ ] Create ADR for framework adapters
 - [ ] Define interface contracts
 - [ ] Plan backward compatibility

### 3.2 Create Core Abstractions

> Move framework-agnostic code to core modules.

- [x] **Create `src/svc_infra/core/` module**
 ```
 src/svc_infra/core/
 ├── __init__.py
 ├── app.py # Abstract app interface
 ├── router.py # Abstract router interface
 ├── middleware.py # Abstract middleware interface
 ├── request.py # Abstract request interface
 └── response.py # Abstract response interface
 ```

- [x] **Define protocols**
 - [ ] `AppProtocol` - startup/shutdown, state, include_router
 - [ ] `RouterProtocol` - add route, middleware
 - [ ] `RequestProtocol` - headers, body, user, state
 - [ ] `ResponseProtocol` - status, headers, body

### 3.3 Implement Django Adapter

> Enable svc-infra modules to work with Django.

- [x] **Create `src/svc_infra/adapters/django/` module**
 ```
 src/svc_infra/adapters/django/
 ├── __init__.py
 ├── app.py # Django app adapter
 ├── views.py # View adapters
 ├── middleware.py # Middleware adapters
 ├── urls.py # URL patterns
 └── settings.py # Settings integration
 ```

- [x] **Wrap django-allauth for auth**
 - [ ] Map to svc-infra auth interface
 - [ ] JWT support via djangorestframework-simplejwt
 - [ ] MFA integration

- [x] **Wrap Django ORM for database**
 - [ ] Repository pattern adapter
 - [ ] Migration compatibility

- [x] **Wrap django-rq or Celery for jobs**
 - [ ] Map to JobQueue interface
 - [ ] Scheduler integration

- [x] **Create Django integration docs**

### 3.4 Implement Litestar Adapter

> Enable svc-infra modules to work with Litestar.

- [x] **Create `src/svc_infra/adapters/litestar/` module**
 ```
 src/svc_infra/adapters/litestar/
 ├── __init__.py
 ├── app.py # Litestar app adapter
 ├── routes.py # Route adapters
 ├── middleware.py # Middleware adapters
 └── dependencies.py # DI adapters
 ```

- [x] **Map existing patterns to Litestar**
 - [ ] `add_*` functions for Litestar
 - [ ] Dependency injection mapping
 - [ ] Middleware adaptation

- [x] **Create Litestar integration docs**

### 3.5 Implement Flask Adapter (Optional)

> Enable svc-infra modules to work with Flask.

- [x] **Create `src/svc_infra/adapters/flask/` module**
- [x] **Wrap Flask-Login for auth**
- [x] **Wrap Flask-SQLAlchemy for database**
- [x] **Wrap Flask-RQ for jobs**
- [x] **Create Flask integration docs**

### 3.6 Backward Compatibility

> Ensure FastAPI users are not affected.

- [x] **Keep `svc_infra.api.fastapi` as primary interface**
- [x] **Add framework detection utility**
- [x] **Update examples for multi-framework**
- [x] **Add migration guide for existing users**

---

## Phase 4: New Modules

**Goal**: Add commonly requested infrastructure modules.

### 4.1 Search Module

> Full-text search abstraction with multiple backends.

- [x] **Create `src/svc_infra/search/` module**
 ```
 src/svc_infra/search/
 ├── __init__.py
 ├── add.py # add_search()
 ├── settings.py # SearchSettings
 ├── backends/
 │ ├── __init__.py
 │ ├── base.py # SearchBackend protocol
 │ ├── postgres.py # PostgreSQL FTS
 │ ├── meilisearch.py # Meilisearch
 │ ├── typesense.py # Typesense
 │ └── memory.py # In-memory (testing)
 ├── index.py # SearchIndex class
 └── query.py # Query builder
 ```

- [x] **Define SearchBackend protocol**
 - [ ] `index(documents)` - Index documents
 - [ ] `search(query, filters, limit)` - Search
 - [ ] `delete(ids)` - Remove from index
 - [ ] `create_index(name, schema)` - Create index

- [x] **Implement PostgreSQL FTS backend**
 - [ ] Use `tsvector` and `tsquery`
 - [ ] GIN index creation
 - [ ] Ranking and highlighting

- [x] **Implement Meilisearch backend**
 - [ ] Wrap meilisearch-python
 - [ ] Index management
 - [ ] Faceted search

- [x] **Implement Typesense backend**
 - [ ] Wrap typesense-python
 - [ ] Collection management
 - [ ] Geo search support

- [x] **Create FastAPI integration**
 - [ ] `add_search(app)` function
 - [ ] Search dependency injection
 - [ ] Optional routes

- [x] **Create docs and tests**
 - [ ] `docs/search.md`
 - [ ] Unit tests for each backend
 - [ ] Integration tests

### 4.2 Feature Flags Module

> Feature flag management with multiple backends.

- [x] **Create `src/svc_infra/flags/` module**
 ```
 src/svc_infra/flags/
 ├── __init__.py
 ├── add.py # add_feature_flags()
 ├── settings.py # FlagSettings
 ├── backends/
 │ ├── __init__.py
 │ ├── base.py # FlagBackend protocol
 │ ├── memory.py # In-memory
 │ ├── database.py # Database-backed
 │ ├── unleash.py # Unleash integration
 │ └── launchdarkly.py # LaunchDarkly integration
 ├── models.py # Flag, Segment, Rule models
 ├── context.py # EvaluationContext
 └── decorators.py # @feature_flag decorator
 ```

- [x] **Define FlagBackend protocol**
 - [ ] `is_enabled(flag_name, context)` - Check flag
 - [ ] `get_variant(flag_name, context)` - Get variant
 - [ ] `list_flags()` - List all flags
 - [ ] `create_flag(flag)` - Create flag
 - [ ] `update_flag(flag)` - Update flag

- [x] **Implement database backend**
 - [ ] Flag model with rules
 - [ ] Segment targeting
 - [ ] Percentage rollouts

- [x] **Implement Unleash backend**
 - [ ] Wrap unleash-client-python
 - [ ] Strategy mapping

- [x] **Create decorator API**
 ```python
 @feature_flag("new_checkout", default=False)
 async def checkout(enabled: bool):
 if enabled:
 return new_checkout()
 return old_checkout()
 ```

- [x] **Create FastAPI integration**
 - [ ] `add_feature_flags(app)` function
 - [ ] Dependency injection
 - [ ] Admin routes for flag management

- [x] **Create docs and tests**
 - [ ] `docs/feature-flags.md`
 - [ ] Unit tests for backends
 - [ ] Integration tests

### 4.3 Email Module

> Transactional email with templates and multiple providers.

- [x] **Create `src/svc_infra/email/` module**
 ```
 src/svc_infra/email/
 ├── __init__.py
 ├── add.py # add_email()
 ├── settings.py # EmailSettings
 ├── providers/
 │ ├── __init__.py
 │ ├── base.py # EmailProvider protocol
 │ ├── smtp.py # SMTP (extend existing)
 │ ├── resend.py # Resend
 │ ├── sendgrid.py # SendGrid
 │ ├── ses.py # AWS SES
 │ └── console.py # Console (dev)
 ├── templates/
 │ ├── __init__.py
 │ └── loader.py # Template loading
 ├── models.py # Email, Attachment models
 └── service.py # EmailService
 ```

- [x] **Define EmailProvider protocol**
 - [ ] `send(email)` - Send single email
 - [ ] `send_batch(emails)` - Send batch
 - [ ] `get_status(message_id)` - Delivery status

- [x] **Implement providers**
 - [ ] Resend (recommended default)
 - [ ] SendGrid
 - [ ] AWS SES
 - [ ] SMTP (extend existing auth sender)

- [x] **Template support**
 - [ ] Jinja2 templates
 - [ ] MJML support (optional)
 - [ ] Inline CSS

- [x] **Create EmailService**
 - [ ] Queue integration for async sending
 - [ ] Retry logic for failures
 - [ ] Template rendering

- [x] **Create FastAPI integration**
 - [ ] `add_email(app)` function
 - [ ] Dependency injection

- [x] **Create docs and tests**
 - [ ] `docs/email.md`
 - [ ] Unit tests for providers
 - [ ] Integration tests

### 4.4 Notifications Module

> Multi-channel notifications (push, SMS, in-app, email).

- [x] **Create `src/svc_infra/notifications/` module**
 ```
 src/svc_infra/notifications/
 ├── __init__.py
 ├── add.py # add_notifications()
 ├── settings.py # NotificationSettings
 ├── channels/
 │ ├── __init__.py
 │ ├── base.py # Channel protocol
 │ ├── email.py # Uses email module
 │ ├── sms.py # Twilio/Vonage
 │ ├── push.py # FCM/APNs
 │ └── inapp.py # In-app (WebSocket/database)
 ├── models.py # Notification, Preference models
 ├── service.py # NotificationService
 └── router.py # Preference API routes
 ```

- [x] **Define Channel protocol**
 - [ ] `send(user, notification)` - Send notification
 - [ ] `supports_batch` - Batch capability

- [x] **Implement channels**
 - [ ] Email (uses email module)
 - [ ] SMS (Twilio)
 - [ ] Push (FCM for Android/web, APNs for iOS)
 - [ ] In-app (WebSocket or polling)

- [x] **Create preference management**
 - [ ] User notification preferences
 - [ ] Channel opt-in/opt-out
 - [ ] Quiet hours

- [x] **Create FastAPI integration**
 - [ ] `add_notifications(app)` function
 - [ ] Preference API routes
 - [ ] WebSocket for in-app

- [x] **Create docs and tests**
 - [ ] `docs/notifications.md`
 - [ ] Unit tests for channels
 - [ ] Integration tests

---

## Phase 5: Enterprise Features

**Goal**: Add enterprise-grade features for larger customers.

### 5.1 SAML/SSO Support

> Enterprise single sign-on via SAML 2.0.

- [x] **Create `src/svc_infra/enterprise/sso/` module**
 ```
 src/svc_infra/enterprise/sso/
 ├── __init__.py
 ├── add.py # add_saml_sso()
 ├── settings.py # SAMLSettings
 ├── providers/
 │ ├── __init__.py
 │ ├── base.py # SSOProvider protocol
 │ ├── saml.py # SAML 2.0 (python-saml)
 │ └── oidc.py # OIDC enterprise (extend existing)
 ├── models.py # SSOConfig, SSOConnection
 ├── router.py # SAML endpoints
 └── service.py # SSOService
 ```

- [x] **Implement SAML 2.0**
 - [ ] Wrap python3-saml
 - [ ] SP-initiated SSO
 - [ ] IdP-initiated SSO
 - [ ] Metadata exchange

- [x] **Per-tenant SSO configuration**
 - [ ] SSOConnection model
 - [ ] Admin UI for SSO setup
 - [ ] Certificate management

- [x] **Create docs and tests**
 - [ ] `docs/enterprise-sso.md`
 - [ ] Integration tests with mock IdP

### 5.2 SCIM Provisioning

> Automatic user provisioning via SCIM 2.0.

- [x] **Create `src/svc_infra/enterprise/scim/` module**
 ```
 src/svc_infra/enterprise/scim/
 ├── __init__.py
 ├── add.py # add_scim()
 ├── settings.py # SCIMSettings
 ├── router.py # SCIM endpoints
 ├── models.py # SCIMUser, SCIMGroup schemas
 └── service.py # SCIMService
 ```

- [x] **Implement SCIM 2.0 endpoints**
 - [ ] `/scim/v2/Users` - User CRUD
 - [ ] `/scim/v2/Groups` - Group CRUD
 - [ ] `/scim/v2/ServiceProviderConfig` - Config
 - [ ] `/scim/v2/Schemas` - Schema discovery

- [x] **Integration with auth module**
 - [ ] Auto-create users from SCIM
 - [ ] Sync groups/roles
 - [ ] Deprovisioning

- [x] **Create docs and tests**
 - [ ] `docs/enterprise-scim.md`
 - [ ] Compliance tests

### 5.3 Advanced Audit Logging

> Tamper-proof audit trail with compliance features.

- [x] **Enhance `src/svc_infra/security/audit_service.py`**
 - [ ] Hash chain integrity
 - [ ] Log export (JSON, CSV)
 - [ ] Retention policies
 - [ ] Search/filter

- [x] **Add compliance features**
 - [ ] SOC 2 event types
 - [ ] HIPAA audit requirements
 - [ ] PCI-DSS logging

- [x] **Create admin UI integration**
 - [ ] Audit log viewer
 - [ ] Export functionality
 - [ ] Integrity verification

- [x] **Create `docs/enterprise-audit.md`**

### 5.4 IP Allowlisting

> Per-tenant IP restriction.

- [x] **Create `src/svc_infra/enterprise/ip_allowlist/` module**
 - [ ] IPAllowlist model
 - [ ] Middleware for enforcement
 - [ ] Admin API for management

- [x] **Integration with tenancy**
 - [ ] Per-tenant allowlists
 - [ ] Global allowlists
 - [ ] Override for admins

- [x] **Create docs and tests**

### 5.5 Data Residency

> GDPR/compliance data location controls.

- [x] **Create `src/svc_infra/enterprise/residency/` module**
 - [ ] Region configuration
 - [ ] Per-tenant region assignment
 - [ ] Database routing based on region

- [x] **Integration with database module**
 - [ ] Multi-database routing
 - [ ] Region-aware queries

- [x] **Create docs**
 - [ ] `docs/enterprise-residency.md`
 - [ ] Compliance documentation

---

## Phase 6: v2.0.0 Release

**Goal**: Finalize, document, and release v2.0.0.

### 6.1 Final Integration

- [x] **Verify all new modules integrate cleanly**
- [x] **Update main `__init__.py` exports**
- [x] **Cross-module testing**

### 6.2 Documentation Polish

- [x] **Update README.md with new features**
- [x] **Create migration guide v1->v2**
- [x] **Update all examples**
- [x] **Create video tutorials (optional)**

### 6.3 Performance Optimization

- [x] **Profile critical paths**
- [x] **Optimize database queries**
- [x] **Cache frequently accessed data**

### 6.4 Release

- [x] **Update CHANGELOG.md**
- [x] **Update pyproject.toml to 2.0.0**
- [x] **Tag and publish**
- [x] **Announce release**

---

## Appendix: Module Structure Reference

### Standard Module Pattern

Every new module should follow this pattern:

```
src/svc_infra/{module}/
├── __init__.py # Exports with __all__, module docstring
├── add.py # add_{module}(app) for FastAPI integration
├── settings.py # {Module}Settings with env var support
├── service.py # Main service class (async preferred)
├── models.py # SQLAlchemy/Pydantic models
├── router.py # FastAPI router (if has endpoints)
├── backends/ # Backend implementations (if multi-backend)
│ ├── __init__.py
│ ├── base.py # Backend protocol
│ └── {backend}.py # Specific implementations
└── exceptions.py # Module-specific exceptions
```

### Standard Test Pattern

```
tests/unit/{module}/
├── test_{module}.py # Main module tests
├── test_{module}_service.py # Service tests
├── test_{module}_backends.py # Backend tests (if applicable)
└── conftest.py # Module fixtures

tests/integration/{module}/
└── test_{module}_integration.py # Integration with real services
```

### Standard Documentation Pattern

```
docs/{module}.md
├── Quick Start
├── Configuration (Environment Variables)
├── API Reference
├── Examples
├── Backends (if applicable)
└── Troubleshooting
```
