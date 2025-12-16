"""
PersonalizationProfile model for managing user preferences and learning styles.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, UUID, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.base import Base


class ReadingLevel(Enum):
    """Reading proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningStyle(Enum):
    """Learning style preferences."""
    VISUAL = "visual"      # More examples, diagrams
    PRACTICAL = "practical"  # Focus on code, implementation
    THEORETICAL = "theoretical"  # Focus on concepts, theory
    BALANCED = "balanced"


class TermHandling(Enum):
    """Technical term handling preferences."""
    TRANSLATE = "translate"      # Translate technical terms
    TRANSLITERATE = "transliterate"  # Keep in Urdu script
    KEEP_ENGLISH = "keep_english"  # Leave in English


class PersonalizationProfile(Base):
    """Represents user preferences for personalized content delivery."""

    __tablename__ = "personalization_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), unique=True, nullable=False, index=True)

    # Reading preferences
    reading_level = Column(SQLEnum(ReadingLevel), default=ReadingLevel.INTERMEDIATE)
    preferred_language = Column(String(10), default='en')

    # Content preferences
    focus_areas = Column(JSON)  # Array of topics user cares about
    learning_style = Column(SQLEnum(LearningStyle), default=LearningStyle.BALANCED)

    # Translation preferences
    enable_transliteration = Column(Boolean, default=True)
    technical_term_handling = Column(SQLEnum(TermHandling), default=TermHandling.TRANSLITERATE)

    # UI preferences
    font_size = Column(Integer, default=16)
    focus_mode_preferences = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PersonalizationProfile(user_id='{self.user_id}', reading_level='{self.reading_level}')>"


class SavedPersonalization(Base):
    """Model for saved personalized content"""

    __tablename__ = "saved_personalizations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # User relationship
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Content tracking
    original_content_hash = Column(String(64), nullable=False, index=True)
    content_url = Column(String(512), nullable=False)
    content_title = Column(String(200), nullable=False)

    # Personalization data
    personalized_content = Column(Text, nullable=False)
    personalization_metadata = Column(JSON, nullable=False)
    adaptations_applied = Column(JSON, nullable=False)

    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<SavedPersonalization(id={self.id}, user_id={self.user_id}, rating={self.user_rating})>"