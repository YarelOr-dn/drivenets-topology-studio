"""Authentication helpers for the shared Topology MCP endpoint."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

from starlette.responses import JSONResponse

from api.auth.service import decode_token
from api.auth.user_store import user_store


current_mcp_user: ContextVar[str] = ContextVar("current_mcp_user", default="")


def bearer_from_headers(headers) -> str:
    auth = headers.get("authorization") or headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return ""
    return auth.split(" ", 1)[1].strip()


def resolve_bearer_token(token: str) -> Optional[str]:
    """Resolve either a normal app JWT or a Cursor-MCP token to a username."""
    raw = (token or "").strip()
    if not raw:
        return None
    payload = decode_token(raw)
    if payload and payload.get("sub"):
        username = str(payload["sub"])
        return username if user_store.get_user(username) else None
    return user_store.validate_cursor_token(raw)


def current_username() -> str:
    username = current_mcp_user.get("")
    if not username:
        raise PermissionError("Authentication required")
    return username


class TopologyMcpAuthMiddleware:
    """Require a valid bearer token before the MCP server sees the request.

    This is deliberately plain ASGI middleware, not BaseHTTPMiddleware.
    Starlette's BaseHTTPMiddleware can corrupt streaming/mounted ASGI response
    sequencing for MCP SSE and trigger "Unexpected http.response.start" crashes.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        if scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        token = bearer_from_headers(headers)
        username = resolve_bearer_token(token)
        if not username:
            response = JSONResponse(
                {"error": "Authentication required"},
                status_code=401,
            )
            await response(scope, receive, send)
            return
        marker = current_mcp_user.set(username)
        try:
            await self.app(scope, receive, send)
        finally:
            current_mcp_user.reset(marker)

