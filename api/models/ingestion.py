"""Pydantic models for document ingestion API."""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class IngestionConfig(BaseModel):
    """Configuration for document ingestion process."""

    chunk_size: int = Field(
        default=600,
        ge=100,
        le=2000,
        description="Target chunk size in tokens"
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Token overlap between chunks"
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["*.draft", "README.md", "*.tmp"],
        description="Glob patterns to exclude from ingestion"
    )
    template_patterns: List[str] = Field(
        default_factory=lambda: [
            r'^how to use this book$',
            r'^table of contents$',
            r'^foreword$',
            r'^preface$',
            r'^about this book$'
        ],
        description="Regex patterns for template content to exclude"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum file size in bytes"
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Batch size for embedding generation"
    )


class IngestionRequest(BaseModel):
    """Request model for document ingestion."""

    content_path: str = Field(
        ...,
        description="Path to directory or file to ingest"
    )
    force_reindex: bool = Field(
        default=False,
        description="Clear existing data before ingestion"
    )
    config: Optional[IngestionConfig] = Field(
        None,
        description="Ingestion configuration"
    )

    @validator('content_path')
    def validate_content_path(cls, v):
        if not v or v.strip() == "":
            raise ValueError("content_path cannot be empty")
        if v.startswith(".."):
            raise ValueError("content_path must not traverse parent directories")
        return v


class ChunkMetadata(BaseModel):
    """Metadata for each chunk."""

    file_path: str
    section_header: Optional[str] = None
    chapter: Optional[str] = None
    chunk_index: int
    token_count: int
    content_hash: str
    is_template: bool = False
    created_at: str


class IngestionJob(BaseModel):
    """Status of an ingestion job."""

    job_id: str
    source_path: str
    status: str  # pending, running, completed, failed
    files_processed: int = 0
    chunks_created: int = 0
    chunks_skipped: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_time: Optional[int] = None  # in seconds


class IngestionResponse(BaseModel):
    """Response model for ingestion initiation."""

    job_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None


class ChunkInfo(BaseModel):
    """Information about a single chunk."""

    chunk_id: str
    content_preview: str = Field(..., max_length=200)
    file_path: str
    section_header: Optional[str] = None
    token_count: int
    is_template: bool