"""MCP server entry point.

Runs the FastMCP server with HTTP streamable transport.
"""

import logging

from reverse_proxy_mcp.mcp.server import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Port is configured in server.py via FastMCP(port=...)
    # FastMCP defaults to 8000 internally, mapped to 5000 via Docker
    logger.info("Starting FastMCP server")
    logger.info("HTTP transport endpoint: http://0.0.0.0:5000/mcp (mapped via Docker)")
    logger.info("Server capabilities: tools (22), resources (9), prompts (5)")

    # Run FastMCP server with streamable HTTP transport
    mcp.run(transport="streamable-http")
