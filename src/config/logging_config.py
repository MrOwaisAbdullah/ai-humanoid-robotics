"""
Production-ready logging configuration.

Configures structured logging with multiple handlers, sensitive data filtering,
and integration with monitoring systems.
"""

import sys
import json
import logging
import logging.handlers
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import traceback
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger
from structlog import processors, stdlib, configure
from structlog.typing import FilteringBoundLogger

from .translation_config import get_config, LogLevel


# Context variables for request tracking
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in log records."""

    def __init__(self, sensitive_fields: List[str] = None, mask_char: str = "*"):
        super().__init__()
        self.sensitive_fields = [field.lower() for field in (sensitive_fields or [])]
        self.mask_char = mask_char

    def filter(self, record):
        """Filter sensitive data from log record."""
        # Filter message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._mask_sensitive_data(str(record.msg))

        # Filter args
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )

        # Filter extra attributes
        for attr_name in dir(record):
            if not attr_name.startswith('_') and attr_name not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                attr_value = getattr(record, attr_name)
                if isinstance(attr_value, str):
                    setattr(record, attr_name, self._mask_sensitive_data(attr_value))

        return True

    def _mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data in text."""
        import re

        # General patterns
        patterns = [
            (r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\']?)([\w\-\.]+)', lambda m: f"{m.group(1)}{self.mask_char * len(m.group(2))}"),
            (r'(?i)(password["\']?\s*[:=]\s*["\']?)([\w\-\.]+)', lambda m: f"{m.group(1)}{self.mask_char * len(m.group(2))}"),
            (r'(?i)(token["\']?\s*[:=]\s*["\']?)([\w\-\.]+)', lambda m: f"{m.group(1)}{self.mask_char * len(m.group(2))}"),
            (r'(?i)(secret["\']?\s*[:=]\s*["\']?)([\w\-\.]+)', lambda m: f"{m.group(1)}{self.mask_char * len(m.group(2))}"),
            (r'(?i)(authorization["\']?\s*[:=]\s*["\']?)([\w\-\.]+)', lambda m: f"{m.group(1)}{self.mask_char * len(m.group(2))}"),
            (r'(Bearer\s+)([\w\-\.]+)', lambda m: f"{m.group(1)}{self.mask_char * len(m.group(2))}"),
        ]

        # Custom field patterns
        for field in self.sensitive_fields:
            patterns.append(
                (rf'(?i)({field}["\']?\s*[:=]\s*["\']?)([\w\-\.]+)',
                 lambda m, f=field: f"{m.group(1)}{self.mask_char * len(m.group(2))}")
            )

        # Apply patterns
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)

        return text


class ContextFilter(logging.Filter):
    """Add context information to log records."""

    def filter(self, record):
        """Add context variables to log record."""
        record.request_id = request_id.get()
        record.user_id = user_id.get()
        record.session_id = session_id.get()
        return True


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to JSON log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()

        # Add context
        if hasattr(record, 'request_id') and record.request_id:
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id') and record.user_id:
            log_record['user_id'] = record.user_id
        if hasattr(record, 'session_id') and record.session_id:
            log_record['session_id'] = record.session_id

        # Add exception details
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # Add source location
        log_record['source'] = {
            'file': record.filename,
            'line': record.lineno,
            'function': record.funcName,
            'module': record.module
        }


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Add color to levelname
        record.levelname = f"{log_color}{record.levelname}{reset}"

        # Add request ID if present
        if hasattr(record, 'request_id') and record.request_id:
            record.msg = f"[{record.request_id[:8]}] {record.msg}"

        return super().format(record)


def setup_logging() -> None:
    """Setup logging configuration based on environment."""
    config = get_config()

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.logging.level.value))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if config.logging.json_format:
        formatter = JSONFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            config.logging.format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if config.logging.json_format:
        console_handler.setFormatter(formatter)
    else:
        console_handler.setFormatter(ColoredFormatter(config.logging.format))
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)

    # File handler (if enabled)
    if config.logging.file_logging:
        setup_file_handler(root_logger, formatter, config)

    # Apply sensitive data filter
    if config.logging.filter_sensitive_data:
        sensitive_filter = SensitiveDataFilter(config.logging.sensitive_fields)
        for handler in root_logger.handlers:
            handler.addFilter(sensitive_filter)

    # Configure structlog
    if config.logging.json_format:
        configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=stdlib.LoggerFactory(),
            wrapper_class=stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer()
            ],
            context_class=dict,
            logger_factory=stdlib.LoggerFactory(),
            wrapper_class=stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        level=config.logging.level.value,
        json_format=config.logging.json_format,
        file_logging=config.logging.file_logging,
        filter_sensitive=config.logging.filter_sensitive_data
    )


def setup_file_handler(
    logger: logging.Logger,
    formatter: Union[logging.Formatter, JSONFormatter],
    config
) -> None:
    """Setup file handler with rotation."""
    # Create logs directory
    log_path = Path(config.logging.file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse rotation settings
    when = "midnight"
    if config.logging.file_rotation.endswith(" day"):
        when = "midnight"
    elif config.logging.file_rotation.endswith(" hour"):
        when = "H"
    elif config.logging.file_rotation.endswith(" minute"):
        when = "M"

    # Parse backup count from retention
    backup_count = 30  # Default
    if "days" in config.logging.file_retention:
        backup_count = int(config.logging.file_retention.split()[0])

    # Create rotating file handler
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=_parse_size(config.logging.max_file_size),
            backupCount=backup_count,
            encoding='utf-8'
        )
    except Exception:
        # Fallback to TimedRotatingFileHandler
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_path,
            when=when,
            backupCount=backup_count,
            encoding='utf-8'
        )

    file_handler.setFormatter(formatter)
    file_handler.addFilter(ContextFilter())
    logger.addHandler(file_handler)


def _parse_size(size_str: str) -> int:
    """Parse size string to bytes."""
    size_str = size_str.upper().strip()
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3
    }

    for unit, multiplier in multipliers.items():
        if size_str.endswith(unit):
            return int(float(size_str[:-len(unit)]) * multiplier)

    return int(size_str)


def bind_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Bind context variables for logging."""
    context = {}

    if request_id:
        request_id.set(request_id)
        context['request_id'] = request_id

    if user_id:
        user_id.set(user_id)
        context['user_id'] = user_id

    if session_id:
        session_id.set(session_id)
        context['session_id'] = session_id

    return context


def unbind_context() -> None:
    """Clear all context variables."""
    request_id.set(None)
    user_id.set(None)
    session_id.set(None)


class LogContext:
    """Context manager for log context."""

    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ):
        self.context = bind_context(request_id, user_id, session_id)
        self.context.update(kwargs)
        self.old_context = {}

    def __enter__(self):
        # Store old context
        for key, value in self.context.items():
            var = globals().get(key)
            if var:
                self.old_context[key] = var.get()
                var.set(value)

        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        for key, value in self.old_context.items():
            var = globals().get(key)
            if var:
                var.set(value)


def log_function_call(func):
    """Decorator to log function calls."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(
            "Function called",
            function=func.__name__,
            args_count=len(args),
            kwargs=list(kwargs.keys())
        )
        try:
            result = func(*args, **kwargs)
            logger.debug(
                "Function completed",
                function=func.__name__
            )
            return result
        except Exception as e:
            logger.error(
                "Function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(
            "Async function called",
            function=func.__name__,
            args_count=len(args),
            kwargs=list(kwargs.keys())
        )
        try:
            result = await func(*args, **kwargs)
            logger.debug(
                "Async function completed",
                function=func.__name__
            )
            return result
        except Exception as e:
            logger.error(
                "Async function failed",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper


# Initialize logging on import
setup_logging()