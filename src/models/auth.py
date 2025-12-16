"""
Authentication models for the AI Book application.

This module contains SQLAlchemy models for user authentication,
sessions, and related entities.
"""

from typing import Optional
from enum import Enum

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime,
    Text, JSON, ForeignKey, Enum as SQLEnum, func
)
from sqlalchemy.orm import relationship
import uuid

from src.database.base import Base


class User(Base):
    """Represents a registered user with email/password authentication."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    background = relationship("UserBackground", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    onboarding_responses = relationship("OnboardingResponse", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    folders = relationship("ChatFolder", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("ChatTag", back_populates="user", cascade="all, delete-orphan")
    translation_jobs = relationship("TranslationJob", back_populates="user", cascade="all, delete-orphan")
    translation_sessions = relationship("TranslationSession", back_populates="user", cascade="all, delete-orphan")
    translation_metrics = relationship("TranslationMetrics", back_populates="user", cascade="all, delete-orphan")
    reading_progress = relationship("ReadingProgress", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    """OAuth provider accounts (Google, etc.) linked to users."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # 'google', 'github', etc.
    provider_account_id = Column(String, nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    token_type = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="accounts")


class UserBackground(Base):
    """Stores user's technical background for personalization."""

    __tablename__ = "user_backgrounds"

    class ExperienceLevel(str, Enum):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"

    class HardwareExpertise(str, Enum):
        NONE = "None"
        ARDUINO = "Arduino"
        ROS_PRO = "ROS-Pro"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    experience_level = Column(SQLEnum(ExperienceLevel), nullable=False)
    years_of_experience = Column(Integer, nullable=False, default=0)
    preferred_languages = Column(JSON, nullable=False, default=list)
    hardware_expertise = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="background")


class OnboardingResponse(Base):
    """Captures individual onboarding question responses."""

    __tablename__ = "onboarding_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    question_key = Column(String(100), nullable=False)
    response_value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="onboarding_responses")


class Session(Base):
    """Active user authentication sessions with sliding expiration."""

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")


class PasswordResetToken(Base):
    """Temporary tokens for secure password reset."""

    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")


class AnonymousSession(Base):
    """Temporary session for anonymous chat users."""

    __tablename__ = "anonymous_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships - ChatSession links to AnonymousSession, not ChatMessage directly
    chat_sessions = relationship("ChatSession", back_populates="anonymous_session")


class ChatSession(Base):
    """Conversation threads associated with users or anonymous sessions."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    anonymous_session_id = Column(String(36), ForeignKey("anonymous_sessions.id"), nullable=True)
    folder_id = Column(String(36), ForeignKey("chat_folders.id"), nullable=True)
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    anonymous_session = relationship("AnonymousSession")
    folder = relationship("ChatFolder", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Individual messages within chat sessions."""

    __tablename__ = "chat_messages"

    class Role(str, Enum):
        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(SQLEnum(Role), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    edit_count = Column(Integer, default=0, nullable=False)

    # Relationships
    chat_session = relationship("ChatSession", back_populates="chat_messages")
    versions = relationship("MessageVersion", back_populates="message", cascade="all, delete-orphan")


class UserPreferences(Base):
    """User-specific settings and preferences."""
    __tablename__ = "user_preferences"

    class Theme(str, Enum):
        LIGHT = "light"
        DARK = "dark"
        AUTO = "auto"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    theme = Column(SQLEnum(Theme), default=Theme.AUTO, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    notification_settings = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")


class MessageVersion(Base):
    """Track version history of edited messages."""

    __tablename__ = "message_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("chat_messages.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    edit_reason = Column(String(500), nullable=True)  # Optional reason for editing

    # Relationships
    message = relationship("ChatMessage", back_populates="versions")


class ChatFolder(Base):
    """User-defined folders for organizing chat sessions."""

    __tablename__ = "chat_folders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="folders")
    chat_sessions = relationship("ChatSession", back_populates="folder")


class ChatTag(Base):
    """Tags for categorizing chat sessions."""

    __tablename__ = "chat_tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=True)  # Hex color code
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="tags")


class MessageReaction(Base):
    """Reactions/em responses to chat messages."""

    __tablename__ = "message_reactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    emoji = Column(String(50), nullable=False)  # Emoji or reaction name
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    message = relationship("ChatMessage")
    user = relationship("User")