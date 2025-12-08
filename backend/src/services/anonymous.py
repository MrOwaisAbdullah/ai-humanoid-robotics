"""
Anonymous session tracking service.

This module provides utilities for managing anonymous user sessions
with message limits and migration to authenticated accounts.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.auth import AnonymousSession, ChatSession, ChatMessage, User


class AnonymousSessionService:
    """Service for managing anonymous user sessions."""

    MAX_MESSAGES = 3  # Maximum messages per anonymous session
    SESSION_DURATION_HOURS = 24  # Session duration in hours

    def __init__(self, db: Session):
        self.db = db

    def create_session(self) -> AnonymousSession:
        """Create a new anonymous session."""
        session = AnonymousSession(
            id=str(uuid.uuid4()),
            message_count=0,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[AnonymousSession]:
        """Get an anonymous session by ID."""
        return self.db.query(AnonymousSession).filter(
            AnonymousSession.id == session_id
        ).first()

    def update_activity(self, session_id: str) -> Optional[AnonymousSession]:
        """Update the last activity timestamp for a session."""
        session = self.get_session(session_id)
        if session:
            session.last_activity = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
        return session

    def increment_message_count(self, session_id: str) -> Optional[AnonymousSession]:
        """Increment message count for a session."""
        session = self.get_session(session_id)
        if session:
            session.message_count += 1
            session.last_activity = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
        return session

    def can_send_message(self, session_id: str) -> bool:
        """Check if a session can send more messages."""
        session = self.get_session(session_id)
        if not session:
            return False
        return session.message_count < self.MAX_MESSAGES

    def get_remaining_messages(self, session_id: str) -> int:
        """Get remaining messages for a session."""
        session = self.get_session(session_id)
        if not session:
            return self.MAX_MESSAGES
        remaining = self.MAX_MESSAGES - session.message_count
        return max(0, remaining)

    def is_session_expired(self, session_id: str) -> bool:
        """Check if a session is expired."""
        session = self.get_session(session_id)
        if not session:
            return True

        expiry_time = session.last_activity + timedelta(hours=self.SESSION_DURATION_HOURS)
        return datetime.utcnow() > expiry_time

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of deleted sessions."""
        expiry_threshold = datetime.utcnow() - timedelta(hours=self.SESSION_DURATION_HOURS)

        expired_sessions = self.db.query(AnonymousSession).filter(
            AnonymousSession.last_activity < expiry_threshold
        ).all()

        count = len(expired_sessions)

        for session in expired_sessions:
            self.db.delete(session)

        self.db.commit()
        return count

    def migrate_to_user(
        self,
        session_id: str,
        user: User,
        max_messages: int = 10
    ) -> Optional[ChatSession]:
        """
        Migrate anonymous session to authenticated user.

        Args:
            session_id: The anonymous session ID
            user: The user to migrate to
            max_messages: Maximum number of messages to migrate

        Returns:
            The new ChatSession for the user, or None if migration fails
        """
        # Get anonymous session
        anon_session = self.get_session(session_id)
        if not anon_session:
            return None

        # Get recent chat messages from anonymous session
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.anonymous_session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(max_messages).all()

        if not messages:
            return None

        # Create new chat session for user
        user_chat_session = ChatSession(
            user_id=user.id,
            title="New Chat",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(user_chat_session)
        self.db.flush()  # Get the ID without committing

        # Migrate messages in chronological order
        for message in reversed(messages):
            user_message = ChatMessage(
                chat_session_id=user_chat_session.id,
                role=message.role,
                content=message.content,
                metadata=message.metadata,
                created_at=message.created_at
            )
            self.db.add(user_message)

        # Delete anonymous session and messages
        self.db.delete(anon_session)
        for message in messages:
            self.db.delete(message)

        self.db.commit()
        self.db.refresh(user_chat_session)
        return user_chat_session

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for an anonymous session."""
        session = self.get_session(session_id)
        if not session:
            return {}

        return {
            "session_id": session.id,
            "message_count": session.message_count,
            "remaining_messages": self.get_remaining_messages(session_id),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_expired": self.is_session_expired(session_id),
            "can_send_message": self.can_send_message(session_id)
        }

    @staticmethod
    def generate_session_id() -> str:
        """Generate a new session ID."""
        return str(uuid.uuid4())