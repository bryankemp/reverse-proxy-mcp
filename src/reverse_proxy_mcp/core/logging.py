"""Centralized logging configuration for Nginx Manager."""

import logging
import sys
from pathlib import Path
from typing import Any

from reverse_proxy_mcp.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """Setup application logging with console and file handlers."""
    # Create logs directory
    log_dir = Path(settings.logs_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_format = ColoredFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler for all logs
    file_handler = logging.FileHandler(log_dir / "reverse_proxy_mcp.log")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)8s | %(name)30s | %(funcName)20s:%(lineno)4d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.FileHandler(log_dir / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    root_logger.addHandler(error_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Debug mode: {settings.debug}")
    logger.debug(f"Log directory: {log_dir}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_exception(
    logger: logging.Logger, exc: Exception, context: dict[str, Any] | None = None
) -> None:
    """Log an exception with context.

    Args:
        logger: Logger instance
        exc: Exception to log
        context: Additional context to log
    """
    logger.error(f"Exception occurred: {type(exc).__name__}: {exc}")
    if context:
        logger.error(f"Context: {context}")
    logger.exception("Stack trace:")


def log_request(method: str, path: str, user_id: int | None = None, **kwargs: Any) -> None:
    """Log an API request.

    Args:
        method: HTTP method
        path: Request path
        user_id: User ID making the request
        **kwargs: Additional request data
    """
    logger = get_logger("reverse_proxy_mcp.api")
    logger.info(f"{method} {path} | User: {user_id} | {kwargs}")


def log_response(method: str, path: str, status_code: int, duration_ms: float) -> None:
    """Log an API response.

    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger("reverse_proxy_mcp.api")
    level = logging.INFO if status_code < 400 else logging.ERROR
    logger.log(level, f"{method} {path} | Status: {status_code} | Duration: {duration_ms:.2f}ms")


def log_db_query(
    query: str, params: dict[str, Any] | None = None, duration_ms: float | None = None
) -> None:
    """Log a database query (only in debug mode).

    Args:
        query: SQL query
        params: Query parameters
        duration_ms: Query duration in milliseconds
    """
    if settings.debug:
        logger = get_logger("reverse_proxy_mcp.db")
        msg = f"Query: {query}"
        if params:
            msg += f" | Params: {params}"
        if duration_ms:
            msg += f" | Duration: {duration_ms:.2f}ms"
        logger.debug(msg)


def log_nginx_operation(operation: str, success: bool, message: str = "") -> None:
    """Log an Nginx operation.

    Args:
        operation: Operation name (e.g., 'reload', 'validate')
        success: Whether operation succeeded
        message: Additional message
    """
    logger = get_logger("reverse_proxy_mcp.nginx")
    level = logging.INFO if success else logging.ERROR
    status = "SUCCESS" if success else "FAILED"
    logger.log(level, f"Nginx {operation} {status} | {message}")
