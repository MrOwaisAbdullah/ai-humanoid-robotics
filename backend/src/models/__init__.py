"""
Import all models to ensure they are registered with SQLAlchemy.
"""

# Import all models to register them with SQLAlchemy
from .auth import (
    User, Account, UserBackground, OnboardingResponse, Session,
    PasswordResetToken, AnonymousSession, ChatSession, ChatMessage,
    UserPreferences, MessageVersion, ChatFolder, ChatTag, MessageReaction
)

from .translation_openai import (
    TranslationJob, TranslationChunk, TranslationError,
    TranslationSession, TranslationCache, TranslationMetrics,
    TranslationJobStatus, ChunkStatus, ErrorSeverity
)

# Export all models
__all__ = [
    # Auth models
    "User", "Account", "UserBackground", "OnboardingResponse", "Session",
    "PasswordResetToken", "AnonymousSession", "ChatSession", "ChatMessage",
    "UserPreferences", "MessageVersion", "ChatFolder", "ChatTag", "MessageReaction",

    # Translation models
    "TranslationJob", "TranslationChunk", "TranslationError",
    "TranslationSession", "TranslationCache", "TranslationMetrics",
    "TranslationJobStatus", "ChunkStatus", "ErrorSeverity"
]