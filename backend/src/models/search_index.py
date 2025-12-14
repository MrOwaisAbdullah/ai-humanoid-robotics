"""
Search index model for enabling fast content retrieval across languages.
"""

from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.sql import func
from src.models.base import BaseModel


class SearchIndex(BaseModel):
    """Enables fast content retrieval across languages."""

    __tablename__ = "search_index"

    content_id = Column(String(255), nullable=False, index=True)
    language = Column(String(10), nullable=False, index=True)  # en, ur, ur-roman
    content_type = Column(String(20), nullable=False, index=True)  # chapter, section, bookmark
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    chapter_id = Column(String(255), nullable=False, index=True)
    section_id = Column(String(255), nullable=True)
    rank = Column(Float, nullable=False, default=0.5)  # 0-1 for result ranking
    indexed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<SearchIndex(content_id='{self.content_id}', language='{self.language}', type='{self.content_type}')>"