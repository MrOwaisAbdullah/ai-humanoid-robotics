"""
Chat models for the AI Book application.

This module contains SQLAlchemy models for chat functionality.
"""

from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, func
)
from sqlalchemy.orm import relationship

from src.database.base import Base


class ChatMessage(Base):
    """Individual messages within chat sessions."""

    class Role(str, Enum):
        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(SQLEnum(Role), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    chat_session = relationship("ChatSession", back_populates="chat_messages")
    anonymous_session = relationship("AnonymousSession", back_populates="chat_messages")