"""
CSRF Protection Middleware for Cookie-based Authentication

This middleware implements CSRF protection using the double-submit cookie pattern
to prevent Cross-Site Request Forgery attacks when using HTTP-only cookies.
"""

import secrets
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware for cookie-based authentication.

    Implements the double-submit cookie pattern:
    1. Generates CSRF token and stores in cookie
    2. Client must include token in header for state-changing requests
    3. Validates token on each protected request
    """

    def __init__(
        self,
        app: Callable,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        secure: bool = True,
        httponly: bool = False,
        samesite: str = "lax",
        max_age: int = 3600,  # 1 hour
        exempt_paths: list = None,
        safe_methods: list = None,
    ):
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite
        self.max_age = max_age
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
        self.safe_methods = safe_methods or ["GET", "HEAD", "OPTIONS", "TRACE"]

        # Store tokens for validation (in production, use Redis or database)
        self._tokens: dict[str, dict] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip CSRF for exempt paths and safe methods
        if (
            self._is_path_exempt(request) or
            request.method in self.safe_methods
        ):
            return await call_next(request)

        # Get or generate CSRF token
        csrf_token = self._get_or_generate_token(request)

        # Set CSRF cookie if not present
        if self.cookie_name not in request.cookies:
            response = await call_next(request)
            self._set_csrf_cookie(response, csrf_token)
            return response

        # Validate CSRF token for state-changing requests
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            await self._validate_csrf_token(request, csrf_token)

        # Add CSRF token to response headers for client access
        response = await call_next(request)
        response.headers[self.header_name] = csrf_token

        return response

    def _is_path_exempt(self, request: Request) -> bool:
        """Check if request path is exempt from CSRF protection."""
        for path in self.exempt_paths:
            if request.url.path.startswith(path):
                return True
        return False

    def _get_or_generate_token(self, request: Request) -> str:
        """Get existing CSRF token or generate new one."""
        # In production, store tokens in database/Redis with user_id
        # For now, use session-based storage
        session_id = getattr(request.state, "session_id", None)

        # Clean up expired tokens periodically
        self._cleanup_expired_tokens()

        if session_id and session_id in self._tokens:
            token_data = self._tokens[session_id]
            if token_data["expires"] > time.time():
                return token_data["token"]
            else:
                del self._tokens[session_id]

        # Generate new token
        token = secrets.token_urlsafe(32)
        expires = time.time() + self.max_age

        if session_id:
            self._tokens[session_id] = {
                "token": token,
                "expires": expires
            }

        return token

    def _set_csrf_cookie(self, response: Response, token: str):
        """Set CSRF token in response cookie."""
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.max_age,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
            path="/",
        )

    async def _validate_csrf_token(self, request: Request, expected_token: str):
        """Validate CSRF token from request header."""
        # Get token from header
        token = request.headers.get(self.header_name)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing",
                headers={"X-Error": "CSRF token required"},
            )

        # Validate token matches expected
        if not secrets.compare_digest(token, expected_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token",
                headers={"X-Error": "CSRF token validation failed"},
            )

        # Check token expiration if we have session info
        session_id = getattr(request.state, "session_id", None)
        if session_id and session_id in self._tokens:
            token_data = self._tokens[session_id]
            if token_data["expires"] <= time.time():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token expired",
                    headers={"X-Error": "CSRF token expired"},
                )

    def _cleanup_expired_tokens(self):
        """Clean up expired CSRF tokens."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            expired_tokens = [
                session_id for session_id, data in self._tokens.items()
                if data["expires"] <= now
            ]
            for session_id in expired_tokens:
                del self._tokens[session_id]
            self._last_cleanup = now


def get_csrf_token(request: Request) -> str:
    """
    Get CSRF token from request headers.

    Helper function for use in route handlers.
    """
    return request.headers.get("X-CSRF-Token")


def validate_csrf_token(request: Request, token: str) -> bool:
    """
    Validate CSRF token against expected token.

    Helper function for use in route handlers.
    """
    return request.headers.get("X-CSRF-Token") == token