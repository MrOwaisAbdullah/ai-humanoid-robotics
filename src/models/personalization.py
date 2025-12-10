"""
PersonalizationProfile model for managing user preferences and learning styles.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import ENUM as Enum
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
    reading_level = Column(Enum(ReadingLevel), default=ReadingLevel.INTERMEDIATE)
    preferred_language = Column(String(10), default='en')

    # Content preferences
    focus_areas = Column(JSON)  # Array of topics user cares about
    learning_style = Column(Enum(LearningStyle), default=LearningStyle.BALANCED)

    # Translation preferences
    enable_transliteration = Column(Boolean, default=True)
    technical_term_handling = Column(Enum(TermHandling), default=TermHandling.TRANSLITERATE)

    # UI preferences
    font_size = Column(Integer, default=16)
    focus_mode_preferences = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PersonalizationProfile(user_id='{self.user_id}', reading_level='{self.reading_level}')>"