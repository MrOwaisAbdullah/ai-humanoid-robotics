"""
Translation and TranslationFeedback models for managing translations and user feedback.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import CheckConstraint
from src.database.base import Base


class Translation(Base):
    """Represents a translated text with caching capabilities."""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    translation_model = Column(String(50), nullable=False)  # e.g., "gemini-1.5-pro"
    character_count = Column(Integer, nullable=False)

    # Relationships
    feedback = relationship("TranslationFeedback", back_populates="translation")

    # Constraints
    __table_args__ = (
        Index('idx_content_lookup', 'content_hash', 'source_language', 'target_language'),
    )

    def __repr__(self):
        return f"<Translation(id={self.id}, source='{self.source_language}', target='{self.target_language}')>"


class TranslationFeedback(Base):
    """Represents user feedback on translations for quality improvement."""

    __tablename__ = "translation_feedback"

    id = Column(Integer, primary_key=True)
    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=False)
    user_id = Column(String(36), nullable=False)  # UUID from auth system
    rating = Column(SmallInteger, nullable=False)  # -1 (down) or 1 (up)
    comment = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    translation = relationship("Translation", back_populates="feedback")

    # Constraints
    __table_args__ = (
        Index('idx_user_translation', 'user_id', 'translation_id', unique=True),
        CheckConstraint('rating IN (-1, 1)', name='check_rating_range'),
    )

    def __repr__(self):
        return f"<TranslationFeedback(id={self.id}, translation_id={self.translation_id}, rating={self.rating})>"