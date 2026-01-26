"""FastMCP server for Reverse Proxy MCP.

Provides HTTP streamable transport with tools, resources, and prompts.
"""

import logging
import os

from mcp.server.fastmcp import FastMCP

from reverse_proxy_mcp.mcp.prompts import register_prompts
from reverse_proxy_mcp.mcp.resources import register_resources
from reverse_proxy_mcp.mcp.tools import register_tools

logger = logging.getLogger(__name__)

# Get port from environment or use default
port = int(os.getenv("MCP_PORT", "5000"))

# Initialize FastMCP server with port configuration
mcp = FastMCP(
    name="reverse-proxy-mcp",
    port=port,
)

# Register all components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

logger.info("FastMCP server initialized with tools, resources, and prompts")
