"""FastAPI middleware for logging and debugging."""

import time
import traceback
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from nginx_manager.core.logging import get_logger, log_exception, log_response

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()

        # Get user info if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)

        # Log request
        logger.debug(
            f"→ {request.method} {request.url.path} | "
            f"User: {user_id} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            log_response(request.method, request.url.path, response.status_code, duration_ms)

            return response

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000

            # Log the exception
            log_exception(
                logger,
                exc,
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "user_id": user_id,
                    "client": request.client.host if request.client else "unknown",
                    "duration_ms": duration_ms,
                },
            )

            # Re-raise to let FastAPI handle it
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and log unhandled errors."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Catch unhandled exceptions and return 500."""
        try:
            return await call_next(request)
        except Exception as exc:
            # Log full traceback
            logger.error(f"Unhandled exception in {request.method} {request.url.path}")
            logger.error(f"Exception type: {type(exc).__name__}")
            logger.error(f"Exception message: {str(exc)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")

            # Return 500 error
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_type": type(exc).__name__,
                    "error_message": (
                        str(exc) if logger.level <= 10 else "An error occurred"
                    ),  # Show details only in debug
                },
            )
