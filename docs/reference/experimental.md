# Experimental APIs

This page lists APIs that are considered experimental. Experimental APIs may change, be renamed, or be removed in minor versions without following the normal deprecation policy.

## What Does "Experimental" Mean?

Experimental APIs are:
- **Functional** and can be used in production at your own risk
- **Subject to change** without the standard 2-version deprecation period
- **Not yet battle-tested** in large-scale production environments
- **Seeking feedback** from early adopters

## Current Experimental APIs

### Object Router

**Status**: Experimental (since v0.1.700)

The Object Router pattern enables automatic REST API generation from Python objects using the robo-infra tool extraction pattern.

```python
from svc_infra.api.fastapi import create_object_router

class MyService:
    def list_items(self) -> list[Item]:
        ...
    def get_item(self, id: str) -> Item:
        ...

router = create_object_router(MyService(), prefix="/items")
app.include_router(router)
```

**Why experimental**:
- Pattern extracted from robo-infra, still being generalized
- Method-to-route mapping conventions may evolve
- Authentication integration patterns being refined

**Exports**:
- `create_object_router`
- `ObjectRouterConfig`
- `route_method`
- `exclude_method`

### WebSocket Utilities

**Status**: Experimental (since v0.1.680)

WebSocket connection management and broadcasting utilities.

```python
from svc_infra.websocket import ConnectionManager

manager = ConnectionManager()
await manager.connect(websocket)
await manager.broadcast({"event": "update"})
```

**Why experimental**:
- Scaling patterns for multi-node deployments need validation
- Redis pub/sub integration is new
- Reconnection handling strategies evolving

**Exports**:
- `ConnectionManager`
- `WebSocketMessage`

### MCP Server Integration

**Status**: Experimental (since v0.1.690)

Integration with Model Context Protocol for AI agent tool serving.

**Why experimental**:
- MCP specification is still evolving
- Transport layer options (stdio, HTTP, SSE) being finalized
- Security model for tool execution needs hardening

## Stability Tiers

| Tier | Meaning | Deprecation Policy |
|------|---------|-------------------|
| **Stable** | Production-ready, fully tested | 2+ minor versions notice |
| **Experimental** | Functional but may change | May change in any release |
| **Internal** | Not exported, implementation detail | No guarantees |

## Stable APIs

The following are considered stable:

- **Security**: `add_security`, `SecurityHeadersMiddleware`, lockout, passwords
- **Database**: All `db` module utilities
- **Caching**: `cache` decorators and backends
- **Jobs**: Background job queues
- **Webhooks**: Webhook signing and delivery
- **Health**: Health check endpoints

## Providing Feedback

If you're using experimental APIs, we want to hear from you:

- GitHub Issues: Report bugs or suggest improvements
- Discussions: Share use cases and patterns that work well
