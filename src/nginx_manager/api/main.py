"""FastAPI application factory."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nginx_manager.api.v1 import auth, backends, certificates, config, proxy_rules, users
from nginx_manager.core import create_all_tables, settings
from nginx_manager.core.database import SessionLocal
from nginx_manager.core.security import hash_password
from nginx_manager.models.database import User

logger = logging.getLogger(__name__)


def _initialize_admin_user() -> None:
    """Initialize admin user from environment variables if not exists."""
    try:
        db = SessionLocal()
        admin_email = os.getenv("ADMIN_EMAIL", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "password")
        
        # Check if admin user exists
        existing = db.query(User).filter(User.username == admin_email).first()
        if not existing:
            # Create admin user
            admin = User(
                username=admin_email,
                email=f"{admin_email}@nginx-manager.local",
                password_hash=hash_password(admin_password),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info(f"Created admin user: {admin_email}")
        db.close()
    except Exception as e:
        logger.error(f"Failed to initialize admin user: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Create database tables
    create_all_tables()
    
    # Initialize admin user
    _initialize_admin_user()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Include API routers
    app.include_router(auth.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(backends.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(proxy_rules.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(users.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(certificates.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(config.router, prefix=f"{settings.api_prefix}/v1")

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
