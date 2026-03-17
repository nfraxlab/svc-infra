# Auth settings

`svc_infra.api.fastapi.auth` wraps FastAPI Users with sensible defaults for sessions, OAuth, MFA, and API keys via `add_auth_users`. Configuration comes from `AuthSettings`, which reads environment variables with the `AUTH_` prefix. 【F:src/svc_infra/api/fastapi/auth/add.py†L240-L321】【F:src/svc_infra/api/fastapi/auth/settings.py†L23-L91】

### Key environment variables

- `AUTH_JWT__SECRET`, `AUTH_JWT__OLD_SECRETS` – rotate signing keys without downtime. 【F:docs/security.md†L63-L70】
- `AUTH_SMTP_HOST`, `AUTH_SMTP_USERNAME`, `AUTH_SMTP_PASSWORD`, `AUTH_SMTP_FROM` – enable SMTP delivery; required in production. 【F:src/svc_infra/api/fastapi/auth/settings.py†L44-L60】【F:src/svc_infra/api/fastapi/auth/sender.py†L33-L59】
- `AUTH_SESSION_COOKIE_SECURE`, `AUTH_SESSION_COOKIE_NAME`, `AUTH_SESSION_COOKIE_SAMESITE` – shape session middleware. 【F:src/svc_infra/api/fastapi/auth/settings.py†L65-L88】【F:src/svc_infra/api/fastapi/auth/add.py†L279-L303】
- `AUTH_PASSWORD_MIN_LENGTH`, `AUTH_PASSWORD_REQUIRE_SYMBOL`, `AUTH_PASSWORD_BREACH_CHECK` – enforce password policy. 【F:docs/security.md†L24-L35】
- `AUTH_MFA_DEFAULT_ENABLED_FOR_NEW_USERS`, `AUTH_MFA_ENFORCE_FOR_ALL_USERS` – adjust MFA enforcement. 【F:src/svc_infra/api/fastapi/auth/settings.py†L32-L40】

## OAuth login

OAuth login providers are driven by the connect registry — the same catalog that powers workspace token connections. There is one set of credentials per provider; both systems share them.

### Enabling a provider for login

Set credentials and flip the login flag:

```bash
CONNECT_GITHUB_CLIENT_ID=xxx
CONNECT_GITHUB_CLIENT_SECRET=yyy
CONNECT_GITHUB_LOGIN_ENABLED=true
```

Any provider in the [connect catalog](connect.md#built-in-catalog) (60+ entries) can be enabled this way, including enterprise OIDC providers (Okta, Auth0, Keycloak, Cognito) and generic OAuth2 providers (Figma, Notion, Calendly, etc.).

### Dynamic-domain providers

For providers that require a tenant or domain, also set `CONNECT_{NAME}_DOMAIN`:

```bash
CONNECT_OKTA_CLIENT_ID=xxx
CONNECT_OKTA_CLIENT_SECRET=yyy
CONNECT_OKTA_DOMAIN=mycompany.okta.com
CONNECT_OKTA_LOGIN_ENABLED=true
```

### Legacy env vars

Existing deployments using the older `AUTH_*` naming continue to work without changes:

| Legacy variable | Equivalent connect variable |
|---|---|
| `AUTH_GITHUB_CLIENT_ID` | `CONNECT_GITHUB_CLIENT_ID` |
| `AUTH_GITHUB_CLIENT_SECRET` | `CONNECT_GITHUB_CLIENT_SECRET` |
| `AUTH_GOOGLE_CLIENT_ID` | `CONNECT_GOOGLE_CLIENT_ID` |
| `AUTH_GOOGLE_CLIENT_SECRET` | `CONNECT_GOOGLE_CLIENT_SECRET` |
| `AUTH_MS_CLIENT_ID` | `CONNECT_MICROSOFT_CLIENT_ID` |
| `AUTH_MS_CLIENT_SECRET` | `CONNECT_MICROSOFT_CLIENT_SECRET` |

The `CONNECT_*` variables take precedence when both are set.

### OIDC providers

Providers with an OIDC discovery URL (Google, Okta, Auth0, Keycloak, Cognito, Apple) use the OIDC flow automatically — no additional configuration is required. For standard OAuth2 providers, the `userinfo` endpoint is called to retrieve the user's identity after token exchange.

### Adding a completely custom login provider

Use `CONNECT_PROVIDERS` to register any provider and then enable it for login:

```bash
CONNECT_PROVIDERS=acme
CONNECT_ACME_CLIENT_ID=xxx
CONNECT_ACME_CLIENT_SECRET=yyy
CONNECT_ACME_AUTHORIZE_URL=https://acme.com/oauth/authorize
CONNECT_ACME_TOKEN_URL=https://acme.com/oauth/token
CONNECT_ACME_USERINFO_URL=https://acme.com/api/me
CONNECT_ACME_SCOPES=openid email profile
CONNECT_ACME_LOGIN_ENABLED=true
```

See [Connect](connect.md) for the full provider catalog and configuration reference.
