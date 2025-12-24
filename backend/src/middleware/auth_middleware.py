"""
Advanced authentication middleware for FastAPI with SQLModel integration.
Handles JWT token verification, user authentication, and role-based access control.
"""

from typing import Optional, Callable
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..core.database import get_async_db
from ..core.security import verify_token, token_blacklist
from ..models.user import User, UserStatus
from ..services.auth_service import auth_service

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for token extraction
security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Advanced authentication middleware for FastAPI.

    This middleware:
    1. Extracts JWT tokens from Authorization headers
    2. Verifies token validity and checks blacklist
    3. Retrieves user information from database
    4. Adds user to request.state
    5. Handles role-based access control
    6. Provides rate limiting by user
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        """
        Initialize authentication middleware.

        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from authentication
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/verify-email",
            "/api/v1/auth/request-password-reset",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static",
            "/public",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add authentication.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware
        """
        # Skip authentication for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)

        try:
            # Extract and verify token
            user = await self._authenticate_request(request)

            # Add user to request state
            request.state.user = user
            request.state.authenticated = user is not None

            # Continue with request
            response = await call_next(request)

            # Add auth headers to response
            if user:
                response.headers["X-User-ID"] = str(user.id)
                response.headers["X-User-Role"] = user.role.value

            return response

        except HTTPException as e:
            # Return HTTP exception response
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            # Don't block request for middleware errors
            request.state.user = None
            request.state.authenticated = False
            return await call_next(request)

    def _should_exclude_path(self, path: str) -> bool:
        """
        Check if path should be excluded from authentication.

        Args:
            path: Request path

        Returns:
            True if path should be excluded
        """
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    async def _authenticate_request(self, request: Request) -> Optional[User]:
        """
        Authenticate request and return user.

        Args:
            request: FastAPI request

        Returns:
            Authenticated user or None

        Raises:
            HTTPException: If authentication fails
        """
        # Extract authorization header
        authorization = request.headers.get("authorization")
        if not authorization:
            return None

        # Extract token from Bearer scheme
        if not authorization.startswith("Bearer "):
            return None

        token = authorization[7:]  # Remove "Bearer " prefix

        # Check if token is blacklisted
        if token_blacklist.is_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token
        payload = verify_token(token, "access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        async with get_async_db() as db:
            user = await auth_service.get_user_by_id(int(user_id), db)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check user status
            if user.status == UserStatus.BANNED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account banned",
                )
            elif user.status == UserStatus.SUSPENDED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account suspended",
                )
            elif user.status == UserStatus.INACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account inactive",
                )

            return user


# ============================================
# Authentication Dependencies
# ============================================
async def get_current_user_optional(
    request: Request
) -> Optional[User]:
    """
    Get current user from request state (optional).

    Args:
        request: FastAPI request

    Returns:
        Current user or None
    """
    return getattr(request.state, 'user', None)


async def get_current_user_required(
    request: Request
) -> User:
    """
    Get current user from request state (required).

    Args:
        request: FastAPI request

    Returns:
        Current user

    Raises:
        HTTPException: If user not authenticated
    """
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user_required)
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from dependency

    Returns:
        Active user

    Raises:
        HTTPException: If user not active
    """
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current verified user.

    Args:
        current_user: Current user from dependency

    Returns:
        Verified user

    Raises:
        HTTPException: If user not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current user from dependency

    Returns:
        Admin user

    Raises:
        HTTPException: If user not admin
    """
    if current_user.role.value not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_super_admin_user(
    current_user: User = Depends(get_current_admin_user)
) -> User:
    """
    Get current super admin user.

    Args:
        current_user: Current user from dependency

    Returns:
        Super admin user

    Raises:
        HTTPException: If user not super admin
    """
    if current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


# ============================================
# Permission Checking Utilities
# ============================================
def has_permission(user: User, permission: str) -> bool:
    """
    Check if user has specific permission.

    Args:
        user: User to check
        permission: Permission string

    Returns:
        True if user has permission
    """
    # Super admins have all permissions
    if user.role.value == "super_admin":
        return True

    # Get user permissions based on role
    user_permissions = get_role_permissions(user.role.value)
    return permission in user_permissions


def has_any_permission(user: User, permissions: list) -> bool:
    """
    Check if user has any of the specified permissions.

    Args:
        user: User to check
        permissions: List of permissions

    Returns:
        True if user has any permission
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: list) -> bool:
    """
    Check if user has all specified permissions.

    Args:
        user: User to check
        permissions: List of permissions

    Returns:
        True if user has all permissions
    """
    return all(has_permission(user, perm) for perm in permissions)


def get_role_permissions(role: str) -> list:
    """
    Get permissions for a specific role.

    Args:
        role: User role

    Returns:
        List of permissions
    """
    role_permissions = {
        "user": [
            "read:own_profile",
            "update:own_profile",
            "create:chat",
            "read:own_chat",
            "update:own_chat",
            "delete:own_chat",
            "read:own_analytics",
        ],
        "moderator": [
            "read:own_profile",
            "update:own_profile",
            "create:chat",
            "read:own_chat",
            "update:own_chat",
            "delete:own_chat",
            "read:own_analytics",
            "read:all_chat",
            "moderate:content",
            "read:public_analytics",
            "manage:reports",
        ],
        "admin": [
            "read:own_profile",
            "update:own_profile",
            "create:chat",
            "read:own_chat",
            "update:own_chat",
            "delete:own_chat",
            "read:own_analytics",
            "read:all_chat",
            "moderate:content",
            "read:public_analytics",
            "manage:reports",
            "read:all_users",
            "update:all_users",
            "ban:users",
            "read:system_config",
            "update:system_config",
            "read:all_analytics",
            "manage:oauth",
        ],
        "super_admin": ["*"],  # All permissions
    }

    return role_permissions.get(role, [])


# ============================================
# Permission Dependencies
# ============================================
def require_permissions(permissions: list, require_all: bool = True):
    """
    Create dependency to require specific permissions.

    Args:
        permissions: List of required permissions
        require_all: Whether user must have all permissions (True) or any (False)

    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_verified_user)
    ) -> User:
        """Check if user has required permissions."""
        if require_all:
            if not has_all_permissions(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permissions}"
                )
        else:
            if not has_any_permission(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required any of: {permissions}"
                )

        return current_user

    return permission_checker


def require_permission(permission: str):
    """Create dependency to require a single permission."""
    return require_permissions([permission])


# Common permission dependencies
require_profile_read = require_permission("read:own_profile")
require_profile_update = require_permission("update:own_profile")
require_chat_create = require_permission("create:chat")
require_chat_read = require_permission("read:own_chat")
require_chat_moderate = require_permissions(["read:all_chat", "moderate:content"], require_all=False)
require_user_management = require_permissions(["read:all_users", "update:all_users"])
require_system_config = require_permissions(["read:system_config", "update:system_config"])


# ============================================
# Rate Limiting by User
# ============================================
async def get_rate_limit_key(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> str:
    """
    Get rate limit key for current user.

    Args:
        request: FastAPI request
        current_user: Current user (optional)

    Returns:
        Rate limit key string
    """
    if current_user:
        return f"user:{current_user.id}"
    else:
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        return f"ip:{request.client.host}"


# ============================================
# Authentication Utilities
# ============================================
def is_authenticated(request: Request) -> bool:
    """
    Check if request is authenticated.

    Args:
        request: FastAPI request

    Returns:
        True if authenticated
    """
    return getattr(request.state, 'authenticated', False)


def get_user_id(request: Request) -> Optional[int]:
    """
    Get user ID from request.

    Args:
        request: FastAPI request

    Returns:
        User ID or None
    """
    user = getattr(request.state, 'user', None)
    return user.id if user else None


def get_user_role(request: Request) -> Optional[str]:
    """
    Get user role from request.

    Args:
        request: FastAPI request

    Returns:
        User role or None
    """
    user = getattr(request.state, 'user', None)
    return user.role.value if user else None


# ============================================
# Token Management
# ============================================
async def revoke_token(token: str):
    """
    Revoke a token (add to blacklist).

    Args:
        token: Token to revoke
    """
    token_blacklist.add_token(token)


def is_token_revoked(token: str) -> bool:
    """
    Check if token is revoked.

    Args:
        token: Token to check

    Returns:
        True if token is revoked
    """
    return token_blacklist.is_blacklisted(token)