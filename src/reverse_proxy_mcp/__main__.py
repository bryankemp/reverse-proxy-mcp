"""Entry point for running the application."""

import uvicorn

from reverse_proxy_mcp.core import settings

if __name__ == "__main__":
    uvicorn.run(
        "nginx_manager.api.main:create_app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        factory=True,
    )
