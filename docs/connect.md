# Connect

`svc_infra.connect` provides OAuth 2.0 + PKCE token acquisition, storage, and background refresh for third-party service connections. It ships with a catalog of 60+ pre-configured providers and supports any provider via environment variables — no code changes required. Configuration comes from environment variables read at startup via `ConnectSettings`.

The same provider registry also powers user login in `svc_infra.auth`. Set one set of credentials; both systems use them. See [Auth](auth.md) for the login side.

## Quick start

```python
from fastapi import FastAPI
from svc_infra.app import add_sql_db
from svc_infra.connect import add_connect

app = FastAPI()
add_sql_db(app)
add_connect(app)          # mounts /connect/authorize, /connect/callback/{provider}, /connect/token/{id}
```

Set the following environment variable before starting:

```
CONNECT_TOKEN_ENCRYPTION_KEY=<fernet-key>  # generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CONNECT_TOKEN_ENCRYPTION_KEY` | Yes | — | Fernet key used to encrypt tokens at rest |
| `CONNECT_API_BASE` | No | `""` | Public base URL of this API (used to build callback URLs) |
| `CONNECT_DEFAULT_REDIRECT_URI` | No | `""` | URI the browser is sent to after OAuth completes |
| `CONNECT_STATE_TTL_SECONDS` | No | `600` | Lifetime of OAuthState rows in seconds |
| `CONNECT_REDIRECT_ALLOW_HOSTS` | No | `""` | Comma-separated allowed redirect hosts |

Provider-specific credentials are read per-provider (see [Providers](#providers)).

## Endpoints

### `GET /connect/authorize`

Initiates an OAuth flow. Returns `{"authorize_url": "..."}`. The client opens this URL in a browser.

| Parameter | Required | Description |
|---|---|---|
| `connection_id` | Yes | UUID identifying this connection in your data model |
| `provider` | No* | Static provider name (e.g. `github`) |
| `mcp_server_url` | No* | MCP server URL for dynamic OAuth discovery (RFC 9728) |
| `redirect_uri` | No | Override the post-OAuth redirect URI |
| `scopes` | No | Space-separated scope override |

*One of `provider` or `mcp_server_url` is required.

### `GET /connect/callback/{provider}`

OAuth redirect target. Validates PKCE state, exchanges code for tokens, stores them encrypted, then redirects the user to `redirect_uri?success=true&connection_id=<id>`. On error, redirects to `redirect_uri?error=<reason>`.

### `GET /connect/token/{connection_id}`

Returns a valid access token for the given connection. Automatically refreshes the token if it is within 5 minutes of expiry.

| Parameter | Required | Description |
|---|---|---|
| `provider` | Yes | Provider name |

Response: `{"token": "<access_token>", "expires_at": "<iso8601 or null>"}`.

Status codes: `200 OK`, `404 Not Found` (no token stored), `502 Bad Gateway` (refresh failed).

## Providers

### Built-in catalog

60+ providers ship pre-configured with correct URLs, scopes, and PKCE settings. To activate any of them, set credentials — no other configuration is needed.

All providers use the unified `CONNECT_{NAME}_*` env var pattern. Legacy names (e.g. `GITHUB_CLIENT_ID`) continue to work as fallbacks.

| Category | Providers |
|---|---|
| Identity / Login | `github`, `google`, `microsoft`, `linkedin`, `apple`, `discord`, `twitter`, `twitch`, `spotify`, `reddit`, `gitlab`, `bitbucket`, `facebook`, `salesforce`, `zoom` |
| Enterprise OIDC | `okta`, `auth0`, `keycloak`, `cognito` |
| Productivity | `notion`, `airtable`, `asana`, `monday`, `figma`, `clickup`, `todoist`, `miro`, `wrike`, `smartsheet`, `basecamp` |
| Dev tools | `vercel`, `netlify`, `render`, `atlassian`, `linear` |
| Communication | `slack`, `intercom` |
| CRM | `hubspot`, `pipedrive`, `zendesk`, `freshdesk` |
| Finance | `stripe`, `quickbooks`, `xero`, `freshbooks` |
| Calendar | `calendly` |
| Storage / Other | `dropbox`, `box`, `instagram`, `mailchimp`, `shopify` |

#### Standard credential env vars

```bash
CONNECT_GITHUB_CLIENT_ID=xxx
CONNECT_GITHUB_CLIENT_SECRET=yyy
```

Providers whose credentials are not set are silently skipped.

#### Per-provider overrides

| Variable | Description |
|---|---|
| `CONNECT_{NAME}_PKCE_REQUIRED` | `true`/`false` — override the catalog default |
| `CONNECT_{NAME}_SCOPES` | Space-separated scope override |
| `CONNECT_{NAME}_AUTHORIZE_URL` | Override the authorize endpoint |
| `CONNECT_{NAME}_TOKEN_URL` | Override the token endpoint |
| `CONNECT_{NAME}_LOGIN_ENABLED` | `true` — also expose this provider for user login via `svc_infra.auth` |

#### Dynamic-domain providers

Some enterprise providers require a tenant or subdomain. Pass it via `CONNECT_{NAME}_DOMAIN` (or provider-specific variable):

```bash
# Okta
CONNECT_OKTA_CLIENT_ID=xxx
CONNECT_OKTA_CLIENT_SECRET=yyy
CONNECT_OKTA_DOMAIN=mycompany.okta.com

# Auth0
CONNECT_AUTH0_CLIENT_ID=xxx
CONNECT_AUTH0_CLIENT_SECRET=yyy
CONNECT_AUTH0_DOMAIN=mycompany.auth0.com

# Shopify (per-shop)
CONNECT_SHOPIFY_CLIENT_ID=xxx
CONNECT_SHOPIFY_CLIENT_SECRET=yyy
CONNECT_SHOPIFY_DOMAIN=myshop.myshopify.com

# Zendesk / Freshdesk / Keycloak / Cognito follow the same pattern
```

### Adding an arbitrary provider

Any provider not in the catalog can be added entirely via environment variables:

```bash
CONNECT_PROVIDERS=acme                              # comma-separated list of names to activate
CONNECT_ACME_CLIENT_ID=xxx
CONNECT_ACME_CLIENT_SECRET=yyy
CONNECT_ACME_AUTHORIZE_URL=https://acme.com/oauth/authorize
CONNECT_ACME_TOKEN_URL=https://acme.com/oauth/token
CONNECT_ACME_SCOPES=read write
```

### Registering programmatically

For cases where credentials are not available as env vars at startup:

```python
from svc_infra.connect import registry, OAuthProvider

registry.register(OAuthProvider(
    name="my-service",
    client_id="...",
    client_secret="...",
    authorize_url="https://my-service.com/oauth/authorize",
    token_url="https://my-service.com/oauth/token",
    default_scopes=["read"],
))
```

## Token storage

Tokens are stored in the `connection_tokens` table. `access_token`, `refresh_token`, and `raw_token` are Fernet-encrypted before writing. The encryption key is read from `CONNECT_TOKEN_ENCRYPTION_KEY` at startup and never logged.

Access the `ConnectionTokenManager` programmatically:

```python
from svc_infra.connect.state import get_connect_token_manager

manager = get_connect_token_manager()
token = await manager.get_valid_token(db, connection_id=..., user_id=..., provider="github")
```

## Background jobs

`add_connect()` registers two background tasks via `InMemoryScheduler`:

| Task | Interval | Action |
|---|---|---|
| `connect:refresh_tokens` | 300 s | Refresh all tokens expiring within the next 10 minutes |
| `connect:cleanup_states` | 600 s | Delete expired `OAuthState` rows |

## Database migrations

Add the connect models to your Alembic environment by importing the discover function:

```python
# env.py (Alembic)
from svc_infra.connect.alembic import discover_packages
for package in discover_packages():
    importlib.import_module(package)
```

## Security

- All tokens are encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256).
- PKCE (S256) is enforced for all providers by default.
- HTTPS is required for redirect URIs unless the host is `localhost` or a custom scheme.
- `redirect_uri` host is validated against `CONNECT_REDIRECT_ALLOW_HOSTS`.
- OAuth state parameters expire after `CONNECT_STATE_TTL_SECONDS` seconds.

See [Security](security.md) for the full security model.
