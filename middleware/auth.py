"""
Authentication middleware for request handling.

This middleware handles session validation, anonymous session tracking,
and session expiration checks.
"""

import uuid
from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from database.config import SessionLocal
from src.models.auth import Session as AuthSession
from auth.auth import verify_token


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for request processing.

    Handles:
    - Session validation for authenticated requests
    - Anonymous session tracking
    - Session expiration checks
    - User attachment to request state
    """

    def __init__(
        self,
        app,
        anonymous_limit: int = 3,
        exempt_paths: list = None,
        anonymous_header: str = "X-Anonymous-Session-ID",
    ):
        super().__init__(app)
        self.anonymous_limit = anonymous_limit
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json", "/auth/login"]
        self.anonymous_header = anonymous_header

        # In-memory storage for anonymous sessions
        # In production, use Redis or database
        self._anonymous_sessions: dict[str, dict] = {}
        self._user_sessions: dict[str, dict] = {}

    async def dispatch(self, request: Request, call_next):
        # Skip middleware for exempt paths
        if self._is_path_exempt(request):
            return await call_next(request)

        # Try to authenticate with JWT token
        user = await self._authenticate_user(request)
        if user:
            request.state.user = user
            request.state.authenticated = True
            
            # Create a DB session to get user session ID
            db = SessionLocal()
            try:
                request.state.session_id = await self._get_user_session_id(user["id"], db)
            finally:
                db.close()
                
            return await call_next(request)

        # Handle anonymous access
        await self._handle_anonymous_request(request)
        return await call_next(request)

    def _is_path_exempt(self, request: Request) -> bool:
        """Check if request path is exempt from authentication."""
        for path in self.exempt_paths:
            if request.url.path.startswith(path):
                return True
        return False

    async def _authenticate_user(self, request: Request) -> Optional[dict]:
        """
        Authenticate user from JWT token in cookie or header.
        """
        token = request.cookies.get("access_token")
        
        # Check header if no cookie
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return None

        payload = verify_token(token)
        if not payload:
            return None

        # In a real implementation, fetch user from database
        # For now, return payload as user representation
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name", ""),
        }

    async def _get_user_session_id(self, user_id: str, db: Session) -> Optional[str]:
        """Get active session ID for user."""
        session = db.query(AuthSession).filter(
            AuthSession.user_id == user_id,
            AuthSession.expires_at > datetime.utcnow()
        ).first()
        return session.id if session else None

    async def _handle_anonymous_request(self, request: Request):
        """Handle requests from anonymous users."""
        # Get or create anonymous session
        session_id = request.headers.get(self.anonymous_header)

        if not session_id:
            session_id = str(uuid.uuid4())
            self._anonymous_sessions[session_id] = {
                "message_count": 0,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
            }

        # Check message limit
        session_data = self._anonymous_sessions.get(session_id, {})
        if session_data.get("message_count", 0) >= self.anonymous_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Anonymous limit of {self.anonymous_limit} messages exceeded. Please sign in to continue.",
                headers={
                    "X-Anonymous-Limit-Reached": "true",
                    "X-Session-ID": session_id,
                },
            )

        # Attach anonymous session to request
        request.state.anonymous = True
        request.state.session_id = session_id
        request.state.authenticated = False

        # Update last activity
        session_data["last_activity"] = datetime.utcnow()
        self._anonymous_sessions[session_id] = session_data

    async def increment_message_count(self, session_id: str):
        """Increment message count for anonymous session."""
        if session_id in self._anonymous_sessions:
            self._anonymous_sessions[session_id]["message_count"] += 1

    def get_anonymous_session(self, session_id: str) -> Optional[dict]:
        """Get anonymous session data."""
        return self._anonymous_sessions.get(session_id)

    def cleanup_expired_sessions(self):
        """Clean up expired anonymous sessions."""
        now = datetime.utcnow()
        expired = [
            session_id for session_id, data in self._anonymous_sessions.items()
            if (now - data["last_activity"]).seconds > 3600  # 1 hour
        ]
        for session_id in expired:
            del self._anonymous_sessions[session_id]


def get_current_session(request: Request) -> Optional[str]:
    """Get current session ID from request state."""
    return getattr(request.state, "session_id", None)


def is_authenticated(request: Request) -> bool:
    """Check if request is from authenticated user."""
    return getattr(request.state, "authenticated", False)


def is_anonymous(request: Request) -> bool:
    """Check if request is from anonymous user."""
    return getattr(request.state, "anonymous", False)


def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from request state."""
    return getattr(request.state, "user", None)


async def check_session_validity(session_id: str, db: Session) -> bool:
    """
    Check if session is still valid (not expired).
    """
    session = db.query(AuthSession).filter(
        AuthSession.token == session_id
    ).first()

    if not session:
        return False

    # Check if session has expired
    if session.expires_at <= datetime.utcnow():
        # Delete expired session
        db.delete(session)
        db.commit()
        return False

    return True