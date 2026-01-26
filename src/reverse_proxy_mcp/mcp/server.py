"""FastMCP server for Reverse Proxy MCP.

Provides HTTP/SSE transport for 21 proxy management tools.
"""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent

from reverse_proxy_mcp.mcp.handlers import TOOL_HANDLERS
from reverse_proxy_mcp.mcp.tools import TOOLS

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP server wrapper for Reverse Proxy MCP tools."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize MCP server.

        Args:
            api_url: Base URL for API server
        """
        self.api_url = api_url
        self.server = Server("reverse-proxy-mcp")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all 21 MCP tools with their handlers."""
        for tool_name, tool_def in TOOLS.items():
            if tool_name in TOOL_HANDLERS:
                self.server.add_tool(
                    tool_def.name,
                    tool_def.description,
                    tool_def.inputSchema,
                    self._create_tool_handler(tool_name),
                )
                logger.debug(f"Registered tool: {tool_name}")
            else:
                logger.warning(f"No handler found for tool: {tool_name}")

        logger.info(f"Registered {len(TOOLS)} MCP tools with handlers")

    def _create_tool_handler(self, tool_name: str):
        """Create handler wrapper for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Async handler function
        """
        handler = TOOL_HANDLERS[tool_name]

        async def tool_handler(arguments: dict[str, Any]) -> list[TextContent]:
            """Execute tool with given arguments.

            Args:
                arguments: Tool arguments from MCP client

            Returns:
                Text content with tool result
            """
            try:
                result = handler(**arguments)
                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                error_result = {"status": "error", "message": str(e)}
                return [TextContent(type="text", text=str(error_result))]

        return tool_handler

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
