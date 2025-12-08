"""
Service for editing chat messages with version tracking.

This module provides functionality to edit messages while maintaining
a complete version history for audit and rollback purposes.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.models.auth import ChatMessage, MessageVersion
from src.database.config import get_db

logger = logging.getLogger(__name__)


class MessageEditorService:
    """Service for editing messages with version tracking."""

    def __init__(self, db: Session):
        self.db = db

    def can_edit_message(
        self,
        message_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Check if a message can be edited by the user.

        Args:
            message_id: ID of the message to check
            user_id: ID of the user attempting to edit

        Returns:
            Dictionary with can_edit status and reason if not editable
        """
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()

        if not message:
            return {
                "can_edit": False,
                "reason": "Message not found"
            }

        # Check if message belongs to the user
        if message.chat_session.user_id != user_id:
            return {
                "can_edit": False,
                "reason": "You can only edit your own messages"
            }

        # Only user messages can be edited
        if message.role != "user":
            return {
                "can_edit": False,
                "reason": "Only user messages can be edited"
            }

        # Check if message is within the editable time window (15 minutes)
        edit_window = timedelta(minutes=15)
        if datetime.utcnow() - message.created_at > edit_window:
            return {
                "can_edit": False,
                "reason": "Messages can only be edited within 15 minutes of sending"
            }

        return {
            "can_edit": True,
            "reason": None
        }

    def edit_message(
        self,
        message_id: str,
        new_content: str,
        user_id: str,
        edit_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Edit a message and create a version record.

        Args:
            message_id: ID of the message to edit
            new_content: New content for the message
            user_id: ID of the user editing the message
            edit_reason: Optional reason for the edit

        Returns:
            Dictionary with edit result and updated message
        """
        # Check if message can be edited
        can_edit_result = self.can_edit_message(message_id, user_id)
        if not can_edit_result["can_edit"]:
            return {
                "success": False,
                "error": can_edit_result["reason"]
            }

        try:
            # Get the message
            message = self.db.query(ChatMessage).filter(
                ChatMessage.id == message_id
            ).first()

            # No changes needed
            if message.content == new_content:
                return {
                    "success": True,
                    "message": "No changes made",
                    "edited_message": self._message_to_dict(message)
                }

            # Create version record before editing
            version = MessageVersion(
                message_id=message.id,
                version_number=message.edit_count + 1,
                content=message.content,
                edit_reason=edit_reason
            )
            self.db.add(version)

            # Update the message
            message.content = new_content
            message.edited_at = datetime.utcnow()
            message.edit_count += 1
            message.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Message {message_id} edited by user {user_id}")

            return {
                "success": True,
                "message": "Message edited successfully",
                "edited_message": self._message_to_dict(message)
            }

        except Exception as e:
            logger.error(f"Failed to edit message {message_id}: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": "Failed to edit message"
            }

    def get_message_versions(
        self,
        message_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get all versions of a message.

        Args:
            message_id: ID of the message
            user_id: ID of the user requesting versions

        Returns:
            Dictionary with version history
        """
        # Verify ownership
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()

        if not message or message.chat_session.user_id != user_id:
            return {
                "success": False,
                "error": "Message not found or access denied"
            }

        # Get all versions including current
        versions = self.db.query(MessageVersion).filter(
            MessageVersion.message_id == message_id
        ).order_by(MessageVersion.version_number.desc()).all()

        version_history = []

        # Add current version
        version_history.append({
            "version": message.edit_count + 1,
            "content": message.content,
            "created_at": message.edited_at.isoformat() if message.edited_at else message.created_at.isoformat(),
            "is_current": True
        })

        # Add historical versions
        for version in versions:
            version_history.append({
                "version": version.version_number,
                "content": version.content,
                "created_at": version.created_at.isoformat(),
                "edit_reason": version.edit_reason,
                "is_current": False
            })

        return {
            "success": True,
            "versions": version_history
        }

    def _message_to_dict(self, message: ChatMessage) -> Dict[str, Any]:
        """Convert message model to dictionary."""
        return {
            "id": message.id,
            "content": message.content,
            "role": message.role,
            "created_at": message.created_at.isoformat(),
            "edited_at": message.edited_at.isoformat() if message.edited_at else None,
            "edit_count": message.edit_count
        }


def edit_message(
    message_id: str,
    new_content: str,
    user_id: str,
    edit_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to edit a message.

    Args:
        message_id: ID of the message to edit
        new_content: New content for the message
        user_id: ID of the user editing the message
        edit_reason: Optional reason for the edit

    Returns:
        Edit result dictionary
    """
    db = next(get_db())
    try:
        service = MessageEditorService(db)
        return service.edit_message(message_id, new_content, user_id, edit_reason)
    finally:
        db.close()


def get_message_versions(message_id: str, user_id: str) -> Dict[str, Any]:
    """
    Convenience function to get message versions.

    Args:
        message_id: ID of the message
        user_id: ID of the user requesting versions

    Returns:
        Version history dictionary
    """
    db = next(get_db())
    try:
        service = MessageEditorService(db)
        return service.get_message_versions(message_id, user_id)
    finally:
        db.close()