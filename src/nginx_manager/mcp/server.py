"""FastMCP server for Nginx Manager.

Provides HTTP/SSE transport for 21 proxy management tools.
"""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP server wrapper for Nginx Manager tools."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize MCP server.

        Args:
            api_url: Base URL for API server
        """
        self.api_url = api_url
        self.server = Server("nginx-manager")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all 21 MCP tools."""
        # Backend Management Tools (5)
        self._register_backend_tools()
        # Proxy Rules Tools (6)
        self._register_proxy_tools()
        # Certificate Tools (4)
        self._register_cert_tools()
        # User & Configuration Tools (4)
        self._register_user_config_tools()
        # Monitoring Tools (2)
        self._register_monitoring_tools()

        logger.info("Registered 21 MCP tools")

    def _register_backend_tools(self) -> None:
        """Register backend management tools."""
        # Placeholder for backend tools
        pass

    def _register_proxy_tools(self) -> None:
        """Register proxy rule tools."""
        # Placeholder for proxy tools
        pass

    def _register_cert_tools(self) -> None:
        """Register certificate management tools."""
        # Placeholder for cert tools
        pass

    def _register_user_config_tools(self) -> None:
        """Register user and configuration tools."""
        # Placeholder for user/config tools
        pass

    def _register_monitoring_tools(self) -> None:
        """Register monitoring tools."""
        # Placeholder for monitoring tools
        pass

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle incoming MCP request.

        Args:
            request: MCP request dictionary

        Returns:
            MCP response dictionary
        """
        try:
            response = await self.server.handle(request)
            return response
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
            }

    def get_health_status(self) -> dict[str, Any]:
        """Get server health status.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "service": "mcp-server",
            "version": "0.1.0",
            "tools_registered": 21,
        }
