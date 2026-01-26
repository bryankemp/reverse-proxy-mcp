"""MCP server entry point.

Runs the MCP server with HTTP/SSE transport on port 5000.
"""

import logging
from typing import Any

import uvicorn
from fastapi import FastAPI, Request

from reverse_proxy_mcp.core import settings
from reverse_proxy_mcp.mcp.server import MCPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mcp_app() -> FastAPI:
    """Create FastAPI app for MCP server with HTTP transport."""
    app = FastAPI(
        title="Nginx Manager MCP",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # Initialize MCP server
    mcp_server = MCPServer(api_url=settings.api_url)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        """MCP server health check."""
        return mcp_server.get_health_status()

    @app.post("/mcp")
    async def mcp_request(request: Request) -> dict[str, Any]:
        """Handle MCP JSON-RPC requests."""
        try:
            data = await request.json()
            result = await mcp_server.handle_request(data)
            return result
        except Exception as e:
            logger.error(f"Error in MCP request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
            }

    @app.get("/")
    async def root() -> dict[str, Any]:
        """MCP server info."""
        return {
            "service": "nginx-manager-mcp",
            "version": "0.1.0",
            "tools": 21,
            "status": "running",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/tools")
    async def list_tools() -> dict[str, Any]:
        """List all available MCP tools."""
        from reverse_proxy_mcp.mcp.tools import TOOLS

        return {
            "tools": [
                {
                    "name": name,
                    "description": tool.get("description", ""),
                }
                for name, tool in TOOLS.items()
            ]
        }

    return app


if __name__ == "__main__":
    app = create_mcp_app()
    port = int(getattr(settings, "mcp_port", 5000))
    logger.info(f"Starting MCP server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
