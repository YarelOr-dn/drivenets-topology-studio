"""
TP Agent MCP Server -- combined MCP (SSE) + FastAPI HTTP server.

Runs on port 9100 with:
- /sse + /messages/  -> MCP SSE endpoint for Cursor agent
- /api               -> FastAPI HTTP endpoints for Streamlit GUI
"""

import json
import logging
import sys

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tp-agent-mcp")

MCP_AVAILABLE = False
try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    logger.warning("mcp package not installed -- MCP SSE disabled, HTTP-only mode")

from .mcp_tools import get_tool_definitions, handle_tool_call
from .http_api import app as fastapi_app


mcp_server = None
sse_transport = None

if MCP_AVAILABLE:
    mcp_server = Server("tp-agent-mcp")
    sse_transport = SseServerTransport("/messages/")

    @mcp_server.list_tools()
    async def list_tools():
        definitions = get_tool_definitions()
        return [
            Tool(
                name=d["name"],
                description=d["description"],
                inputSchema=d["inputSchema"],
            )
            for d in definitions
        ]

    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict):
        logger.info(f"MCP tool call: {name}({json.dumps(arguments)[:200]})")
        try:
            result = handle_tool_call(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"MCP tool error: {name}: {e}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def handle_sse(request: Request):
    """SSE endpoint -- clients GET this to establish the event stream."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )
    return Response()


async def health(request: Request):
    return JSONResponse({
        "status": "ok",
        "service": "tp-agent-mcp",
        "mcp_enabled": MCP_AVAILABLE,
        "endpoints": {
            "http_api": "/api",
            "mcp_sse": "/sse" if MCP_AVAILABLE else "disabled",
        },
    })


def create_app() -> Starlette:
    """Create the combined Starlette application."""
    routes = [
        Route("/health", health, methods=["GET"]),
        Mount("/api", app=fastapi_app),
    ]

    if MCP_AVAILABLE:
        routes.insert(0, Route("/sse", endpoint=handle_sse, methods=["GET"]))
        routes.insert(1, Mount("/messages/", app=sse_transport.handle_post_message))

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]

    async def on_startup():
        logger.info("TP Agent MCP server starting on port 9200")
        logger.info("  HTTP API: http://localhost:9200/api/health")
        if MCP_AVAILABLE:
            logger.info("  MCP SSE:  http://localhost:9200/sse")
        else:
            logger.info("  MCP SSE:  DISABLED (install 'mcp' package)")

    return Starlette(
        routes=routes,
        middleware=middleware,
        on_startup=[on_startup],
    )


app = create_app()


def main():
    uvicorn.run(
        "tp_agent_mcp.server:app",
        host="0.0.0.0",
        port=9200,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
