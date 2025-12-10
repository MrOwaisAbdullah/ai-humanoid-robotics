"""
Error handling utilities for the API.

Provides custom exceptions and error response formatting.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class BaseError(Exception):
    """Base class for custom application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        cause: Exception = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(BaseError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundError(BaseError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: Union[str, int] = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        details = {"resource": resource}
        if identifier:
            details["identifier"] = str(identifier)
        super().__init__(message, "NOT_FOUND", details)


class ConflictError(BaseError):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str, resource: str = None, identifier: Union[str, int] = None):
        details = {}
        if resource:
            details["resource"] = resource
        if identifier:
            details["identifier"] = str(identifier)
        super().__init__(message, "CONFLICT", details)


class PermissionError(BaseError):
    """Raised when user lacks permission for an action."""

    def __init__(self, action: str, resource: str = None):
        message = f"Permission denied for action: {action}"
        if resource:
            message += f" on resource: {resource}"
        details = {"action": action}
        if resource:
            details["resource"] = resource
        super().__init__(message, "PERMISSION_DENIED", details)


class AuthenticationError(BaseError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(BaseError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class RateLimitError(BaseError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)


class DatabaseError(BaseError):
    """Raised when database operation fails."""

    def __init__(self, message: str, operation: str = None, cause: Exception = None):
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(message, "DATABASE_ERROR", details, cause)


class ExternalServiceError(BaseError):
    """Raised when external service call fails."""

    def __init__(
        self,
        message: str,
        service: str = None,
        status_code: int = None,
        response_body: str = None
    ):
        details = {}
        if service:
            details["service"] = service
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


# Response models
class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None, description="Field name if validation error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    errors: Optional[List[ErrorDetail]] = Field(None, description="List of validation errors")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


# Error handler functions
def create_error_response(
    error: BaseError,
    request_id: str = None,
    include_traceback: bool = False
) -> ErrorResponse:
    """Create standardized error response."""
    error_dict = error.to_dict()

    response = ErrorResponse(
        error=error_dict["error"],
        message=error_dict["message"],
        details=error_dict.get("details"),
        timestamp=logger.makeRecord(
            name="error",
            level=40,
            pathname="",
            lineno=0,
            msg=error.message,
            args=(),
            exc_info=None
        ).asctime,
        request_id=request_id
    )

    if include_traceback and error.cause:
        response.details["traceback"] = traceback.format_exc(type(error.cause), error.cause, error.cause.__traceback__)

    return response


def handle_database_error(error: SQLAlchemyError, operation: str = None) -> DatabaseError:
    """Handle database errors and convert to DatabaseError."""
    logger.error(f"Database error in {operation or 'unknown operation'}: {str(error)}")

    # Check for specific database errors
    if "unique constraint" in str(error).lower():
        return ConflictError("Resource already exists", cause=error)
    elif "foreign key constraint" in str(error).lower():
        return ValidationError("Referenced resource does not exist", cause=error)
    elif "connection" in str(error).lower():
        return DatabaseError("Database connection failed", operation, error)
    else:
        return DatabaseError("Database operation failed", operation, error)


def handle_validation_error(exc: Exception) -> ValidationError:
    """Handle Pydantic validation errors."""
    if hasattr(exc, 'errors'):
        # Pydantic v2 validation error
        errors = exc.errors()  # type: ignore
        messages = []
        for error in errors:
            field = '.'.join(str(x) for x in error['loc'])
            messages.append(f"{field}: {error['msg']}")
        message = f"Validation failed: {'; '.join(messages)}"
        return ValidationError(message)
    else:
        return ValidationError(str(exc))


def create_http_exception(error: BaseError, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Convert BaseError to HTTPException."""
    return HTTPException(
        status_code=status_code,
        detail=create_error_response(error).dict()
    )


# Error status code mapping
ERROR_STATUS_MAP = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    PermissionError: status.HTTP_403_FORBIDDEN,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
}


def get_error_status_code(error: BaseError) -> int:
    """Get appropriate HTTP status code for error type."""
    return ERROR_STATUS_MAP.get(type(error), status.HTTP_500_INTERNAL_SERVER_ERROR)


# Decorator for error handling
def handle_errors(func):
    """Decorator to automatically handle exceptions in endpoint functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseError as e:
            status_code = get_error_status_code(e)
            raise create_http_exception(e, status_code)
        except SQLAlchemyError as e:
            db_error = handle_database_error(e)
            status_code = get_error_status_code(db_error)
            raise create_http_exception(db_error, status_code)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            error = BaseError("An unexpected error occurred", "INTERNAL_ERROR")
            raise create_http_exception(error)
    return wrapper


# Context manager for error handling
class ErrorHandler:
    """Context manager for handling errors within a block."""

    def __init__(self, operation: str = None, reraise: bool = True):
        self.operation = operation
        self.reraise = reraise
        self.error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True

        if isinstance(exc_val, BaseError):
            self.error = exc_val
        elif isinstance(exc_val, SQLAlchemyError):
            self.error = handle_database_error(exc_val, self.operation)
        else:
            logger.error(f"Unexpected error in {self.operation or 'operation'}: {str(exc_val)}", exc_info=True)
            self.error = BaseError("An unexpected error occurred", "INTERNAL_ERROR")

        if self.reraise:
            raise self.error

        return True


# Error metrics tracking
class ErrorMetrics:
    """Track error metrics for monitoring."""

    def __init__(self):
        self.errors: Dict[str, int] = {}
        self.total_errors = 0

    def record_error(self, error: BaseError):
        """Record an error occurrence."""
        self.errors[error.error_code] = self.errors.get(error.error_code, 0) + 1
        self.total_errors += 1

    def get_error_rate(self, total_requests: int) -> float:
        """Calculate error rate."""
        return (self.total_errors / total_requests * 100) if total_requests > 0 else 0

    def get_top_errors(self, limit: int = 5) -> List[tuple]:
        """Get top occurring errors."""
        sorted_errors = sorted(self.errors.items(), key=lambda x: x[1], reverse=True)
        return sorted_errors[:limit]

    def reset(self):
        """Reset error metrics."""
        self.errors = {}
        self.total_errors = 0


# Global error metrics instance
error_metrics = ErrorMetrics()


# Utility functions
def log_error(error: BaseError, request_id: str = None, user_id: str = None):
    """Log error with context."""
    logger.error(
        f"{error.error_code}: {error.message}",
        extra={
            "error_code": error.error_code,
            "details": error.details,
            "request_id": request_id,
            "user_id": user_id,
            "error_type": type(error).__name__,
        },
        exc_info=error.cause
    )
    error_metrics.record_error(error)