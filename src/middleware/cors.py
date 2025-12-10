"""
CORS middleware configuration for frontend-backend communication.

Provides configurable Cross-Origin Resource Sharing middleware.
"""

import os
from typing import List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint


class CustomCORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with additional security features."""

    def __init__(
        self,
        app: FastAPI,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        expose_headers: List[str] = None,
        allow_credentials: bool = True,
        max_age: int = 86400,  # 24 hours
        strict_mode: bool = False
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or self._get_default_origins()
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = allow_headers or ["*"]
        self.expose_headers = expose_headers or []
        self.allow_credentials = allow_credentials
        self.max_age = max_age
        self.strict_mode = strict_mode

        # Apply FastAPI's CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.allow_origins,
            allow_credentials=self.allow_credentials,
            allow_methods=self.allow_methods,
            allow_headers=self.allow_headers,
            expose_headers=self.expose_headers,
            max_age=self.max_age
        )

    def _get_default_origins(self) -> List[str]:
        """Get default allowed origins from environment."""
        env_origins = os.getenv("CORS_ORIGINS", "")
        if env_origins:
            return [origin.strip() for origin in env_origins.split(",")]

        # Default origins for development
        default_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ]

        # Add production URL if available
        if os.getenv("FRONTEND_URL"):
            default_origins.append(os.getenv("FRONTEND_URL"))

        return default_origins

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add additional CORS security features."""

        # Handle preflight requests
        if request.method == "OPTIONS":
            # Add additional security headers for preflight
            response = await call_next(request)
        else:
            response = await call_next(request)

        # Add security headers
        self._add_security_headers(request, response)

        # Log CORS requests in strict mode
        if self.strict_mode:
            self._log_cors_request(request, response)

        return response

    def _add_security_headers(self, request: Request, response: Response):
        """Add additional security headers."""
        # Remove server information
        response.headers["Server"] = ""

        # CSP header (Content Security Policy)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS (only in production with HTTPS)
        if os.getenv("ENVIRONMENT") == "production" and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Permissions Policy
        permissions_policy = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)

    def _log_cors_request(self, request: Request, response: Response):
        """Log CORS-related requests for monitoring."""
        from src.utils.logging import get_logger

        logger = get_logger("cors")

        origin = request.headers.get("origin")
        if origin:
            if origin not in self.allow_origins:
                logger.warning(
                    "Cross-origin request from unauthorized origin",
                    origin=origin,
                    path=request.url.path,
                    method=request.method,
                )
            else:
                logger.info(
                    "Cross-origin request allowed",
                    origin=origin,
                    path=request.url.path,
                    method=request.method,
                )


class RateLimitCORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware with rate limiting per origin."""

    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 100,
        burst_size: int = 200
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.request_counts = {}  # Simple in-memory tracking

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Apply rate limiting based on origin."""
        import time
        from fastapi import HTTPException

        origin = request.headers.get("origin")
        if origin:
            current_time = time.time()
            minute_key = int(current_time // 60)

            # Clean old entries
            self._cleanup_old_entries(minute_key)

            # Track requests
            origin_key = f"{origin}:{minute_key}"
            count = self.request_counts.get(origin_key, 0)

            if count >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests from this origin",
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str((minute_key + 1) * 60)
                    }
                )

            self.request_counts[origin_key] = count + 1

        response = await call_next(request)

        # Add rate limit headers
        if origin:
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            remaining = max(0, self.requests_per_minute - self.request_counts.get(origin_key, 0))
            response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _cleanup_old_entries(self, current_minute: int):
        """Remove old entries from request counts."""
        keys_to_remove = []
        for key in self.request_counts.keys():
            key_minute = int(key.split(":")[-1])
            if current_minute - key_minute > 5:  # Keep 5 minutes of history
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.request_counts[key]


def configure_cors(
    app: FastAPI,
    environment: str = "development"
) -> None:
    """Configure CORS based on environment."""

    if environment == "production":
        # Production CORS settings
        origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

        # Add production frontend URL
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url and frontend_url not in origins:
            origins.append(frontend_url)

        # In production, be strict about origins
        if origins:
            app.add_middleware(
                CustomCORSMiddleware,
                allow_origins=origins,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
                expose_headers=["X-Total-Count", "X-Page-Count"],
                strict_mode=True
            )

        # Add rate limiting
        app.add_middleware(
            RateLimitCORSMiddleware,
            requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        )

    else:
        # Development CORS settings - more permissive
        app.add_middleware(
            CustomCORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://localhost:5173",  # Vite dev server
                "http://127.0.0.1:5173",
            ],
            allow_credentials=True,
            strict_mode=False
        )


# CORS configuration for specific routes
class RouteSpecificCORSMiddleware(BaseHTTPMiddleware):
    """Apply different CORS settings to specific routes."""

    def __init__(
        self,
        app: FastAPI,
        path_prefix: str,
        cors_config: dict
    ):
        super().__init__(app)
        self.path_prefix = path_prefix
        self.cors_config = cors_config

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Apply route-specific CORS configuration."""
        if request.url.path.startswith(self.path_prefix):
            # Apply custom CORS settings for this route
            origin = request.headers.get("origin")
            if origin and self.cors_config.get("allowed_origins"):
                if origin in self.cors_config["allowed_origins"]:
                    response = await call_next(request)
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = "true"

                    for method in self.cors_config.get("allowed_methods", []):
                        response.headers["Access-Control-Allow-Methods"] = ", ".join(methods)

                    for header in self.cors_config.get("allowed_headers", []):
                        response.headers["Access-Control-Allow-Headers"] = ", ".join(headers)

                    return response
        else:
            # Use default CORS handling
            return await call_next(request)


# Pre-configured CORS settings for different environments
CORS_CONFIGS = {
    "development": {
        "allowed_origins": ["http://localhost:3000", "http://localhost:5173"],
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allowed_headers": ["*"],
        "allow_credentials": True,
        "strict_mode": False
    },
    "staging": {
        "allowed_origins": ["https://staging.example.com"],
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allowed_headers": ["Authorization", "Content-Type"],
        "allow_credentials": True,
        "strict_mode": True
    },
    "production": {
        "allowed_origins": ["https://example.com"],
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allowed_headers": ["Authorization", "Content-Type"],
        "allow_credentials": True,
        "strict_mode": True
    }
}


def setup_cors_with_config(
    app: FastAPI,
    config_name: str = "development"
) -> None:
    """Setup CORS using pre-configured settings."""

    config = CORS_CONFIGS.get(config_name, CORS_CONFIGS["development"])

    app.add_middleware(
        CustomCORSMiddleware,
        **config
    )

    # Log CORS configuration
    from src.utils.logging import get_logger

    logger = get_logger("cors")
    logger.info(
        "CORS configured",
        environment=config_name,
        allowed_origins=config["allowed_origins"],
        allow_credentials=config["allow_credentials"]
    )