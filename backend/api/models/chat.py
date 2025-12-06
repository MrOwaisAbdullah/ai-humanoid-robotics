"""Pydantic models for chat API."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class RetrievalConfig(BaseModel):
    """Configuration for retrieval operations."""

    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum results to retrieve"
    )
    use_mmr: bool = Field(
        default=True,
        description="Use Maximal Marginal Relevance"
    )
    mmr_lambda: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="MMR diversity parameter"
    )
    exclude_templates: bool = Field(
        default=True,
        description="Exclude template content from results"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include chunk metadata in results"
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question"
    )
    context: Optional[List[str]] = Field(
        None,
        description="Optional context to include"
    )
    config: Optional[RetrievalConfig] = Field(
        None,
        description="Retrieval configuration"
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for context preservation"
    )

    @validator('query')
    def validate_query(cls, v):
        if not v or v.strip() == "":
            raise ValueError("query cannot be empty")
        if len(v.strip()) < 3:
            raise ValueError("query must be at least 3 characters")
        return v.strip()


class TextSelectionRequest(BaseModel):
    """Request model for text selection Q&A."""

    query: str = Field(..., description="Question about selected text")
    selected_text: str = Field(..., description="Text selected by user")
    context: Optional[str] = Field(
        None,
        description="Surrounding context (optional)"
    )
    page_number: Optional[int] = Field(
        None,
        description="Page number if applicable"
    )


class Source(BaseModel):
    """Source information for chat response."""

    content: str = Field(..., description="Relevant content snippet")
    file_path: str = Field(..., description="Source file path")
    section_header: Optional[str] = Field(None, description="Section title")
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    chunk_index: int = Field(..., description="Chunk position in document")
    content_hash: str = Field(..., description="SHA256 hash of content")
    is_duplicate: bool = Field(default=False, description="True if duplicate")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(..., description="Sources used for answer")
    context_used: bool = Field(..., description="Whether RAG context was used")
    query_embedding: Optional[List[float]] = Field(
        None,
        description="Query embedding (for debugging)"
    )
    response_id: str = Field(..., description="Unique response identifier")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    model_used: Optional[str] = Field(None, description="Model used for generation")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    duration_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query")
    config: Optional[RetrievalConfig] = Field(None, description="Search configuration")
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum results to return"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional search filters"
    )


class SearchResult(BaseModel):
    """Single search result."""

    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    file_path: str = Field(..., description="Source file path")
    section_header: Optional[str] = Field(None, description="Section title")
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., description="Result rank")
    is_duplicate: bool = Field(default=False, description="True if duplicate")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response model for semantic search."""

    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total matches found")
    query_time_ms: int = Field(..., description="Search duration in milliseconds")
    query_embedding: Optional[List[float]] = Field(None, description="Query embedding")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="System status")
    version: str = Field(..., description="API version")
    uptime_seconds: int = Field(..., description="Server uptime in seconds")
    services: Dict[str, Any] = Field(..., description="Service statuses")
    metrics: Dict[str, Any] = Field(..., description="System metrics")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Request identifier")