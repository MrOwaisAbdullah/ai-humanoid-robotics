"""
Chat API routes with authentication support.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import uuid
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database.config import get_db
from src.models.auth import User, ChatSession, ChatMessage, AnonymousSession
from src.security.dependencies import get_current_user, get_current_user_or_anonymous
from src.services.message_editor import MessageEditorService
from rag.chat import ChatHandler

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Logger
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    context_window: Optional[int] = None
    k: Optional[int] = 5
    stream: bool = True


class ChatSessionResponse(BaseModel):
    """Chat session response model."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list = []


@router.post("/send")
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_anonymous)
):
    """Send a chat message with authentication support."""

    # Get the global chat_handler from main module
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from main import chat_handler

    if not chat_handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service not initialized"
        )

    # Check if user is anonymous and has exceeded limit
    if not current_user.is_authenticated:
        # Get or create anonymous session
        anon_session_id = request.headers.get("X-Anonymous-Session-ID")
        if anon_session_id:
            anon_session = db.query(AnonymousSession).filter(
                AnonymousSession.id == anon_session_id
            ).first()
        else:
            anon_session = None

        if not anon_session:
            # Create new anonymous session
            anon_session = AnonymousSession(
                id=str(uuid.uuid4()),
                message_count=0
            )
            db.add(anon_session)
            db.commit()

        # Check message limit
        if anon_session.message_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Anonymous users are limited to 3 messages. Please sign in to continue."
            )

        # Increment message count
        anon_session.message_count += 1
        anon_session.last_activity = datetime.utcnow()
        db.commit()

    # Get or create chat session
    session_id = chat_request.session_id
    chat_session = None

    if session_id:
        # Try to find existing session
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()

    if not chat_session:
        # Create new chat session
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=current_user.id if current_user.is_authenticated else None,
            anonymous_session_id=anon_session.id if not current_user.is_authenticated and anon_session else None,
            title="New Chat"
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

    # Save user message
    user_message = ChatMessage(
        chat_session_id=chat_session.id,
        role="user",
        content=chat_request.message,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()

    # Get session ID for context
    session_id_for_context = chat_request.session_id if chat_request.session_id else str(chat_session.id)

    if chat_request.stream:
        async def stream_and_persist():
            accumulated_content = ""
            try:
                async for chunk in chat_handler.stream_chat(
                    query=chat_request.message,
                    session_id=session_id_for_context,
                    k=chat_request.k,
                    context_window=chat_request.context_window
                ):
                    yield chunk
                    
                    # Parse chunk to accumulate content
                    if chunk.startswith("data: "):
                        try:
                            data_str = chunk[6:].strip()
                            if data_str != "[DONE]":
                                data = json.loads(data_str)
                                if data.get("type") == "chunk" and data.get("content"):
                                    accumulated_content += data["content"]
                                elif data.get("type") == "final" and data.get("answer"):
                                    accumulated_content = data["answer"]
                        except:
                            pass
                
                # Persist the accumulated message
                if accumulated_content:
                    ai_response = ChatMessage(
                        chat_session_id=chat_session.id,
                        role="assistant",
                        content=accumulated_content,
                        created_at=datetime.utcnow()
                    )
                    db.add(ai_response)
                    db.commit()
                    
                    # Update session timestamp
                    chat_session.updated_at = datetime.utcnow()
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Streaming failed: {str(e)}")
                # Optionally handle persistence of partial content or error state here

        return StreamingResponse(stream_and_persist(), media_type="text/event-stream")

    # Process the message through RAG system (Non-streaming)
    try:
        # Get response from chat handler
        response = await chat_handler.chat(
            query=chat_request.message,
            session_id=session_id_for_context,
            k=chat_request.k,
            context_window=chat_request.context_window
        )

        # Extract the response content
        ai_content = response.get("answer", "I'm sorry, I couldn't process your request.")

        # Create AI response
        ai_response = ChatMessage(
            chat_session_id=chat_session.id,
            role="assistant",
            content=ai_content,
            created_at=datetime.utcnow()
        )
        db.add(ai_response)
        db.commit()

    except Exception as e:
        # If RAG fails, provide a fallback response
        logger.error(f"RAG processing failed: {str(e)}")
        ai_response = ChatMessage(
            chat_session_id=chat_session.id,
            role="assistant",
            content="I'm having trouble accessing the book content right now. Please try again later.",
            created_at=datetime.utcnow()
        )
        db.add(ai_response)
        db.commit()

    # Update session timestamp
    chat_session.updated_at = datetime.utcnow()
    db.commit()

    # Get session messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_session_id == chat_session.id
    ).order_by(ChatMessage.created_at).all()

    return {
        "session_id": chat_session.id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "title": chat_session.title
    }


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's chat sessions."""
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()

    return [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "messages": []  # Messages loaded separately
        }
        for session in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session with messages."""
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Check session ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Get messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_session_id == session_id
    ).order_by(ChatMessage.created_at).all()

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.put("/sessions/{session_id}")
async def update_chat_session(
    session_id: str,
    session_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a chat session (e.g., title)."""
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Check session ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Update allowed fields
    if "title" in session_data:
        session.title = session_data["title"]

    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": []
    }


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session."""
    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Check session ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Delete session (messages will be deleted via cascade)
    db.delete(session)
    db.commit()

    return {"message": "Chat session deleted successfully"}


@router.get("/anonymous/session-info")
async def get_anonymous_session_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get information about an anonymous session for migration preview."""
    anonymous_session_id = request.headers.get("X-Anonymous-Session-ID")

    if not anonymous_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anonymous session ID required"
        )

    from src.services.session_migration import SessionMigrationService
    migration_service = SessionMigrationService(db)

    session_info = migration_service.get_anonymous_session_info(anonymous_session_id)

    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anonymous session not found"
        )

    return session_info


@router.put("/messages/{message_id}/edit")
@limiter.limit("30/minute")
async def edit_message(
    request: Request,
    message_id: str,
    edit_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit a chat message (only user messages within 15 minutes)."""

    # Validate edit data
    new_content = edit_data.get("content")
    if not new_content or not new_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is required and cannot be empty"
        )

    # Initialize the message editor service
    editor_service = MessageEditorService(db)

    # Check if message can be edited
    can_edit = editor_service.can_edit_message(message_id, str(current_user.id))
    if not can_edit["can_edit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=can_edit["reason"]
        )

    # Edit the message
    result = editor_service.edit_message(
        message_id=message_id,
        new_content=new_content.strip(),
        user_id=str(current_user.id),
        edit_reason=edit_data.get("reason")
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to edit message")
        )

    return result


@router.get("/messages/{message_id}/versions")
@limiter.limit("60/minute")
async def get_message_versions(
    request: Request,
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get version history of a message."""

    editor_service = MessageEditorService(db)
    result = editor_service.get_message_versions(message_id, str(current_user.id))

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Message not found")
        )

    return result


class ChatSearchRequest(BaseModel):
    """Chat search request model."""
    query: str
    session_id: Optional[str] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    message_type: Optional[str] = None  # "user", "assistant", or None for all


@router.post("/search")
@limiter.limit("100/minute")
async def search_chat_messages(
    request: Request,
    search_request: ChatSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search chat messages for authenticated users."""

    if not current_user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for searching messages"
        )

    try:
        # Build base query
        query = db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.user_id == str(current_user.id)
        )

        # Filter by session if specified
        if search_request.session_id:
            query = query.filter(ChatMessage.chat_session_id == search_request.session_id)

        # Filter by message type if specified
        if search_request.message_type:
            query = query.filter(ChatMessage.role == search_request.message_type)

        # Filter by date range if provided
        if search_request.date_from:
            try:
                date_from = datetime.fromisoformat(search_request.date_from.replace('Z', '+00:00'))
                query = query.filter(ChatMessage.created_at >= date_from)
            except ValueError:
                pass  # Invalid date format, ignore filter

        if search_request.date_to:
            try:
                date_to = datetime.fromisoformat(search_request.date_to.replace('Z', '+00:00'))
                query = query.filter(ChatMessage.created_at <= date_to)
            except ValueError:
                pass  # Invalid date format, ignore filter

        # Search in message content (case-insensitive)
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(ChatMessage.content.ilike(search_term))

        # Get total count
        total_count = query.count()

        # Apply pagination and ordering
        messages = query.order_by(ChatMessage.created_at.desc()).offset(
            search_request.offset or 0
        ).limit(search_request.limit or 50).all()

        # Format results
        results = []
        for message in messages:
            # Highlight matching text
            content = message.content
            if search_request.query:
                # Simple highlighting (in production, you might want more sophisticated highlighting)
                content = content.replace(
                    search_request.query,
                    f"**{search_request.query}**"
                )

            results.append({
                "id": message.id,
                "session_id": message.chat_session_id,
                "role": message.role,
                "content": content[:500] + ("..." if len(content) > 500 else ""),  # Preview
                "full_content": content,
                "created_at": message.created_at.isoformat(),
                "edited_at": message.edited_at.isoformat() if message.edited_at else None,
                "edit_count": message.edit_count or 0
            })

        return {
            "results": results,
            "total_count": total_count,
            "query": search_request.query,
            "limit": search_request.limit or 50,
            "offset": search_request.offset or 0
        }

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed. Please try again."
        )