"""FastAPI application factory."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from reverse_proxy_mcp.api.middleware import ErrorHandlingMiddleware, LoggingMiddleware
from reverse_proxy_mcp.api.v1 import (
    auth,
    backends,
    certificates,
    config,
    monitoring,
    proxy_rules,
    users,
)
from reverse_proxy_mcp.api.v2 import matrix
from reverse_proxy_mcp.core import create_all_tables, settings
from reverse_proxy_mcp.core.database import SessionLocal
from reverse_proxy_mcp.core.logging import get_logger, setup_logging
from reverse_proxy_mcp.core.security import hash_password
from reverse_proxy_mcp.models.database import User

# Initialize logging first
setup_logging()
logger = get_logger(__name__)


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
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info(f"Created admin user: {admin_email}")
        db.close()
    except Exception as e:
        logger.error(f"Failed to initialize admin user: {e}")


def _find_webui_path() -> Path | None:
    env_dir = os.getenv("WEBUI_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p
    candidates = [
        Path("/app/webui/build/web"),
        Path(__file__).resolve().parents[3] / "webui" / "build" / "web",
        Path.cwd() / "webui" / "build" / "web",
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return None


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

    # Add error handling middleware (first to catch all errors)
    app.add_middleware(ErrorHandlingMiddleware)

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Include API routers
    # v1 endpoints (hierarchical)
    app.include_router(auth.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(backends.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(proxy_rules.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(users.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(certificates.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(config.router, prefix=f"{settings.api_prefix}/v1")
    app.include_router(monitoring.router, prefix=f"{settings.api_prefix}/v1")

    # v2 endpoints (matrix URIs)
    app.include_router(matrix.router)

    # Setup static files for Flutter web UI (works in container and local dev)
    web_ui_path = _find_webui_path()
    if web_ui_path and web_ui_path.is_dir():
        # Mount known static asset directories
        for dirname in ["assets", "canvaskit", "icons"]:
            dir_path = web_ui_path / dirname
            if dir_path.is_dir():
                app.mount(f"/{dirname}", StaticFiles(directory=str(dir_path)), name=dirname)

        # Mount specific files
        @app.get("/")
        async def root() -> FileResponse:
            return FileResponse(web_ui_path / "index.html", media_type="text/html")

        @app.get("/index.html")
        async def index() -> FileResponse:
            return FileResponse(web_ui_path / "index.html", media_type="text/html")

        @app.get("/manifest.json")
        async def manifest() -> FileResponse:
            return FileResponse(web_ui_path / "manifest.json")

        @app.get("/favicon.png")
        async def favicon() -> FileResponse:
            return FileResponse(web_ui_path / "favicon.png")

        @app.get("/flutter.js")
        async def flutter_js() -> FileResponse:
            return FileResponse(web_ui_path / "flutter.js")

        @app.get("/flutter_bootstrap.js")
        async def flutter_bootstrap() -> FileResponse:
            return FileResponse(web_ui_path / "flutter_bootstrap.js")

        @app.get("/flutter_service_worker.js")
        async def flutter_sw() -> FileResponse:
            return FileResponse(web_ui_path / "flutter_service_worker.js")

        @app.get("/main.dart.js")
        async def main_dart() -> FileResponse:
            return FileResponse(web_ui_path / "main.dart.js")

        @app.get("/version.json")
        async def version_json() -> FileResponse:
            return FileResponse(web_ui_path / "version.json")

        # SPA fallback: catch-all that serves index.html for unknown routes
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            """Serve Flutter web app with SPA fallback to index.html."""
            file_path = web_ui_path / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            # Fallback to index.html for SPA client-side routing
            return FileResponse(web_ui_path / "index.html")

        logger.info(f"Serving web UI from {web_ui_path}")
    else:
        logger.warning("Web UI not found; looked in ENV WEBUI_DIR and common paths")

    logger.info(f"{settings.app_name} v{settings.app_version} initialized")
    return app
