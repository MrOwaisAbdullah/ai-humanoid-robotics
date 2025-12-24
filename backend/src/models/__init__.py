"""
Database models for the AI Book backend application.
Includes both legacy SQLAlchemy models and new SQLModel models.
"""

# Import legacy SQLAlchemy models (for compatibility)
from .auth import (
    User as LegacyUser, Account, UserBackground, OnboardingResponse, Session,
    PasswordResetToken, AnonymousSession, ChatSession as LegacyChatSession,
    ChatMessage as LegacyChatMessage,
    UserPreferences, MessageVersion, ChatFolder, ChatTag, MessageReaction
)

from .translation_openai import (
    TranslationJob, TranslationChunk, TranslationError,
    TranslationSession, TranslationCache, TranslationMetrics,
    TranslationJobStatus, ChunkStatus, ErrorSeverity
)

# Import new SQLModel models
from .user import (
    User,
    UserCreate,
    UserUpdate,
    UserRead,
    UserPublic,
    UserRole,
    UserStatus,
    AuthProvider,
    UserSession,
    RefreshToken,
    EmailVerification,
    PasswordReset,
    OAuthAccount,
)

from .chat import (
    ChatSession,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionRead,
    ChatMessage,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageRead,
    MessageRole,
    ChatStatus,
    MessageType,
    ChatAnalytics,
)

# Export all models for easy importing
__all__ = [
    # Legacy SQLAlchemy models (for compatibility)
    "LegacyUser",
    "Account",
    "UserBackground",
    "OnboardingResponse",
    "Session",
    "PasswordResetToken",
    "AnonymousSession",
    "LegacyChatSession",
    "LegacyChatMessage",
    "UserPreferences",
    "MessageVersion",
    "ChatFolder",
    "ChatTag",
    "MessageReaction",

    # Translation models
    "TranslationJob",
    "TranslationChunk",
    "TranslationError",
    "TranslationSession",
    "TranslationCache",
    "TranslationMetrics",
    "TranslationJobStatus",
    "ChunkStatus",
    "ErrorSeverity",

    # New SQLModel User models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserPublic",
    "UserRole",
    "UserStatus",
    "AuthProvider",
    "UserSession",
    "RefreshToken",
    "EmailVerification",
    "PasswordReset",
    "OAuthAccount",

    # New SQLModel Chat models
    "ChatSession",
    "ChatSessionCreate",
    "ChatSessionUpdate",
    "ChatSessionRead",
    "ChatMessage",
    "ChatMessageCreate",
    "ChatMessageUpdate",
    "ChatMessageRead",
    "MessageRole",
    "ChatStatus",
    "MessageType",
    "ChatAnalytics",
]