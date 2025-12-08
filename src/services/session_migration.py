"""
Service for handling migration of anonymous chat sessions to authenticated users.

This module provides functionality to migrate chat sessions, messages,
and related data from anonymous users to authenticated users when they sign up or log in.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta

from src.models.auth import User, ChatSession, ChatMessage, AnonymousSession
from src.database.config import get_db

logger = logging.getLogger(__name__)


class SessionMigrationService:
    """Service for migrating anonymous sessions to authenticated users."""

    def __init__(self, db: Session):
        self.db = db

    def migrate_anonymous_session(
        self,
        anonymous_session_id: str,
        authenticated_user_id: str
    ) -> Dict[str, Any]:
        """
        Migrate all chat sessions and messages from an anonymous session to an authenticated user.

        Args:
            anonymous_session_id: ID of the anonymous session
            authenticated_user_id: ID of the authenticated user

        Returns:
            Dictionary containing migration results including:
            - migrated_sessions_count: Number of sessions migrated
            - migrated_messages_count: Number of messages migrated
            - session_ids: List of migrated session IDs
        """
        try:
            # Get the anonymous session record
            anon_session = self.db.query(AnonymousSession).filter(
                AnonymousSession.id == anonymous_session_id
            ).first()

            if not anon_session:
                logger.warning(f"Anonymous session not found: {anonymous_session_id}")
                return {
                    "success": False,
                    "error": "Anonymous session not found",
                    "migrated_sessions_count": 0,
                    "migrated_messages_count": 0,
                    "session_ids": []
                }

            # Get all chat sessions associated with this anonymous session
            chat_sessions = self.db.query(ChatSession).filter(
                ChatSession.anonymous_session_id == anonymous_session_id
            ).all()

            if not chat_sessions:
                logger.info(f"No chat sessions found for anonymous session: {anonymous_session_id}")
                return {
                    "success": True,
                    "migrated_sessions_count": 0,
                    "migrated_messages_count": 0,
                    "session_ids": []
                }

            migrated_sessions = []
            total_messages = 0

            for session in chat_sessions:
                # Update the session to associate with the authenticated user
                session.user_id = authenticated_user_id
                session.anonymous_session_id = None

                # Update all messages in this session
                messages = self.db.query(ChatMessage).filter(
                    ChatMessage.chat_session_id == session.id
                ).all()

                for message in messages:
                    # Ensure message is properly linked
                    message.chat_session_id = session.id

                total_messages += len(messages)
                migrated_sessions.append(session.id)

                # Update session title if it's the default
                if session.title == "New Chat":
                    session.title = f"Chat from {datetime.utcnow().strftime('%Y-%m-%d')}"

            # Commit the changes
            self.db.commit()

            # Update the anonymous session to mark it as migrated
            anon_session.migrated_at = datetime.utcnow()
            anon_session.migrated_to_user_id = authenticated_user_id
            self.db.commit()

            logger.info(
                f"Successfully migrated {len(chat_sessions)} sessions "
                f"with {total_messages} messages from anonymous session "
                f"{anonymous_session_id} to user {authenticated_user_id}"
            )

            return {
                "success": True,
                "migrated_sessions_count": len(chat_sessions),
                "migrated_messages_count": total_messages,
                "session_ids": migrated_sessions
            }

        except Exception as e:
            logger.error(
                f"Failed to migrate anonymous session {anonymous_session_id}: {str(e)}",
                exc_info=True
            )
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "migrated_sessions_count": 0,
                "migrated_messages_count": 0,
                "session_ids": []
            }

    def get_anonymous_session_info(self, anonymous_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an anonymous session including session count and message count.

        Args:
            anonymous_session_id: ID of the anonymous session

        Returns:
            Dictionary with session info or None if not found
        """
        try:
            anon_session = self.db.query(AnonymousSession).filter(
                AnonymousSession.id == anonymous_session_id
            ).first()

            if not anon_session:
                return None

            # Count chat sessions
            session_count = self.db.query(ChatSession).filter(
                ChatSession.anonymous_session_id == anonymous_session_id
            ).count()

            # Count total messages
            message_count = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.anonymous_session_id == anonymous_session_id
            ).count()

            return {
                "id": anon_session.id,
                "message_count": anon_session.message_count,
                "chat_sessions_count": session_count,
                "total_messages_count": message_count,
                "last_activity": anon_session.last_activity,
                "created_at": anon_session.created_at,
                "migrated_at": anon_session.migrated_at,
                "migrated_to_user_id": anon_session.migrated_to_user_id
            }

        except Exception as e:
            logger.error(f"Failed to get anonymous session info: {str(e)}")
            return None

    def cleanup_expired_anonymous_sessions(self, days_old: int = 30) -> int:
        """
        Clean up expired anonymous sessions that haven't been migrated.

        Args:
            days_old: Delete sessions older than this many days

        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Get expired anonymous sessions that haven't been migrated
            expired_sessions = self.db.query(AnonymousSession).filter(
                and_(
                    AnonymousSession.last_activity < cutoff_date,
                    AnonymousSession.migrated_at.is_(None)
                )
            ).all()

            # Delete associated chat sessions and messages
            deleted_count = 0
            for anon_session in expired_sessions:
                # Get and delete chat sessions
                chat_sessions = self.db.query(ChatSession).filter(
                    ChatSession.anonymous_session_id == anon_session.id
                ).all()

                for session in chat_sessions:
                    # Messages will be deleted via cascade
                    self.db.delete(session)
                    deleted_count += 1

                # Delete the anonymous session
                self.db.delete(anon_session)

            self.db.commit()

            logger.info(f"Cleaned up {len(expired_sessions)} expired anonymous sessions "
                       f"with {deleted_count} chat sessions")

            return len(expired_sessions)

        except Exception as e:
            logger.error(f"Failed to cleanup expired anonymous sessions: {str(e)}")
            self.db.rollback()
            return 0


def migrate_anonymous_session_on_auth(
    anonymous_session_id: str,
    authenticated_user_id: str
) -> Dict[str, Any]:
    """
    Convenience function to migrate an anonymous session when a user authenticates.

    This is typically called during login or registration flow.

    Args:
        anonymous_session_id: ID from X-Anonymous-Session-ID header
        authenticated_user_id: ID of the newly authenticated user

    Returns:
        Migration result dictionary
    """
    db = next(get_db())
    try:
        service = SessionMigrationService(db)
        return service.migrate_anonymous_session(anonymous_session_id, authenticated_user_id)
    finally:
        db.close()


def get_anonymous_session_for_migration(anonymous_session_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get anonymous session info for migration preview.

    Args:
        anonymous_session_id: ID from X-Anonymous-Session-ID header

    Returns:
        Session info dictionary or None
    """
    db = next(get_db())
    try:
        service = SessionMigrationService(db)
        return service.get_anonymous_session_info(anonymous_session_id)
    finally:
        db.close()