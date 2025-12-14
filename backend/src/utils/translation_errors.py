"""
Translation Error Handling Utilities.

Provides custom exceptions and error handling utilities for the
OpenAI Translation System with Gemini API integration.
"""

import asyncio
import time
from typing import Optional, Dict, Any, Callable, TypeVar, Union
from functools import wraps
from enum import Enum

from src.utils.translation_logger import get_translation_logger

logger = get_translation_logger(__name__)

T = TypeVar('T')


class TranslationError(Exception):
    """Base exception for translation errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "TRANSLATION_ERROR",
        severity: str = "MEDIUM",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        is_retriable: bool = True
    ):
        super().__init__(message)
        self.error_type = error_type
        self.severity = severity
        self.error_code = error_code
        self.details = details or {}
        self.is_retriable = is_retriable


class APIError(TranslationError):
    """API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_type="API_ERROR",
            severity="HIGH",
            **kwargs
        )
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(TranslationError):
    """Rate limiting errors."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_type="RATE_LIMIT",
            severity="MEDIUM",
            is_retriable=True,
            **kwargs
        )
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining


class ContentTooLargeError(TranslationError):
    """Content size limit errors."""

    def __init__(
        self,
        message: str,
        content_size: int,
        max_size: int,
        **kwargs
    ):
        super().__init__(
            message,
            error_type="CONTENT_TOO_LARGE",
            severity="MEDIUM",
            is_retriable=False,
            **kwargs
        )
        self.content_size = content_size
        self.max_size = max_size


class InvalidContentError(TranslationError):
    """Invalid content format errors."""

    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        validation_errors: Optional[list] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_type="INVALID_CONTENT",
            severity="MEDIUM",
            is_retriable=False,
            **kwargs
        )
        self.content_type = content_type
        self.validation_errors = validation_errors or []


class SystemError(TranslationError):
    """System-level errors."""

    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_type="SYSTEM_ERROR",
            severity="HIGH",
            is_retriable=True,
            **kwargs
        )
        self.component = component


class TimeoutError(TranslationError):
    """Timeout errors."""

    def __init__(
        self,
        message: str,
        timeout_seconds: int,
        **kwargs
    ):
        super().__init__(
            message,
            error_type="TIMEOUT",
            severity="HIGH",
            is_retriable=True,
            **kwargs
        )
        self.timeout_seconds = timeout_seconds


class ConfigurationError(TranslationError):
    """Configuration errors."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_type="CONFIGURATION_ERROR",
            severity="CRITICAL",
            is_retriable=False,
            **kwargs
        )
        self.config_key = config_key


def with_translation_error_handling(
    default_error: Optional[Exception] = None,
    log_errors: bool = True,
    reraise: bool = True
):
    """
    Decorator for handling translation errors consistently.

    Args:
        default_error: Default error to raise if no specific error matches
        log_errors: Whether to log errors
        reraise: Whether to re-raise errors after handling

    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except TranslationError as e:
                if log_errors:
                    logger.error(
                        f"Translation error in {func.__name__}",
                        error_type=e.error_type,
                        severity=e.severity,
                        message=str(e),
                        details=e.details
                    )
                if reraise:
                    raise
                return None  # type: ignore
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"Unexpected error in {func.__name__}",
                        error=str(e),
                        error_type=type(e).__name__
                    )
                if reraise:
                    raise default_error or SystemError(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        component=func.__module__
                    )
                return None  # type: ignore

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except TranslationError as e:
                if log_errors:
                    logger.error(
                        f"Translation error in {func.__name__}",
                        error_type=e.error_type,
                        severity=e.severity,
                        message=str(e),
                        details=e.details
                    )
                if reraise:
                    raise
                return None  # type: ignore
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"Unexpected error in {func.__name__}",
                        error=str(e),
                        error_type=type(e).__name__
                    )
                if reraise:
                    raise default_error or SystemError(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        component=func.__module__
                    )
                return None  # type: ignore

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


async def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_on: Optional[tuple] = None
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry (must be async)
        max_retries: Maximum number of retries
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Whether to add jitter to delay
        retry_on: Exception types to retry on

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    if retry_on is None:
        retry_on = (APIError, RateLimitError, TimeoutError, SystemError)

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e

            # Don't retry on non-retriable errors or after max retries
            if (
                attempt == max_retries or
                (isinstance(e, TranslationError) and not e.is_retriable) or
                not isinstance(e, retry_on)
            ):
                raise

            # Calculate delay
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)

            # Add jitter if requested
            if jitter:
                import random
                delay *= (0.5 + random.random() * 0.5)

            # For rate limit errors, use the retry-after header if available
            if isinstance(e, RateLimitError) and e.retry_after:
                delay = max(delay, float(e.retry_after))

            logger.warning(
                f"Retrying {func.__name__} after {delay:.2f}s",
                attempt=attempt + 1,
                max_retries=max_retries,
                error=str(e)
            )

            await asyncio.sleep(delay)

    # This should never be reached, but just in case
    raise last_exception  # type: ignore


def handle_api_error(
    status_code: int,
    response_body: Optional[str] = None,
    message: Optional[str] = None
) -> APIError:
    """
    Convert HTTP status code to appropriate API error.

    Args:
        status_code: HTTP status code
        response_body: Response body from API
        message: Custom error message

    Returns:
        Appropriate APIError instance
    """
    # Default messages based on status code
    error_messages = {
        400: "Bad request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not found",
        429: "Rate limit exceeded",
        500: "Internal server error",
        502: "Bad gateway",
        503: "Service unavailable",
        504: "Gateway timeout"
    }

    if message is None:
        message = error_messages.get(status_code, f"HTTP {status_code}")

    # Special handling for rate limit
    if status_code == 429:
        # Try to extract retry-after from response
        retry_after = None
        if response_body:
            try:
                import json
                data = json.loads(response_body)
                retry_after = data.get("retry_after")
            except (json.JSONDecodeError, KeyError):
                pass

        return RateLimitError(
            message,
            status_code=status_code,
            response_body=response_body,
            retry_after=retry_after
        )

    # For other client errors, don't retry
    if 400 <= status_code < 500:
        return APIError(
            message,
            status_code=status_code,
            response_body=response_body,
            is_retriable=False
        )

    # For server errors, allow retry
    return APIError(
        message,
        status_code=status_code,
        response_body=response_body,
        is_retriable=True
    )


class ErrorCollector:
    """Collects and manages errors during translation processing."""

    def __init__(self):
        self.errors: list[Dict[str, Any]] = []
        self.warnings: list[Dict[str, Any]] = []

    def add_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "MEDIUM"
    ) -> None:
        """Add an error to the collector."""
        error_data = {
            "error_type": getattr(error, "error_type", type(error).__name__),
            "message": str(error),
            "severity": getattr(error, "severity", severity),
            "is_retriable": getattr(error, "is_retriable", True),
            "context": context or {},
            "timestamp": time.time()
        }

        # Add additional error details if available
        if isinstance(error, TranslationError):
            error_data.update({
                "error_code": error.error_code,
                "details": error.details
            })

        self.errors.append(error_data)

        logger.error(
            "Error collected",
            error_type=error_data["error_type"],
            message=error_data["message"],
            severity=error_data["severity"]
        )

    def add_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a warning to the collector."""
        warning_data = {
            "message": message,
            "context": context or {},
            "timestamp": time.time()
        }

        self.warnings.append(warning_data)

        logger.warning(
            "Warning collected",
            message=message,
            context=context
        )

    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if any warnings have been collected."""
        return len(self.warnings) > 0

    def get_errors(self) -> list[Dict[str, Any]]:
        """Get all collected errors."""
        return self.errors.copy()

    def get_warnings(self) -> list[Dict[str, Any]]:
        """Get all collected warnings."""
        return self.warnings.copy()

    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected errors and warnings."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.get_errors(),
            "warnings": self.get_warnings()
        }

    def clear(self) -> None:
        """Clear all collected errors and warnings."""
        self.errors.clear()
        self.warnings.clear()