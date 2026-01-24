"""FastAPI application factory."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nginx_manager.api.v1 import auth, backends, proxy_rules
from nginx_manager.core import create_all_tables, settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Create database tables
    create_all_tables()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Include API routers
    app.include_router(auth.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(backends.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(proxy_rules.router, prefix=f"{settings.api_prefix}/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "version": settings.app_version}

    # Root endpoint
    @app.get("/")
    async def root() -> dict:
        """Root endpoint."""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "api_docs": f"{settings.api_prefix}/v1/docs",
        }

    logger.info(f"{settings.app_name} v{settings.app_version} initialized")

    return app
