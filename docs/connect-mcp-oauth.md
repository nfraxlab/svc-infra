# Connect: MCP OAuth

`svc_infra.connect` supports automatic OAuth discovery for Model Context Protocol (MCP) servers that implement the OAuth Authorization Framework ([RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728) + [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414)). When a client passes `mcp_server_url` to the `/connect/authorize` endpoint, the server dynamically discovers the OAuth provider metadata and proceeds with a standard PKCE flow.

## How it works

1. The client sends `GET /connect/authorize?mcp_server_url=https://mcp.example.com&connection_id=<id>`.
2. `MCPOAuthDiscovery.discover()` probes `https://mcp.example.com/.well-known/oauth-protected-resource` (RFC 9728) to obtain `authorization_servers`.
3. The first authorization server URL is used to fetch `/.well-known/oauth-authorization-server` (RFC 8414) which provides `authorization_endpoint` and `token_endpoint`.
4. An `OAuthProvider` is constructed from the discovered metadata and registered in the global `registry` under `mcp:<url>`.
5. The standard PKCE authorize → callback → token flow proceeds identically to named providers.

The di covered provider is cached in-process for 1 hour to avoid repeated discovery calls.

## Detecting MCP OAuth support

```python
from svc_infra.connect import MCPOAuthDiscovery, MCPOAuthNotSupported

discovery = MCPOAuthDiscovery()

if await discovery.is_mcp_oauth_supported("https://mcp.example.com"):
    provider = await discovery.discover("https://mcp.example.com")
    print(provider.authorize_url)
```

`is_mcp_oauth_supported()` sends a lightweight `POST` probe and inspects the `WWW-Authenticate` response header. It never raises — it returns `False` on network errors or unsupported servers.

`discover()` raises `MCPOAuthNotSupported` when:
- The server does not expose RFC 9728 resource metadata
- The `authorization_servers` field is absent
- The authorization server metadata is unreachable or malformed
- `authorization_endpoint` or `token_endpoint` are missing

## Access token injection

After token acquisition the access token is available via `/connect/token/{connection_id}`. Callers inject it into the `Authorization: Bearer` header of their MCP connections. The `ai_infra.mcp.client.MCPClient` picks this up transparently through the standard Bearer path — this module only acquires and refreshes the token; MCP protocol internals remain in ai-infra.

## Example

```python
from fastapi import FastAPI
from svc_infra.connect import add_connect

app = FastAPI()
add_connect(app)
```

Client flow (pseudo-code):

```
# 1. Start the flow
POST /connect/authorize?mcp_server_url=https://mcp.example.com&connection_id=<uuid>
→ {"authorize_url": "https://auth.example.com/authorize?..."}

# 2. Browser follows authorize_url, completes login, provider redirects to:
GET /connect/callback/mcp:https://mcp.example.com?code=...&state=...
→ 302 → your-app://done?success=true&connection_id=<uuid>

# 3. Retrieve the token for MCP calls
GET /connect/token/<uuid>?provider=mcp:https://mcp.example.com
→ {"token": "<access_token>", "expires_at": "..."}
```

## Discovery caching

Results are cached in-process using a plain `dict`. Clear the cache in tests by importing and clearing `_DISCOVERY_CACHE`:

```python
from svc_infra.connect import mcp_discovery as _mod
_mod._DISCOVERY_CACHE.clear()
```

## Unsupported servers

When `MCPOAuthNotSupported` is raised, callers should fall back to a manual token input UI and store the token directly via `ConnectionTokenManager.store()`.
