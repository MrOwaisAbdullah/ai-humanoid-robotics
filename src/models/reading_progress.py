"""
Reading progress model for tracking user progress through chapters and sections.
"""

from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class ReadingProgress(BaseModel):
    """Stores user's reading progress through chapters and sections."""

    __tablename__ = "reading_progress"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    chapter_id = Column(String(255), nullable=False, index=True)
    section_id = Column(String(255), nullable=False)
    position = Column(Float, nullable=False, default=0.0)  # 0-100 percentage
    completed = Column(Boolean, nullable=False, default=False)
    time_spent = Column(Integer, nullable=False, default=0)  # Minutes
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reading_progress")

    # Unique constraint to ensure one progress record per user per section
    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<ReadingProgress(user_id='{self.user_id}', chapter='{self.chapter_id}', position={self.position}%)>"