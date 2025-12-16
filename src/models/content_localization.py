"""
Content localization model for tracking translation status of content pages.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Index, Enum as SQLEnum
from src.database.base import Base


class ProcessingStatus(Enum):
    """Processing status for content localization."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some chunks failed


class ContentLocalization(Base):
    """Tracks the translation status and metadata for content pages."""

    __tablename__ = "content_localization"

    id = Column(Integer, primary_key=True)
    content_url = Column(String(500), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False, index=True)

    # Localization status
    is_translated = Column(Boolean, default=False)
    last_translation_date = Column(DateTime)
    translation_cache_key = Column(String(64))

    # Content metadata
    word_count = Column(Integer)
    character_count = Column(Integer)
    has_code_blocks = Column(Boolean, default=False)
    detected_languages = Column(JSON)  # Array of detected languages

    # Processing metadata
    chunk_count = Column(Integer, default=1)
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ContentLocalization(url='{self.content_url}', status='{self.processing_status}', translated={self.is_translated})>"