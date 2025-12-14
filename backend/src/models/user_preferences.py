"""
User preferences model for storing personalization settings.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class UserPreference(BaseModel):
    """Stores user personalization settings."""

    __tablename__ = "user_preferences"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    language = Column(String(10), nullable=False, default='en')  # en, ur, ur-roman
    reading_pace = Column(String(20), nullable=False, default='medium')  # slow, medium, fast
    preferred_depth = Column(String(20), nullable=False, default='detailed')  # overview, detailed, comprehensive
    show_code_examples = Column(Boolean, nullable=False, default=True)
    adaptive_difficulty = Column(Boolean, nullable=False, default=False)
    theme = Column(String(20), nullable=False, default='auto')  # light, dark, auto
    font_size = Column(Integer, nullable=False, default=16)
    line_height = Column(Float, nullable=False, default=1.5)

    # Relationships
    user = relationship("User", back_populates="preferences")
    custom_notes = relationship("UserCustomNote", back_populates="preference", cascade="all, delete-orphan")

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<UserPreference(user_id='{self.user_id}', language='{self.language}', theme='{self.theme}')>"


class UserCustomNote(BaseModel):
    """Custom notes as key-value pairs for user preferences."""

    __tablename__ = "user_custom_notes"

    user_preference_id = Column(String(36), ForeignKey("user_preferences.id"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)

    # Relationships
    preference = relationship("UserPreference", back_populates="custom_notes")

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<UserCustomNote(key='{self.key}', preference_id='{self.user_preference_id}')>"