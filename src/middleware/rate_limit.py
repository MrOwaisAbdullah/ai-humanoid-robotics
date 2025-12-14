"""
Rate Limiting Middleware for Translation API.

This middleware implements per-IP and per-user rate limiting
to prevent abuse and manage Gemini API quotas effectively.
"""

import time
import asyncio
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.translation_logger import get_translation_logger

logger = get_translation_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting API requests.

    Implements:
    - Per-IP rate limiting
    - Per-user rate limiting (if authenticated)
    - Sliding window algorithm
    - Redis-based storage (if available)
    - In-memory fallback
    """

    def __init__(
        self,
        app,
        *,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        redis_client=None
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Requests allowed per minute per client
            requests_per_hour: Requests allowed per hour per client
            redis_client: Optional Redis client for distributed rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.redis_client = redis_client

        # In-memory storage fallback
        self.ip_rate_limits: Dict[str, Dict[str, Any]] = {}
        self.user_rate_limits: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "Rate limit middleware initialized",
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_hour,
            redis_enabled=redis_client is not None
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response or rate limit error
        """
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/enhanced", "/metrics/health"]:
            return await call_next(request)

        # Get client identifiers
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)

        # Check rate limits
        await self._check_rate_limits(client_ip, user_id)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        self._add_rate_limit_headers(response, client_ip, user_id)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Get user ID from request if authenticated."""
        # This would extract from JWT token or session
        # For now, return None to implement IP-based limiting only
        return None

    async def _check_rate_limits(self, client_ip: str, user_id: Optional[str]) -> None:
        """
        Check if client has exceeded rate limits.

        Args:
            client_ip: Client IP address
            user_id: Optional user ID

        Raises:
            HTTPException: If rate limit exceeded
        """
        now = time.time()

        # Check per-IP limits
        ip_data = await self._get_rate_limit_data(f"ip:{client_ip}")
        if self._is_rate_limited(ip_data, now):
            retry_after = self._calculate_retry_after(ip_data, now)
            logger.warning(
                "IP rate limit exceeded",
                client_ip=client_ip,
                requests_in_minute=ip_data.get("minute_requests", 0),
                retry_after=retry_after
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"IP rate limit exceeded. Please wait {retry_after:.1f} seconds.",
                    "retry_after": retry_after,
                    "limit_type": "ip"
                }
            )

        # Check per-user limits if authenticated
        if user_id:
            user_data = await self._get_rate_limit_data(f"user:{user_id}")
            if self._is_rate_limited(user_data, now):
                retry_after = self._calculate_retry_after(user_data, now)
                logger.warning(
                    "User rate limit exceeded",
                    user_id=user_id,
                    requests_in_minute=user_data.get("minute_requests", 0),
                    retry_after=retry_after
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"User rate limit exceeded. Please wait {retry_after:.1f} seconds.",
                        "retry_after": retry_after,
                        "limit_type": "user"
                    }
                )

        # Update rate limit data
        await self._update_rate_limit_data(f"ip:{client_ip}", now)
        if user_id:
            await self._update_rate_limit_data(f"user:{user_id}", now)

    async def _get_rate_limit_data(self, key: str) -> Dict[str, Any]:
        """Get rate limit data for a client."""
        if self.redis_client:
            try:
                # Get data from Redis
                data = await self.redis_client.hgetall(f"rate_limit:{key}")
                if data:
                    return {
                        "minute_requests": int(data.get("minute_requests", 0)),
                        "minute_window": float(data.get("minute_window", 0)),
                        "hour_requests": int(data.get("hour_requests", 0)),
                        "hour_window": float(data.get("hour_window", 0)),
                        "last_request": float(data.get("last_request", 0))
                    }
            except Exception as e:
                logger.warning("Redis rate limit read failed", error=str(e))

        # Fall back to in-memory
        if key.startswith("ip:"):
            storage = self.ip_rate_limits
            key = key[3:]  # Remove "ip:" prefix
        else:
            storage = self.user_rate_limits
            key = key[5:]  # Remove "user:" prefix

        return storage.get(key, {
            "minute_requests": 0,
            "minute_window": 0,
            "hour_requests": 0,
            "hour_window": 0,
            "last_request": 0
        })

    async def _update_rate_limit_data(self, key: str, now: float) -> None:
        """Update rate limit data for a client."""
        # Get current data
        data = await self._get_rate_limit_data(key)

        # Update minute window
        if now - data["minute_window"] > 60:
            data["minute_requests"] = 1
            data["minute_window"] = now
        else:
            data["minute_requests"] += 1

        # Update hour window
        if now - data["hour_window"] > 3600:
            data["hour_requests"] = 1
            data["hour_window"] = now
        else:
            data["hour_requests"] += 1

        data["last_request"] = now

        # Save updated data
        if self.redis_client:
            try:
                # Save to Redis with TTL
                await self.redis_client.hset(
                    f"rate_limit:{key}",
                    mapping={
                        "minute_requests": str(data["minute_requests"]),
                        "minute_window": str(data["minute_window"]),
                        "hour_requests": str(data["hour_requests"]),
                        "hour_window": str(data["hour_window"]),
                        "last_request": str(data["last_request"])
                    }
                )
                # Set TTL to 1 hour
                await self.redis_client.expire(f"rate_limit:{key}", 3600)
            except Exception as e:
                logger.warning("Redis rate limit write failed", error=str(e))

        # Fall back to in-memory
        if key.startswith("ip:"):
            storage = self.ip_rate_limits
            key = key[3:]  # Remove "ip:" prefix
        else:
            storage = self.user_rate_limits
            key = key[5:]  # Remove "user:" prefix

        storage[key] = data

        # Cleanup old entries (simple cleanup every 100 requests)
        if data["minute_requests"] % 100 == 0:
            await self._cleanup_old_entries(now)

    async def _cleanup_old_entries(self, now: float) -> None:
        """Clean up old rate limit entries."""
        cutoff = now - 3600  # 1 hour ago

        # Cleanup IP entries
        to_remove = []
        for ip, data in self.ip_rate_limits.items():
            if data["last_request"] < cutoff:
                to_remove.append(ip)
        for ip in to_remove:
            del self.ip_rate_limits[ip]

        # Cleanup user entries
        to_remove = []
        for user, data in self.user_rate_limits.items():
            if data["last_request"] < cutoff:
                to_remove.append(user)
        for user in to_remove:
            del self.user_rate_limits[user]

        if to_remove:
            logger.debug("Cleaned up old rate limit entries", count=len(to_remove))

    def _is_rate_limited(self, data: Dict[str, Any], now: float) -> bool:
        """Check if client has exceeded rate limits."""
        # Check minute limit
        if now - data["minute_window"] < 60:
            if data["minute_requests"] >= self.requests_per_minute:
                return True

        # Check hour limit
        if now - data["hour_window"] < 3600:
            if data["hour_requests"] >= self.requests_per_hour:
                return True

        return False

    def _calculate_retry_after(self, data: Dict[str, Any], now: float) -> float:
        """Calculate retry-after time based on rate limit data."""
        # Check minute limit
        if now - data["minute_window"] < 60 and data["minute_requests"] >= self.requests_per_minute:
            return 60 - (now - data["minute_window"])

        # Check hour limit
        if now - data["hour_window"] < 3600 and data["hour_requests"] >= self.requests_per_hour:
            return 3600 - (now - data["hour_window"])

        return 60.0  # Default retry after

    def _add_rate_limit_headers(
        self,
        response,
        client_ip: str,
        user_id: Optional[str]
    ) -> None:
        """Add rate limit headers to response."""
        now = time.time()

        # Get current limits
        ip_data = asyncio.create_task(self._get_rate_limit_data(f"ip:{client_ip}"))
        ip_data_result = asyncio.run(ip_data)

        # Add headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, self.requests_per_minute - ip_data_result.get("minute_requests", 0))
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.requests_per_hour - ip_data_result.get("hour_requests", 0))
        )

        # Add reset time
        if ip_data_result.get("minute_window", 0):
            reset_time = ip_data_result["minute_window"] + 60
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))


class TranslationRateLimitMiddleware(RateLimitMiddleware):
    """
    Specialized rate limit middleware for translation endpoints.

    Implements stricter limits for translation endpoints to manage
    Gemini API quotas effectively.
    """

    def __init__(
        self,
        app,
        *,
        redis_client=None
    ):
        """
        Initialize translation rate limit middleware.

        Args:
            app: FastAPI application
            redis_client: Optional Redis client
        """
        # Stricter limits for translation endpoints
        super().__init__(
            app,
            requests_per_minute=10,  # 10 translations per minute
            requests_per_hour=500,   # 500 translations per hour
            redis_client=redis_client
        )

        logger.info(
            "Translation rate limit middleware initialized",
            requests_per_minute=10,
            requests_per_hour=500
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request with translation-specific rate limiting.

        Only applies to translation endpoints.
        """
        # Check if this is a translation endpoint
        if not request.url.path.startswith("/translation/"):
            return await call_next(request)

        # Apply rate limiting
        return await super().dispatch(request, call_next)