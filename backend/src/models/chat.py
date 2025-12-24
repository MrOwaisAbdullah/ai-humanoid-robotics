"""
Chat models for managing conversations and messages.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, Boolean, DateTime, JSON, Index, ForeignKey
from sqlalchemy.sql import func

from ..core.database import Base


class MessageRole(str, Enum):
    """Message roles in chat conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatStatus(str, Enum):
    """Chat session status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageType(str, Enum):
    """Types of messages."""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    FILE = "file"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"


# ============================================
# Chat Session Model
# ============================================
class ChatSessionBase(SQLModel):
    """Base chat session model."""
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Chat session title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Chat session description"
    )
    status: ChatStatus = Field(
        default=ChatStatus.ACTIVE,
        description="Chat session status"
    )
    model_name: str = Field(
        default="gpt-3.5-turbo",
        max_length=50,
        description="AI model used for this session"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="System prompt for the AI assistant"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="AI model temperature setting"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=4096,
        description="Maximum tokens for AI responses"
    )
    is_pinned: bool = Field(
        default=False,
        description="Whether the chat is pinned"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional chat metadata"
    )
    last_activity_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="Last activity timestamp"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Chat creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Last update timestamp"
    )


class ChatSession(ChatSessionBase, table=True):
    """Chat session model with database table."""
    __tablename__ = "chat_sessions"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
        description="User ID (null for anonymous chats)"
    )

    # Define indexes for performance
    __table_args__ = (
        Index('idx_chat_user_status', 'user_id', 'status'),
        Index('idx_chat_created_at', 'created_at'),
        Index('idx_chat_last_activity', 'last_activity_at'),
        Index('idx_chat_is_pinned', 'is_pinned'),
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(
        back_populates="chat_session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ChatSessionCreate(ChatSessionBase):
    """Chat session creation schema."""
    pass


class ChatSessionUpdate(SQLModel):
    """Chat session update schema."""
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Updated title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated description"
    )
    status: Optional[ChatStatus] = Field(
        default=None,
        description="Updated status"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Updated system prompt"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Updated temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=4096,
        description="Updated max tokens"
    )
    is_pinned: Optional[bool] = Field(
        default=None,
        description="Updated pin status"
    )


class ChatSessionRead(ChatSessionBase):
    """Chat session read schema."""
    id: int
    user_id: Optional[int]
    last_activity_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = Field(
        default=None,
        description="Number of messages in the session"
    )


# ============================================
# Chat Message Model
# ============================================
class ChatMessageBase(SQLModel):
    """Base chat message model."""
    content: str = Field(
        description="Message content"
    )
    role: MessageRole = Field(
        description="Message role (user/assistant/system/tool)"
    )
    message_type: MessageType = Field(
        default=MessageType.TEXT,
        description="Type of message content"
    )
    token_count: Optional[int] = Field(
        default=None,
        description="Number of tokens in the message"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional message metadata"
    )
    is_deleted: bool = Field(
        default=False,
        description="Whether the message has been deleted"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Message creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Last update timestamp"
    )


class ChatMessage(ChatMessageBase, table=True):
    """Chat message model with database table."""
    __tablename__ = "chat_messages"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    chat_session_id: int = Field(
        foreign_key="chat_sessions.id",
        nullable=False,
        index=True
    )
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
        description="User ID (null for anonymous messages)"
    )
    parent_message_id: Optional[int] = Field(
        default=None,
        foreign_key="chat_messages.id",
        nullable=True,
        index=True,
        description="Parent message ID for threading"
    )

    # Define indexes for performance
    __table_args__ = (
        Index('idx_message_session_role', 'chat_session_id', 'role'),
        Index('idx_message_session_created', 'chat_session_id', 'created_at'),
        Index('idx_message_user_created', 'user_id', 'created_at'),
        Index('idx_message_parent', 'parent_message_id'),
    )

    # Relationships
    chat_session: ChatSession = Relationship(back_populates="messages")
    user: Optional["User"] = Relationship()
    parent_message: Optional["ChatMessage"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "ChatMessage.id"
        }
    )
    child_messages: List["ChatMessage"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "ChatMessage.parent_message_id"
        }
    )


class ChatMessageCreate(ChatMessageBase):
    """Chat message creation schema."""
    pass


class ChatMessageUpdate(SQLModel):
    """Chat message update schema."""
    content: Optional[str] = Field(
        default=None,
        description="Updated content"
    )
    is_deleted: Optional[bool] = Field(
        default=None,
        description="Updated deletion status"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated metadata"
    )


class ChatMessageRead(ChatMessageBase):
    """Chat message read schema."""
    id: int
    chat_session_id: int
    user_id: Optional[int]
    parent_message_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# ============================================
# Chat Analytics Model (Optional)
# ============================================
class ChatAnalyticsBase(SQLModel):
    """Base chat analytics model."""
    total_messages: int = Field(
        default=0,
        description="Total messages sent"
    )
    total_tokens: int = Field(
        default=0,
        description="Total tokens used"
    )
    average_response_time: Optional[float] = Field(
        default=None,
        description="Average AI response time in seconds"
    )
    session_duration: Optional[int] = Field(
        default=None,
        description="Session duration in seconds"
    )
    user_satisfaction: Optional[float] = Field(
        default=None,
        ge=1.0,
        le=5.0,
        description="User satisfaction rating"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional analytics data"
    )
    created_at: datetime = Field(
        default_factory=func.now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Analytics creation timestamp"
    )


class ChatAnalytics(ChatAnalyticsBase, table=True):
    """Chat analytics model with database table."""
    __tablename__ = "chat_analytics"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    chat_session_id: int = Field(
        foreign_key="chat_sessions.id",
        nullable=False,
        unique=True,
        index=True
    )
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True
    )

    # Relationships
    chat_session: ChatSession = Relationship()
    user: Optional["User"] = Relationship()


# ============================================
# Import User model to avoid circular imports
# ============================================
try:
    from .user import User
except ImportError:
    # User model might not be created yet
    pass