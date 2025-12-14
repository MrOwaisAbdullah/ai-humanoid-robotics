"""
Logging configuration for the application.

Provides structured logging with different levels and outputs.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to level name
        levelcolor = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{levelcolor}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    json_logs: bool = False,
    enable_console: bool = True
) -> None:
    """Configure logging for the application."""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        if json_logs:
            console_formatter = jsonlogger.JsonFormatter(
                fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)

        file_formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Error file handler
    error_log_file = log_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)

    error_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class RequestLogger:
    """Logger for HTTP requests with structured data."""

    def __init__(self, logger_name: str = "request"):
        self.logger = structlog.get_logger(logger_name)

    def log_request(
        self,
        method: str,
        url: str,
        status_code: int = None,
        client_ip: str = None,
        user_id: str = None,
        request_id: str = None,
        duration: float = None,
        headers: Dict[str, Any] = None,
        error: str = None
    ):
        """Log HTTP request with context."""
        log_data = {
            "event": "http_request",
            "method": method,
            "url": url,
            "status_code": status_code,
            "client_ip": client_ip,
            "user_id": user_id,
            "request_id": request_id,
            "duration_ms": duration * 1000 if duration else None,
            "error": error,
        }

        # Add relevant headers
        if headers:
            relevant_headers = {
                k: v for k, v in headers.items()
                if k.lower() in ['user-agent', 'referer', 'x-forwarded-for', 'x-real-ip']
            }
            if relevant_headers:
                log_data["headers"] = relevant_headers

        if error or status_code >= 400:
            self.logger.error("Request failed", **log_data)
        else:
            self.logger.info("Request completed", **log_data)

    def log_error(
        self,
        error: Exception,
        request_id: str = None,
        user_id: str = None,
        context: Dict[str, Any] = None
    ):
        """Log error with context."""
        log_data = {
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "request_id": request_id,
            "user_id": user_id,
        }

        if context:
            log_data.update(context)

        self.logger.error("Application error", exc_info=True, **log_data)


class BusinessLogger:
    """Logger for business events and user actions."""

    def __init__(self, logger_name: str = "business"):
        self.logger = structlog.get_logger(logger_name)

    def log_user_action(
        self,
        action: str,
        user_id: str,
        resource_type: str = None,
        resource_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Log user action for analytics."""
        log_data = {
            "event": "user_action",
            "action": action,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
        }

        if metadata:
            log_data.update(metadata)

        self.logger.info("User action", **log_data)

    def log_reading_progress(
        self,
        user_id: str,
        chapter_id: str,
        section_id: str = None,
        position: float = None,
        time_spent: int = None
    ):
        """Log reading progress events."""
        self.log_user_action(
            action="reading_progress",
            user_id=user_id,
            resource_type="chapter",
            resource_id=chapter_id,
            metadata={
                "section_id": section_id,
                "position": position,
                "time_spent_minutes": time_spent,
            }
        )

    def log_bookmark_action(
        self,
        action: str,  # create, update, delete
        user_id: str,
        bookmark_id: str = None,
        chapter_id: str = None,
        section_id: str = None
    ):
        """Log bookmark actions."""
        self.log_user_action(
            action=f"bookmark_{action}",
            user_id=user_id,
            resource_type="bookmark",
            resource_id=bookmark_id,
            metadata={
                "chapter_id": chapter_id,
                "section_id": section_id,
            }
        )

    def log_search_event(
        self,
        user_id: str,
        query: str,
        results_count: int = None,
        language: str = None,
        filters: Dict[str, Any] = None
    ):
        """Log search events."""
        self.log_user_action(
            action="search",
            user_id=user_id,
            resource_type="search",
            metadata={
                "query": query,
                "results_count": results_count,
                "language": language,
                "filters": filters,
            }
        )

    def log_language_change(
        self,
        user_id: str,
        from_language: str,
        to_language: str
    ):
        """Log language preference changes."""
        self.log_user_action(
            action="language_change",
            user_id=user_id,
            resource_type="preference",
            metadata={
                "from_language": from_language,
                "to_language": to_language,
            }
        )


class SecurityLogger:
    """Logger for security-related events."""

    def __init__(self, logger_name: str = "security"):
        self.logger = structlog.get_logger(logger_name)

    def log_auth_event(
        self,
        event: str,  # login, logout, failed_login, etc.
        user_id: str = None,
        email: str = None,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True,
        reason: str = None
    ):
        """Log authentication events."""
        log_data = {
            "event": f"auth_{event}",
            "user_id": user_id,
            "email": email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
        }

        if reason:
            log_data["reason"] = reason

        if success:
            self.logger.info("Authentication event", **log_data)
        else:
            self.logger.warning("Authentication failure", **log_data)

    def log_permission_denied(
        self,
        user_id: str,
        action: str,
        resource: str,
        ip_address: str = None
    ):
        """Log permission denied events."""
        self.logger.warning(
            "Permission denied",
            event="permission_denied",
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
        )

    def log_suspicious_activity(
        self,
        description: str,
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        details: Dict[str, Any] = None
    ):
        """Log suspicious activity."""
        log_data = {
            "event": "suspicious_activity",
            "description": description,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        if details:
            log_data.update(details)

        self.logger.warning("Suspicious activity detected", **log_data)


# Logger instances
request_logger = RequestLogger()
business_logger = BusinessLogger()
security_logger = SecurityLogger()


# Utility functions
def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_exception(logger: structlog.BoundLogger, message: str, **kwargs):
    """Log an exception with traceback."""
    logger.error(message, exc_info=True, **kwargs)


def set_log_context(**kwargs):
    """Set global logging context."""
    return structlog.contextvars.bind_contextvars(**kwargs)


def correlation_id_filter(record):
    """Filter to add correlation ID to log records."""
    from uuid import uuid4

    correlation_id = getattr(record, 'correlation_id', None) or str(uuid4())
    record.correlation_id = correlation_id
    return record


# Initialize logging with environment variables
def init_logging():
    """Initialize logging from environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", None)
    json_logs = os.getenv("JSON_LOGS", "false").lower() == "true"
    enable_console = os.getenv("ENABLE_CONSOLE_LOGS", "true").lower() == "true"

    setup_logging(
        level=log_level,
        log_file=log_file,
        json_logs=json_logs,
        enable_console=enable_console
    )


# Context manager for logging performance
import time
from contextlib import contextmanager


@contextmanager
def log_performance(logger: structlog.BoundLogger, operation: str, **context):
    """Context manager to log operation performance."""
    start_time = time.time()
    logger.info(f"Starting {operation}", operation=operation, **context)

    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(
            f"Completed {operation}",
            operation=operation,
            duration_seconds=duration,
            **context
        )