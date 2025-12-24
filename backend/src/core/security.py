"""
Security utilities for authentication, password hashing, and JWT token management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import secrets
import hashlib
import re
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt

from .config import settings

# ============================================
# Password Hashing Configuration
# ============================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Higher rounds for better security
)


# ============================================
# JWT Token Management
# ============================================
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data to encode
        expires_delta: Custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token.

    Args:
        data: Payload data to encode
        expires_delta: Custom expiration time

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expire_days)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Dict: Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        # Check token type
        if payload.get("type") != token_type:
            return None

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            return None

        return payload

    except JWTError:
        return None


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token without verification (for debugging).

    Args:
        token: JWT token to decode

    Returns:
        Dict: Decoded payload or None if invalid format
    """
    try:
        # Remove Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        # Split token parts
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (base64url)
        import base64
        import json

        # Add padding if needed
        payload_b64 = parts[1]
        padding_needed = 4 - len(payload_b64) % 4
        if padding_needed:
            payload_b64 += "=" * padding_needed

        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode())

        return payload

    except Exception:
        return None


# ============================================
# Password Management
# ============================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Dict[str, Union[bool, str]]:
    """
    Validate password strength according to requirements.

    Args:
        password: Password to validate

    Returns:
        Dict: Validation result with is_valid and message
    """
    errors = []

    # Length check
    if len(password) < settings.password_min_length:
        errors.append(f"Password must be at least {settings.password_min_length} characters long")

    if len(password) > 128:
        errors.append("Password must be less than 128 characters long")

    # Character requirements
    if settings.password_require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    if settings.password_require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    if settings.password_require_numbers and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    if settings.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    # Common password patterns
    if password.lower() in ['password', '123456', 'qwerty', 'admin', 'letmein']:
        errors.append("Password is too common and not allowed")

    # Check for sequential characters
    if re.search(r'(012|123|234|345|456|567|678|789)', password):
        errors.append("Password should not contain sequential numbers")

    is_valid = len(errors) == 0
    message = "Password is valid" if is_valid else "; ".join(errors)

    return {
        "is_valid": is_valid,
        "message": message,
        "errors": errors
    }


# ============================================
# Token Generation for Verification
# ============================================
def generate_verification_token() -> str:
    """
    Generate a secure verification token for email verification.

    Returns:
        str: Secure random token
    """
    return secrets.urlsafe_b64encode(secrets.token_bytes(32)).decode()


def generate_password_reset_token() -> str:
    """
    Generate a secure password reset token.

    Returns:
        str: Secure random token
    """
    return secrets.urlsafe_b64encode(secrets.token_bytes(32)).decode()


def generate_session_token() -> str:
    """
    Generate a secure session token.

    Returns:
        str: Secure random token
    """
    return secrets.token_urlsafe(32)


# ============================================
# Hash Utilities
# ============================================
def create_email_hash(email: str) -> str:
    """
    Create a consistent hash for email (for gravatar, etc.).

    Args:
        email: Email address to hash

    Returns:
        str: MD5 hash of lowercase email
    """
    return hashlib.md5(email.lower().encode()).hexdigest()


def create_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        str: API key with prefix
    """
    token = secrets.token_urlsafe(32)
    return f"ab_{token}"  # ab = ai-book


# ============================================
# Security Headers
# ============================================
def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP responses.

    Returns:
        Dict: Security headers
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if settings.is_production else "",
    }


# ============================================
# Rate Limiting
# ============================================
def get_client_identifier(request) -> str:
    """
    Get a consistent client identifier for rate limiting.

    Args:
        request: FastAPI request object

    Returns:
        str: Client identifier (IP address or user ID)
    """
    # Try to get user ID from request state (if authenticated)
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP in the chain
        return f"ip:{forwarded_for.split(',')[0].strip()}"

    return f"ip:{request.client.host}"


# ============================================
# Input Validation and Sanitization
# ============================================
def sanitize_email(email: str) -> str:
    """
    Sanitize email address.

    Args:
        email: Email address to sanitize

    Returns:
        str: Sanitized email
    """
    return email.strip().lower()


def sanitize_username(username: str) -> str:
    """
    Sanitize username.

    Args:
        username: Username to sanitize

    Returns:
        str: Sanitized username
    """
    # Remove special characters, keep alphanumeric and underscore
    return re.sub(r'[^a-zA-Z0-9_]', '', username.strip())


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email to validate

    Returns:
        bool: True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# ============================================
# Token Blacklisting (Optional Enhancement)
# ============================================
class TokenBlacklist:
    """Simple in-memory token blacklist (for development)."""

    def __init__(self):
        self.blacklisted_tokens = set()

    def add_token(self, token: str):
        """Add token to blacklist."""
        self.blacklisted_tokens.add(token)

    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        return token in self.blacklisted_tokens

    def remove_token(self, token: str):
        """Remove token from blacklist."""
        self.blacklisted_tokens.discard(token)

    def clear_expired(self):
        """Clear expired tokens (requires decoding each token)."""
        expired = []
        for token in self.blacklisted_tokens:
            payload = decode_token_without_verification(token)
            if payload and payload.get('exp', 0) < datetime.utcnow().timestamp():
                expired.append(token)

        for token in expired:
            self.blacklisted_tokens.remove(token)


# Global token blacklist instance
token_blacklist = TokenBlacklist()