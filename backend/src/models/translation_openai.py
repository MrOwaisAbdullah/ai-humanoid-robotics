"""
Comprehensive OpenAI Translation System Models.

Provides database models for:
- Translation jobs with progress tracking
- Chunk-based translation processing
- Enhanced caching with page URL + content hash
- Error logging and retry tracking
- User session management
- Translation quality metrics
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, SmallInteger, ForeignKey,
    Index, Boolean, Numeric, JSON, BigInteger, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func

from src.database.base import Base


class TranslationJobStatus(Enum):
    """Translation job status values."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    CHUNK_PROCESSING = "chunk_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"


class ChunkStatus(Enum):
    """Translation chunk status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"  # For code blocks


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TranslationJob(Base):
    """
    Represents a translation job with comprehensive tracking.

    Supports:
    - Large text translation with chunking
    - Progress tracking
    - Error handling and retries
    - Performance metrics
    - Cost tracking
    """

    __tablename__ = "translation_jobs"

    # Primary key and identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(64), unique=True, nullable=False, index=True)  # External job ID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)

    # Content identifiers for caching
    content_hash = Column(String(64), nullable=False, index=True)
    page_url = Column(Text, nullable=True, index=True)  # Source page URL for caching

    # Translation parameters
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)

    # Content information
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)

    # Processing options
    preserve_code_blocks = Column(Boolean, default=True, nullable=False)
    enable_transliteration = Column(Boolean, default=True, nullable=False)
    chunk_size = Column(Integer, default=2000, nullable=False)  # Characters per chunk
    max_chunks = Column(Integer, default=100, nullable=False)

    # OpenAI specific settings
    model_name = Column(String(50), nullable=False, default="gpt-4-turbo-preview")
    temperature = Column(Numeric(3, 2), default=0.3, nullable=False)
    max_tokens = Column(Integer, default=2048, nullable=False)

    # Status and progress
    status = Column(String(20), default=TranslationJobStatus.PENDING.value, nullable=False, index=True)
    progress_percentage = Column(Numeric(5, 2), default=0.0, nullable=False)
    chunks_total = Column(Integer, default=0, nullable=False)
    chunks_completed = Column(Integer, default=0, nullable=False)
    chunks_failed = Column(Integer, default=0, nullable=False)

    # Retry settings
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Performance metrics
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_ms = Column(BigInteger, default=0, nullable=False)

    # Cost tracking
    input_tokens = Column(BigInteger, default=0, nullable=False)
    output_tokens = Column(BigInteger, default=0, nullable=False)
    estimated_cost_usd = Column(Numeric(10, 6), default=0.000000, nullable=False)
    actual_cost_usd = Column(Numeric(10, 6), nullable=True)

    # Quality metrics
    quality_score = Column(Numeric(5, 2), nullable=True)  # 1-5 score
    confidence_score = Column(Numeric(5, 2), nullable=True)  # 1-5 score

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Supports IPv6

    # Relationships
    user = relationship("User", back_populates="translation_jobs")
    chunks = relationship("TranslationChunk", back_populates="job", cascade="all, delete-orphan")
    errors = relationship("TranslationError", back_populates="job", cascade="all, delete-orphan")
    metrics = relationship("TranslationMetrics", back_populates="job", cascade="all, delete-orphan")
    cache_entries = relationship("TranslationCache", back_populates="job", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_job_status_created', 'status', 'created_at'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_content_lookup', 'content_hash', 'source_language', 'target_language'),
        Index('idx_job_page_cache', 'page_url', 'content_hash'),
        Index('idx_activity', 'last_activity_at'),
        Index('idx_progress', 'status', 'progress_percentage'),
        CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_progress_range'),
        CheckConstraint('temperature >= 0 AND temperature <= 2', name='check_temperature_range'),
        CheckConstraint('chunk_size > 0 AND chunk_size <= 10000', name='check_chunk_size'),
    )

    def __repr__(self):
        return f"<TranslationJob(id={self.id}, status={self.status}, progress={self.progress_percentage}%)>"


class TranslationChunk(Base):
    """
    Represents a chunk of text being translated.

    Supports:
    - Individual chunk status tracking
    - Retry mechanism
    - Performance metrics per chunk
    - Code block detection
    """

    __tablename__ = "translation_chunks"

    # Primary key and identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("translation_jobs.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)

    # Content
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)

    # Position in original text
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)

    # Chunk properties
    is_code_block = Column(Boolean, default=False, nullable=False)
    code_language = Column(String(50), nullable=True)
    word_count = Column(Integer, nullable=False)

    # Status and processing
    status = Column(String(20), default=ChunkStatus.PENDING.value, nullable=False, index=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Processing metrics
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_ms = Column(BigInteger, default=0, nullable=False)

    # Token usage
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)

    # Quality indicators
    confidence_score = Column(Numeric(5, 2), nullable=True)
    requires_review = Column(Boolean, default=False, nullable=False)

    # Error information
    last_error = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    job = relationship("TranslationJob", back_populates="chunks")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_job_chunk', 'job_id', 'chunk_index', unique=True),
        Index('idx_chunk_status', 'status', 'created_at'),
        Index('idx_code_blocks', 'is_code_block', 'code_language'),
        CheckConstraint('chunk_index >= 0', name='check_chunk_index'),
        CheckConstraint('start_position >= 0 AND end_position >= start_position', name='check_positions'),
        CheckConstraint('word_count >= 0', name='check_word_count'),
    )

    def __repr__(self):
        return f"<TranslationChunk(job_id={self.job_id}, index={self.chunk_index}, status={self.status})>"


class TranslationError(Base):
    """
    Tracks errors during translation processing.

    Supports:
    - Detailed error logging
    - Error categorization
    - Retry tracking
    - Error analytics
    """

    __tablename__ = "translation_errors"

    # Primary key and identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("translation_jobs.id"), nullable=False, index=True)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("translation_chunks.id"), nullable=True, index=True)
    error_id = Column(String(64), unique=True, nullable=False, index=True)  # Unique error identifier

    # Error details
    error_type = Column(String(50), nullable=False, index=True)  # e.g., "api_error", "timeout", "rate_limit"
    error_code = Column(String(50), nullable=True)  # API error code
    error_message = Column(Text, nullable=False)
    error_details = Column(JSON, nullable=True)  # Additional error context

    # Severity and categorization
    severity = Column(String(20), default=ErrorSeverity.MEDIUM.value, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # e.g., "network", "parsing", "validation"

    # Retry information
    is_retriable = Column(Boolean, default=True, nullable=False)
    retry_attempt = Column(Integer, default=1, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Context information
    request_payload = Column(JSON, nullable=True)  # Sanitized request data
    response_payload = Column(JSON, nullable=True)  # Sanitized response data

    # Stack trace and debugging
    stack_trace = Column(Text, nullable=True)
    debug_info = Column(JSON, nullable=True)

    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(String(200), nullable=True)  # How the error was resolved

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    job = relationship("TranslationJob", back_populates="errors")
    chunk = relationship("TranslationChunk")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_error_type_created', 'error_type', 'created_at'),
        Index('idx_error_severity', 'severity', 'created_at'),
        Index('idx_job_errors', 'job_id', 'created_at'),
        Index('idx_retry_schedule', 'next_retry_at', 'is_retriable'),
    )

    def __repr__(self):
        return f"<TranslationError(id={self.id}, type={self.error_type}, severity={self.severity})>"


class TranslationSession(Base):
    """
    Manages user translation sessions.

    Supports:
    - Session-based tracking
    - Rate limiting
    - User preferences
    - Analytics
    """

    __tablename__ = "translation_sessions"

    # Primary key and identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # Session information
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Usage tracking
    request_count = Column(Integer, default=0, nullable=False)
    character_count = Column(Integer, default=0, nullable=False)
    total_cost_usd = Column(Numeric(10, 6), default=0.000000, nullable=False)

    # Rate limiting
    requests_per_minute = Column(Integer, default=60, nullable=False)
    characters_per_hour = Column(Integer, default=100000, nullable=False)

    # Session context
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), nullable=True)
    preferred_model = Column(String(50), nullable=True)

    # Client information
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    country_code = Column(String(2), nullable=True)

    # Session preferences (stored as JSON)
    preferences = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="translation_sessions")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_user_sessions', 'user_id', 'is_active'),
        Index('idx_session_expiry', 'expires_at', 'is_active'),
        Index('idx_ip_sessions', 'ip_address', 'started_at'),
        CheckConstraint('request_count >= 0', name='check_request_count'),
        CheckConstraint('character_count >= 0', name='check_character_count'),
        CheckConstraint('requests_per_minute > 0', name='check_rate_limit_requests'),
        CheckConstraint('characters_per_hour > 0', name='check_rate_limit_chars'),
    )

    def __repr__(self):
        return f"<TranslationSession(id={self.session_id}, active={self.is_active}, requests={self.request_count})>"


class TranslationCache(Base):
    """
    Enhanced translation caching with page URL support.

    Supports:
    - Page URL + content hash keys
    - Hierarchical caching
    - Cache invalidation
    - Cache analytics
    """

    __tablename__ = "translation_cache"

    # Primary key and identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(128), unique=True, nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("translation_jobs.id"), nullable=True, index=True)

    # Cache keys
    content_hash = Column(String(64), nullable=False, index=True)
    page_url = Column(Text, nullable=True, index=True)
    url_hash = Column(String(64), nullable=True, index=True)  # Hash of URL for privacy

    # Translation data
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)

    # Cache metadata
    hit_count = Column(Integer, default=0, nullable=False)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Quality and performance
    quality_score = Column(Numeric(5, 2), nullable=True)
    processing_time_ms = Column(BigInteger, nullable=False)
    model_version = Column(String(50), nullable=False)

    # Cache configuration
    ttl_hours = Column(Integer, default=168, nullable=False)  # 7 days default
    is_pinned = Column(Boolean, default=False, nullable=False)  # Never expires if pinned
    priority = Column(Integer, default=0, nullable=False)  # Higher priority less likely to evict

    # Validation
    is_validated = Column(Boolean, default=False, nullable=False)
    validated_by = Column(String(50), nullable=True)  # user_id or "system"

    # Relationships
    job = relationship("TranslationJob", back_populates="cache_entries")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_cache_lookup', 'content_hash', 'source_language', 'target_language'),
        Index('idx_page_cache', 'url_hash', 'content_hash'),
        Index('idx_cache_expires', 'expires_at', 'priority'),
        Index('idx_cache_popularity', 'hit_count', 'last_hit_at'),
        CheckConstraint('hit_count >= 0', name='check_hit_count'),
        CheckConstraint('processing_time_ms >= 0', name='check_processing_time'),
        CheckConstraint('ttl_hours > 0', name='check_ttl_hours'),
    )

    def __repr__(self):
        return f"<TranslationCache(key={self.cache_key[:20]}..., hits={self.hit_count})>"


class TranslationMetrics(Base):
    """
    Tracks detailed translation metrics and analytics.

    Supports:
    - Performance monitoring
    - Quality analytics
    - Cost tracking
    - Usage statistics
    """

    __tablename__ = "translation_metrics"

    # Primary key and identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("translation_jobs.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    # Time period
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # hourly, daily, weekly, monthly

    # Usage metrics
    total_requests = Column(Integer, default=0, nullable=False)
    total_characters = Column(BigInteger, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    successful_translations = Column(Integer, default=0, nullable=False)
    failed_translations = Column(Integer, default=0, nullable=False)

    # Performance metrics
    avg_processing_time_ms = Column(BigInteger, default=0, nullable=False)
    min_processing_time_ms = Column(BigInteger, default=0, nullable=False)
    max_processing_time_ms = Column(BigInteger, default=0, nullable=False)
    p95_processing_time_ms = Column(BigInteger, default=0, nullable=False)

    # Cost metrics
    total_input_tokens = Column(BigInteger, default=0, nullable=False)
    total_output_tokens = Column(BigInteger, default=0, nullable=False)
    total_cost_usd = Column(Numeric(12, 6), default=0.000000, nullable=False)
    avg_cost_per_char = Column(Numeric(10, 8), default=0.00000000, nullable=False)

    # Quality metrics
    avg_quality_score = Column(Numeric(5, 2), nullable=True)
    avg_confidence_score = Column(Numeric(5, 2), nullable=True)

    # Cache metrics
    cache_hits = Column(Integer, default=0, nullable=False)
    cache_misses = Column(Integer, default=0, nullable=False)
    cache_hit_rate = Column(Numeric(5, 2), default=0.0, nullable=False)

    # Error metrics
    error_count = Column(Integer, default=0, nullable=False)
    error_rate = Column(Numeric(5, 2), default=0.0, nullable=False)
    top_error_types = Column(JSON, nullable=True)  # Top 5 error types with counts

    # Additional dimensions
    source_language = Column(String(10), nullable=True, index=True)
    target_language = Column(String(10), nullable=True, index=True)
    model_name = Column(String(50), nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    job = relationship("TranslationJob", back_populates="metrics")
    user = relationship("User", back_populates="translation_metrics")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_metrics_date_period', 'metric_date', 'period_type'),
        Index('idx_user_metrics', 'user_id', 'metric_date'),
        Index('idx_job_metrics', 'job_id', 'metric_date'),
        Index('idx_lang_metrics', 'source_language', 'target_language', 'metric_date'),
        CheckConstraint('total_requests >= 0', name='check_total_requests'),
        CheckConstraint('total_characters >= 0', name='check_total_characters'),
        CheckConstraint('cache_hit_rate >= 0 AND cache_hit_rate <= 100', name='check_cache_hit_rate'),
        CheckConstraint('error_rate >= 0 AND error_rate <= 100', name='check_error_rate'),
    )

    def __repr__(self):
        return f"<TranslationMetrics(date={self.metric_date}, requests={self.total_requests})>"