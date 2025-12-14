"""
Logging configuration for OpenAI Translation System.

Provides structured logging with correlation IDs for translation requests,
performance metrics, and error tracking.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
from functools import wraps

import structlog
from structlog.stdlib import LoggerFactory

from src.utils.logging import get_logger

# Configure structlog for translation service
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Get translation-specific logger
translation_logger = structlog.get_logger("translation")


class TranslationLogger:
    """
    Enhanced logger for translation operations with correlation tracking.
    """

    def __init__(self, name: str):
        """
        Initialize translation logger.

        Args:
            name: Logger name (usually the module name)
        """
        self.logger = structlog.get_logger(f"translation.{name}")
        self.start_time: Optional[float] = None
        self.correlation_id: Optional[str] = None

    def bind_request(self, request_id: Optional[str] = None) -> 'TranslationLogger':
        """
        Bind request correlation ID to logger.

        Args:
            request_id: Request ID (generates UUID if not provided)

        Returns:
            Self for method chaining
        """
        self.correlation_id = request_id or str(uuid.uuid4())
        self.logger = self.logger.bind(
            correlation_id=self.correlation_id,
            request_id=request_id
        )
        return self

    def bind_job(self, job_id: str, **kwargs) -> 'TranslationLogger':
        """
        Bind translation job context to logger.

        Args:
            job_id: Translation job ID
            **kwargs: Additional job context

        Returns:
            Self for method chaining
        """
        self.logger = self.logger.bind(
            job_id=job_id,
            **kwargs
        )
        return self

    def bind_chunk(self, chunk_index: int, **kwargs) -> 'TranslationLogger':
        """
        Bind translation chunk context to logger.

        Args:
            chunk_index: Chunk index
            **kwargs: Additional chunk context

        Returns:
            Self for method chaining
        """
        self.logger = self.logger.bind(
            chunk_index=chunk_index,
            **kwargs
        )
        return self

    def start_timer(self) -> float:
        """
        Start timing an operation.

        Returns:
            Start timestamp
        """
        self.start_time = time.time()
        return self.start_time

    def end_timer(self, operation: str) -> float:
        """
        End timing an operation and log the duration.

        Args:
            operation: Operation name

        Returns:
            Duration in milliseconds
        """
        if self.start_time is None:
            self.logger.warning("Timer not started", operation=operation)
            return 0.0

        duration_ms = (time.time() - self.start_time) * 1000
        self.logger.info(
            "Operation completed",
            operation=operation,
            duration_ms=duration_ms
        )
        self.start_time = None
        return duration_ms

    @contextmanager
    def time_operation(self, operation: str, **context):
        """
        Context manager for timing operations.

        Args:
            operation: Operation name
            **context: Additional context to log
        """
        start_time = time.time()
        self.logger.info(
            "Operation started",
            operation=operation,
            **context
        )

        try:
            yield
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(
                "Operation completed",
                operation=operation,
                duration_ms=duration_ms,
                success=True,
                **context
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "Operation failed",
                operation=operation,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                **context
            )
            raise

    def log_translation_request(
        self,
        text_length: int,
        source_lang: str,
        target_lang: str,
        page_url: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log translation request details.

        Args:
            text_length: Length of text to translate
            source_lang: Source language
            target_lang: Target language
            page_url: Page URL (if available)
            **kwargs: Additional context
        """
        self.logger.info(
            "Translation request",
            text_length=text_length,
            source_lang=source_lang,
            target_lang=target_lang,
            page_url=page_url,
            **kwargs
        )

    def log_translation_response(
        self,
        translated_length: int,
        chunks_count: int,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        cached: bool = False,
        **kwargs
    ) -> None:
        """
        Log translation response details.

        Args:
            translated_length: Length of translated text
            chunks_count: Number of chunks processed
            tokens_used: Tokens used (if available)
            cost_usd: Cost in USD (if available)
            cached: Whether response was from cache
            **kwargs: Additional context
        """
        self.logger.info(
            "Translation response",
            translated_length=translated_length,
            chunks_count=chunks_count,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            cached=cached,
            **kwargs
        )

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Log error with full context.

        Args:
            error: Exception that occurred
            context: Additional error context
            **kwargs: Additional log context
        """
        error_data = {
            "error_type": getattr(error, "error_type", type(error).__name__),
            "error_message": str(error),
            "severity": getattr(error, "severity", "MEDIUM"),
            "is_retriable": getattr(error, "is_retriable", True)
        }

        if context:
            error_data.update(context)

        error_data.update(kwargs)

        self.logger.error(
            "Translation error",
            **error_data
        )

    def log_performance_metrics(
        self,
        metrics: Dict[str, Union[int, float]],
        **kwargs
    ) -> None:
        """
        Log performance metrics.

        Args:
            metrics: Dictionary of metrics
            **kwargs: Additional context
        """
        self.logger.info(
            "Performance metrics",
            **metrics,
            **kwargs
        )

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)


def get_translation_logger(name: str) -> TranslationLogger:
    """
    Get a translation logger instance.

    Args:
        name: Logger name (usually the module name)

    Returns:
        TranslationLogger instance
    """
    return TranslationLogger(name)


def log_translation_performance(func):
    """
    Decorator to automatically log translation function performance.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_translation_logger(func.__module__)
        logger.bind_request()

        # Extract relevant information from kwargs if available
        text_length = None
        source_lang = kwargs.get('source_lang') or kwargs.get('source_language')
        target_lang = kwargs.get('target_lang') or kwargs.get('target_language')

        # Try to get text length from args or kwargs
        if args:
            # Assume first argument might be the text or request object
            if hasattr(args[0], 'text'):
                text_length = len(args[0].text)
            elif isinstance(args[0], str):
                text_length = len(args[0])
        elif 'text' in kwargs:
            text_length = len(kwargs['text'])
        elif 'request' in kwargs and hasattr(kwargs['request'], 'text'):
            text_length = len(kwargs['request'].text)

        if text_length and source_lang and target_lang:
            logger.log_translation_request(
                text_length=text_length,
                source_lang=source_lang,
                target_lang=target_lang
            )

        with logger.time_operation(func.__name__):
            try:
                result = await func(*args, **kwargs)

                # Log success metrics if available
                if hasattr(result, 'translated_text'):
                    translated_length = len(result.translated_text)
                elif isinstance(result, str):
                    translated_length = len(result)
                else:
                    translated_length = 0

                logger.log_translation_response(
                    translated_length=translated_length,
                    chunks_count=getattr(result, 'chunks_count', 1),
                    tokens_used=getattr(result, 'tokens_used', None),
                    cost_usd=getattr(result, 'cost_usd', None),
                    cached=getattr(result, 'cached', False)
                )

                return result

            except Exception as e:
                logger.log_error(e, function=func.__name__)
                raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_translation_logger(func.__module__)
        logger.bind_request()

        # Similar logic for sync functions
        text_length = None
        if args and isinstance(args[0], str):
            text_length = len(args[0])
        elif 'text' in kwargs:
            text_length = len(kwargs['text'])

        if text_length:
            logger.info(
                "Function called",
                function=func.__name__,
                text_length=text_length
            )

        with logger.time_operation(func.__name__):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.log_error(e, function=func.__name__)
                raise

    # Return appropriate wrapper based on whether function is async
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class PerformanceTracker:
    """
    Tracks performance metrics for translation operations.
    """

    def __init__(self):
        self.metrics: Dict[str, Any] = {}

    def start_operation(self, operation_id: str, operation_type: str) -> None:
        """Start tracking an operation."""
        self.metrics[operation_id] = {
            "type": operation_type,
            "start_time": time.time(),
            "end_time": None,
            "duration_ms": None
        }

    def end_operation(self, operation_id: str, **metadata) -> float:
        """End tracking an operation and return duration."""
        if operation_id not in self.metrics:
            return 0.0

        end_time = time.time()
        self.metrics[operation_id].update({
            "end_time": end_time,
            "duration_ms": (end_time - self.metrics[operation_id]["start_time"]) * 1000,
            **metadata
        })

        return self.metrics[operation_id]["duration_ms"]

    def get_metrics(self) -> Dict[str, Any]:
        """Get all tracked metrics."""
        return self.metrics.copy()

    def clear_metrics(self) -> None:
        """Clear all tracked metrics."""
        self.metrics.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        if not self.metrics:
            return {}

        durations = [
            m["duration_ms"] for m in self.metrics.values()
            if m["duration_ms"] is not None
        ]

        if not durations:
            return {}

        return {
            "total_operations": len(self.metrics),
            "completed_operations": len(durations),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations)
        }


# Global performance tracker
performance_tracker = PerformanceTracker()