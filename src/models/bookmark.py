"""
Bookmark model for user-saved page references with optional metadata.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class Bookmark(BaseModel):
    """Represents user-saved page references with optional metadata."""

    __tablename__ = "bookmarks"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    chapter_id = Column(String(255), nullable=False, index=True)
    section_id = Column(String(255), nullable=True)
    page_url = Column(String(2048), nullable=False)
    page_title = Column(String(255), nullable=False)
    snippet = Column(Text, nullable=True)
    note = Column(String(1000), nullable=True)
    is_private = Column(Boolean, nullable=False, default=True)

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    tags = relationship("BookmarkTag", back_populates="bookmark", cascade="all, delete-orphan")

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<Bookmark(id='{self.id}', user_id='{self.user_id}', title='{self.page_title}')>"


class BookmarkTag(BaseModel):
    """Tags for organizing bookmarks."""

    __tablename__ = "bookmark_tags"

    bookmark_id = Column(String(36), ForeignKey("bookmarks.id"), nullable=False, index=True)
    tag = Column(String(50), nullable=False, index=True)

    # Relationships
    bookmark = relationship("Bookmark", back_populates="tags")

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<BookmarkTag(bookmark_id='{self.bookmark_id}', tag='{self.tag}')>"