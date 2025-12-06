"""Custom exceptions for the RAG API."""

from typing import Any, Dict, Optional
from fastapi import HTTPException
import uuid


class RAGException(Exception):
    """Base exception for RAG system errors."""

    def __init__(
        self,
        message: str,
        code: str = "RAG_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RAGException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else None
        )


class ContentNotFoundError(RAGException):
    """Raised when no content is found for a query."""

    def __init__(self, query: str, threshold: float = None):
        super().__init__(
            message=f"No relevant content found for query: {query[:100]}...",
            code="CONTENT_NOT_FOUND",
            details={
                "query": query,
                "similarity_threshold": threshold,
                "suggestion": "Try rephrasing your question or check if documents are ingested"
            }
        )


class IngestionError(RAGException):
    """Raised during document ingestion."""

    def __init__(self, message: str, file_path: str = None):
        super().__init__(
            message=message,
            code="INGESTION_ERROR",
            details={"file_path": file_path} if file_path else None
        )


class EmbeddingError(RAGException):
    """Raised during embedding generation."""

    def __init__(self, message: str, retry_count: int = None):
        super().__init__(
            message=message,
            code="EMBEDDING_ERROR",
            details={"retry_count": retry_count} if retry_count else None
        )


class VectorStoreError(RAGException):
    """Raised during vector store operations."""

    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=message,
            code="VECTOR_STORE_ERROR",
            details={"operation": operation} if operation else None
        )


class RateLimitError(RAGException):
    """Raised when rate limits are exceeded."""

    def __init__(self, service: str, retry_after: int = None):
        super().__init__(
            message=f"Rate limit exceeded for {service}",
            code="RATE_LIMIT_ERROR",
            details={
                "service": service,
                "retry_after": retry_after,
                "suggestion": "Please wait before making another request"
            }
        )


class ConfigurationError(RAGException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key} if config_key else None
        )


def create_http_exception(
    exc: RAGException,
    status_code: int = 500,
    request_id: Optional[str] = None
) -> HTTPException:
    """Convert RAGException to HTTPException with proper format."""

    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id or str(uuid.uuid4())
            }
        }
    )


def handle_validation_error(field: str, message: str) -> HTTPException:
    """Create a validation error HTTP exception."""

    exc = ValidationError(message, field)
    return create_http_exception(exc, status_code=422)


def handle_content_not_found(query: str, threshold: float = None) -> HTTPException:
    """Create a content not found HTTP exception."""

    exc = ContentNotFoundError(query, threshold)
    return create_http_exception(exc, status_code=404)


def handle_ingestion_error(message: str, file_path: str = None) -> HTTPException:
    """Create an ingestion error HTTP exception."""

    exc = IngestionError(message, file_path)
    return create_http_exception(exc, status_code=500)


def handle_rate_limit_error(service: str, retry_after: int = None) -> HTTPException:
    """Create a rate limit error HTTP exception."""

    exc = RateLimitError(service, retry_after)
    headers = {"Retry-After": str(retry_after)} if retry_after else None
    return create_http_exception(exc, status_code=429, request_id=None)


def handle_embedding_error(message: str, retry_count: int = None) -> HTTPException:
    """Create an embedding error HTTP exception."""

    exc = EmbeddingError(message, retry_count)
    return create_http_exception(exc, status_code=502)


def handle_vector_store_error(message: str, operation: str = None) -> HTTPException:
    """Create a vector store error HTTP exception."""

    exc = VectorStoreError(message, operation)
    return create_http_exception(exc, status_code=503)