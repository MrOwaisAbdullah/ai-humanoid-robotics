"""
Conversation context management for RAG system.

Handles session management, conversation history, and context window optimization.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from .models import Message, MessageRole, ConversationContext
import tiktoken

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages conversation context and session state."""

    def __init__(
        self,
        max_context_messages: int = 3,
        max_session_duration: int = 3600,  # 1 hour
        max_sessions: int = 1000
    ):
        self.max_context_messages = max_context_messages
        self.max_session_duration = max_session_duration
        self.max_sessions = max_sessions
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # In-memory session store (for production, use Redis or database)
        self.sessions: Dict[str, ConversationContext] = {}

        # System message
        self.system_message = Message(
            id="system",
            role=MessageRole.SYSTEM,
            content=(
                "You are an AI assistant for the book 'Physical AI and Humanoid Robotics'. "
                "This book covers Physical AI systems, humanoid robots, robot sensing, "
                "actuation mechanisms, and the convergence of AI with robotics. "
                "Provide accurate, detailed answers based on the book content. "
                "Always cite your sources using [Chapter - Section] format. "
                "If asked about topics outside this book, respond: 'I can only provide information "
                "about Physical AI, humanoid robots, and the specific topics covered in this book.' "
                "If the context doesn't contain relevant information, say so clearly."
            ),
            token_count=0
        )
        self.system_message.token_count = self.count_tokens(self.system_message.content)

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        Get existing session or create a new one.

        Args:
            session_id: Optional existing session ID

        Returns:
            Session ID (new or existing)
        """
        if session_id and session_id in self.sessions:
            # Update last activity
            self.sessions[session_id].last_activity = datetime.utcnow()
            return session_id

        # Create new session
        import uuid
        new_session_id = str(uuid.uuid4())

        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            self._cleanup_old_sessions()

        # Create new context
        self.sessions[new_session_id] = ConversationContext(
            session_id=new_session_id,
            max_messages=self.max_context_messages,
            messages=[self.system_message],
            total_tokens=self.system_message.token_count
        )

        return new_session_id

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        citations: Optional[List[str]] = None
    ) -> Message:
        """
        Add a message to the conversation context.

        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
            citations: Optional list of citation IDs

        Returns:
            Created message
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        context = self.sessions[session_id]

        # Create message
        message = Message(
            id=str(datetime.utcnow().timestamp()),
            role=role,
            content=content,
            token_count=self.count_tokens(content),
            citations=citations or []
        )

        # Add to context
        context.add_message(message)

        return message

    def get_context_messages(
        self,
        session_id: str,
        max_tokens: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages for context window.

        Args:
            session_id: Session identifier
            max_tokens: Maximum tokens to include

        Returns:
            List of messages for context
        """
        if session_id not in self.sessions:
            return []

        context = self.sessions[session_id]
        messages = context.get_context_messages()

        # Apply token limit if specified
        if max_tokens:
            messages = self._apply_token_limit(messages, max_tokens)

        return messages

    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get full conversation history.

        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages

        Returns:
            List of all messages in conversation
        """
        if session_id not in self.sessions:
            return []

        messages = self.sessions[session_id].messages

        if limit:
            return messages[-limit:]

        return messages

    def clear_session(self, session_id: str) -> bool:
        """
        Clear a conversation session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was cleared
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        if session_id not in self.sessions:
            return None

        context = self.sessions[session_id]

        return {
            "session_id": session_id,
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "message_count": len(context.messages),
            "total_tokens": context.total_tokens,
            "duration_seconds": (datetime.utcnow() - context.created_at).total_seconds()
        }

    def get_all_sessions_info(self) -> List[Dict[str, Any]]:
        """Get information about all active sessions."""
        return [
            self.get_session_info(session_id)
            for session_id in self.sessions.keys()
        ]

    def _cleanup_old_sessions(self):
        """Remove sessions that have expired."""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, context in self.sessions.items():
            # Check if session has expired
            if (current_time - context.last_activity).total_seconds() > self.max_session_duration:
                expired_sessions.append(session_id)

        # Remove expired sessions
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Removed expired session: {session_id}")

        # If still too many sessions, remove oldest ones
        if len(self.sessions) >= self.max_sessions:
            # Sort by last activity and remove oldest
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_activity
            )

            sessions_to_remove = len(self.sessions) - self.max_sessions + 1
            for i in range(sessions_to_remove):
                session_id = sorted_sessions[i][0]
                del self.sessions[session_id]
                logger.info(f"Removed old session: {session_id}")

    def _apply_token_limit(
        self,
        messages: List[Message],
        max_tokens: int
    ) -> List[Message]:
        """
        Apply token limit to messages, keeping the most recent ones.

        Args:
            messages: List of messages
            max_tokens: Maximum tokens to include

        Returns:
            Filtered list of messages
        """
        # Always include system message if present
        system_msg = None
        if messages and messages[0].role == MessageRole.SYSTEM:
            system_msg = messages[0]
            messages = messages[1:]

        # Work backwards from most recent messages
        selected_messages = []
        current_tokens = 0

        for message in reversed(messages):
            if current_tokens + message.token_count > max_tokens:
                break

            selected_messages.append(message)
            current_tokens += message.token_count

        # Reverse to maintain order
        selected_messages.reverse()

        # Add system message back at the beginning
        if system_msg:
            selected_messages.insert(0, system_msg)

        return selected_messages

    def optimize_context_window(
        self,
        session_id: str,
        target_tokens: int = 4000
    ) -> List[Dict[str, str]]:
        """
        Optimize context window for OpenAI API.

        Returns messages formatted for OpenAI API.
        """
        messages = self.get_context_messages(session_id, target_tokens)

        # Format for OpenAI
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        return formatted_messages

    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session data for backup or analysis."""
        if session_id not in self.sessions:
            return None

        context = self.sessions[session_id]

        return {
            "session_id": session_id,
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "messages": [msg.model_dump() for msg in context.messages],
            "total_tokens": context.total_tokens,
            "metadata": context.metadata
        }

    def import_session(self, session_data: Dict[str, Any]) -> bool:
        """Import session data from backup."""
        try:
            session_id = session_data["session_id"]

            # Create messages
            messages = []
            for msg_data in session_data["messages"]:
                message = Message(**msg_data)
                messages.append(message)

            # Create context
            context = ConversationContext(
                session_id=session_id,
                max_messages=self.max_context_messages,
                messages=messages,
                total_tokens=session_data["total_tokens"],
                created_at=datetime.fromisoformat(session_data["created_at"]),
                last_activity=datetime.fromisoformat(session_data["last_activity"]),
                metadata=session_data.get("metadata", {})
            )

            self.sessions[session_id] = context
            logger.info(f"Imported session: {session_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to import session: {str(e)}")
            return False

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        total_messages = sum(len(ctx.messages) for ctx in self.sessions.values())
        total_tokens = sum(ctx.total_tokens for ctx in self.sessions.values())

        return {
            "active_sessions": len(self.sessions),
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "max_sessions": self.max_sessions,
            "max_context_messages": self.max_context_messages
        }