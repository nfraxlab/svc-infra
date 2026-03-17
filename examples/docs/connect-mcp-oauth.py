"""MCP OAuth discovery example using svc_infra.connect.

Demonstrates how to detect whether an MCP server supports OAuth, trigger
dynamic provider discovery, and retrieve the resulting access token for use
in MCP client connections.

The acquired token should be passed to ai_infra.mcp.client.MCPClient via the
Authorization header — ai-infra picks it up through the standard Bearer path.

Required environment variables:
    CONNECT_TOKEN_ENCRYPTION_KEY
    CONNECT_API_BASE
    CONNECT_DEFAULT_REDIRECT_URI
"""

from __future__ import annotations

import asyncio

from svc_infra.connect import MCPOAuthDiscovery, MCPOAuthNotSupported


async def main() -> None:
    mcp_server_url = "https://your-mcp-server.example.com"
    discovery = MCPOAuthDiscovery()

    # Lightweight probe: check before attempting full discovery
    supported = await discovery.is_mcp_oauth_supported(mcp_server_url)
    if not supported:
        print("This MCP server does not support OAuth. Use manual token input instead.")
        return

    try:
        provider = await discovery.discover(mcp_server_url)
    except MCPOAuthNotSupported as exc:
        print(f"Discovery failed: {exc}")
        return

    print(f"Discovered provider: {provider.name}")
    print(f"  authorize_url: {provider.authorize_url}")
    print(f"  token_url:     {provider.token_url}")
    print()
    print("Initiate the OAuth flow via the connect API:")
    print(f"  GET /connect/authorize?mcp_server_url={mcp_server_url}&connection_id=<uuid>")
    print('  → returns {"authorize_url": "..."}')
    print()
    print("After the user completes login, retrieve the token:")
    print(f"  GET /connect/token/<connection_id>?provider={provider.name}")


if __name__ == "__main__":
    asyncio.run(main())
