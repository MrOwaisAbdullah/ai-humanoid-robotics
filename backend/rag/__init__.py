"""
RAG (Retrieval-Augmented Generation) package for Physical AI & Humanoid Robotics book.

This package provides:
- Document ingestion from Markdown files
- Semantic chunking with overlapping context
- OpenAI embeddings generation
- Qdrant vector storage and retrieval
- Streaming chat responses with citations
"""

__version__ = "1.0.0"

import logging
import structlog
from typing import Any, Dict

# Configure structured logging for RAG components
def configure_rag_logging(
    level: str = "INFO",
    enable_json: bool = False,
    additional_fields: Dict[str, Any] = None
) -> None:
    """Configure structured logging for RAG components."""

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, level.upper()),
    )

    # Configure specific loggers
    loggers = [
        "backend.rag",
        "backend.api",
        "qdrant_client",
        "openai",
        "httpx",
        "aiohttp"
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))

    # Add additional fields if provided
    if additional_fields:
        structlog.contextvars.bind_contextvars(**additional_fields)

# Initialize default configuration
configure_rag_logging(
    level="INFO",
    enable_json=False,
    additional_fields={"service": "rag-api", "version": __version__}
)

# Export the logger for use in other modules
logger = structlog.get_logger(__name__)