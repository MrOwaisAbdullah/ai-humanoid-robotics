"""
Cache service for server-side caching with localStorage fallback.

Provides Redis caching with localStorage fallback, supporting different TTLs
for various cache types including translations, user preferences, and API responses.
"""

import json
import pickle
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import hashlib
import os
from pathlib import Path

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from src.utils.errors import CacheError, ValidationError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CacheType(Enum):
    """Cache types with different TTLs."""
    TRANSLATION = "translation"
    USER_PREFERENCE = "user_preference"
    API_RESPONSE = "api_response"
    PERSONALIZATION = "personalization"
    PROGRESS = "progress"
    SEARCH_RESULT = "search_result"
    BOOKMARK = "bookmark"


class CacheService:
    """
    Cache service with Redis primary and localStorage fallback.

    Features:
    - Redis as primary cache (if available)
    - localStorage as fallback
    - TTL support per cache type
    - Compression for large objects
    - Statistics tracking
    - Error handling and logging
    """

    # TTL configurations (in seconds)
    TTL_CONFIG = {
        CacheType.TRANSLATION: 7 * 24 * 60 * 60,  # 7 days
        CacheType.USER_PREFERENCE: 30 * 24 * 60 * 60,  # 30 days
        CacheType.API_RESPONSE: 5 * 60,  # 5 minutes
        CacheType.PERSONALIZATION: 1 * 60 * 60,  # 1 hour
        CacheType.PROGRESS: 24 * 60 * 60,  # 24 hours
        CacheType.SEARCH_RESULT: 10 * 60,  # 10 minutes
        CacheType.BOOKMARK: 30 * 24 * 60 * 60,  # 30 days
    }

    # Statistics
    _stats = {
        "hits": 0,
        "misses": 0,
        "errors": 0,
        "redis_hits": 0,
        "local_hits": 0,
    }

    def __init__(
        self,
        redis_url: Optional[str] = None,
        localStorage_path: Optional[str] = None,
        enable_redis: bool = True,
        enable_compression: bool = True,
        compression_threshold: int = 1024
    ):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL
            localStorage_path: Path to localStorage directory
            enable_redis: Whether to use Redis if available
            enable_compression: Whether to compress large objects
            compression_threshold: Size threshold for compression (bytes)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.localStorage_path = Path(localStorage_path or os.getenv("CACHE_LOCAL_PATH", "./cache_data"))
        self.enable_redis = enable_redis and REDIS_AVAILABLE
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold

        self._redis_client = None
        self._local_cache = {}

        # Initialize localStorage
        self.localStorage_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Cache service initialized",
            redis_enabled=self.enable_redis,
            localStorage_path=str(self.localStorage_path),
            compression_enabled=self.enable_compression
        )

    async def _get_redis_client(self):
        """Get or create Redis client."""
        if not self.enable_redis:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning("Failed to connect to Redis", error=str(e))
                self.enable_redis = False
                self._redis_client = None

        return self._redis_client

    def _generate_cache_key(
        self,
        prefix: str,
        identifier: str,
        version: str = "v1",
        **kwargs
    ) -> str:
        """
        Generate a consistent cache key.

        Args:
            prefix: Cache type or prefix
            identifier: Unique identifier for the cache entry
            version: Version of the cache schema
            **kwargs: Additional parameters to include in key

        Returns:
            Generated cache key
        """
        # Create a stable representation of parameters
        params = sorted(kwargs.items())
        param_str = json.dumps(params, sort_keys=True, separators=(',', ':'))

        # Create hash of identifier and params
        hash_input = f"{identifier}:{param_str}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        return f"{prefix}:{version}:{identifier}:{hash_value}"

    async def get(
        self,
        key: str,
        cache_type: CacheType = CacheType.API_RESPONSE,
        use_compression: Optional[bool] = None
    ) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            cache_type: Type of cache entry
            use_compression: Override compression setting

        Returns:
            Cached value or None if not found
        """
        try:
            # Try Redis first
            if self.enable_redis:
                redis_client = await self._get_redis_client()
                if redis_client:
                    value = await self._get_from_redis(
                        redis_client,
                        key,
                        cache_type,
                        use_compression
                    )
                    if value is not None:
                        self._stats["hits"] += 1
                        self._stats["redis_hits"] += 1
                        return value

            # Fallback to localStorage
            value = await self._get_from_local(key, cache_type, use_compression)
            if value is not None:
                self._stats["hits"] += 1
                self._stats["local_hits"] += 1

                # If found locally but not in Redis, backfill to Redis
                if self.enable_redis:
                    redis_client = await self._get_redis_client()
                    if redis_client:
                        ttl = self.TTL_CONFIG[cache_type]
                        await self._set_to_redis(
                            redis_client,
                            key,
                            value,
                            ttl,
                            use_compression
                        )

                return value

            # Cache miss
            self._stats["misses"] += 1
            return None

        except Exception as e:
            self._stats["errors"] += 1
            logger.error("Cache get failed", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: CacheType = CacheType.API_RESPONSE,
        ttl: Optional[int] = None,
        use_compression: Optional[bool] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache entry
            ttl: Time to live in seconds (overrides type TTL)
            use_compression: Override compression setting

        Returns:
            True if successful, False otherwise
        """
        try:
            success = True
            ttl = ttl or self.TTL_CONFIG[cache_type]

            # Set in Redis
            if self.enable_redis:
                redis_client = await self._get_redis_client()
                if redis_client:
                    success = await self._set_to_redis(
                        redis_client,
                        key,
                        value,
                        ttl,
                        use_compression
                    ) and success

            # Set in localStorage (always set as fallback)
            local_success = await self._set_to_local(
                key,
                value,
                cache_type,
                ttl,
                use_compression
            )
            success = local_success and success

            return success

        except Exception as e:
            self._stats["errors"] += 1
            logger.error("Cache set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            success = True

            # Delete from Redis
            if self.enable_redis:
                redis_client = await self._get_redis_client()
                if redis_client:
                    await redis_client.delete(key)

            # Delete from localStorage
            local_file = self.localStorage_path / f"{key}.cache"
            if local_file.exists():
                local_file.unlink()

            # Remove from memory cache
            if key in self._local_cache:
                del self._local_cache[key]

            return True

        except Exception as e:
            self._stats["errors"] += 1
            logger.error("Cache delete failed", key=key, error=str(e))
            return False

    async def clear(
        self,
        pattern: Optional[str] = None,
        cache_type: Optional[CacheType] = None
    ) -> int:
        """
        Clear cache entries.

        Args:
            pattern: Pattern to match keys (supports wildcards)
            cache_type: Clear only this cache type

        Returns:
            Number of entries cleared
        """
        try:
            cleared_count = 0

            # Build pattern if cache_type specified
            if cache_type and not pattern:
                pattern = f"{cache_type.value}:*"

            # Clear from Redis
            if self.enable_redis:
                redis_client = await self._get_redis_client()
                if redis_client:
                    if pattern:
                        keys = await redis_client.keys(pattern)
                        if keys:
                            await redis_client.delete(*keys)
                            cleared_count += len(keys)
                    else:
                        await redis_client.flushdb()
                        cleared_count = -1  # Indicate full clear

            # Clear from localStorage
            if pattern:
                # Convert pattern to file pattern
                file_pattern = pattern.replace("*", "").replace(":", "_") + "*.cache"
                for cache_file in self.localStorage_path.glob(file_pattern):
                    cache_file.unlink()
                    cleared_count += 1
            else:
                # Clear all files
                for cache_file in self.localStorage_path.glob("*.cache"):
                    cache_file.unlink()
                    cleared_count += 1

                # Clear memory cache
                self._local_cache.clear()

            logger.info("Cache cleared", pattern=pattern, count=cleared_count)
            return cleared_count

        except Exception as e:
            self._stats["errors"] += 1
            logger.error("Cache clear failed", pattern=pattern, error=str(e))
            return 0

    async def _get_from_redis(
        self,
        redis_client,
        key: str,
        cache_type: CacheType,
        use_compression: Optional[bool]
    ) -> Optional[Any]:
        """Get value from Redis."""
        try:
            data = await redis_client.get(key)
            if data is None:
                return None

            # Uncompress if needed
            if use_compression or (use_compression is None and self.enable_compression):
                if data.startswith(b"COMP:"):
                    import gzip
                    data = gzip.decompress(data[5:])

            # Deserialize
            return pickle.loads(data)

        except Exception as e:
            logger.warning("Redis get failed", key=key, error=str(e))
            return None

    async def _set_to_redis(
        self,
        redis_client,
        key: str,
        value: Any,
        ttl: int,
        use_compression: Optional[bool]
    ) -> bool:
        """Set value in Redis."""
        try:
            # Serialize
            data = pickle.dumps(value)

            # Compress if needed
            if (use_compression or (use_compression is None and self.enable_compression)) \
               and len(data) > self.compression_threshold:
                import gzip
                data = b"COMP:" + gzip.compress(data)

            await redis_client.setex(key, ttl, data)
            return True

        except Exception as e:
            logger.warning("Redis set failed", key=key, error=str(e))
            return False

    async def _get_from_local(
        self,
        key: str,
        cache_type: CacheType,
        use_compression: Optional[bool]
    ) -> Optional[Any]:
        """Get value from localStorage."""
        try:
            # Check memory cache first
            cache_entry = self._local_cache.get(key)
            if cache_entry:
                # Check if expired
                if cache_entry["expires"] > datetime.utcnow():
                    return cache_entry["value"]
                else:
                    # Remove expired entry
                    del self._local_cache[key]

            # Check file cache
            cache_file = self.localStorage_path / f"{key}.cache"
            if not cache_file.exists():
                return None

            # Read and validate file
            data = cache_file.read_bytes()
            cache_entry = json.loads(data.decode())

            # Check if expired
            expires = datetime.fromisoformat(cache_entry["expires"])
            if expires <= datetime.utcnow():
                cache_file.unlink()
                return None

            # Decode value
            if cache_entry.get("compressed") and (use_compression or (use_compression is None and self.enable_compression)):
                import gzip
                value = pickle.loads(gzip.decompress(cache_entry["value"].encode()))
            else:
                value = pickle.loads(cache_entry["value"].encode())

            # Update memory cache
            self._local_cache[key] = {
                "value": value,
                "expires": expires
            }

            return value

        except Exception as e:
            logger.warning("Local cache get failed", key=key, error=str(e))
            return None

    async def _set_to_local(
        self,
        key: str,
        value: Any,
        cache_type: CacheType,
        ttl: int,
        use_compression: Optional[bool]
    ) -> bool:
        """Set value in localStorage."""
        try:
            expires = datetime.utcnow() + timedelta(seconds=ttl)

            # Compress if needed
            compressed = False
            if (use_compression or (use_compression is None and self.enable_compression)):
                serialized = pickle.dumps(value)
                if len(serialized) > self.compression_threshold:
                    import gzip
                    value_serialized = gzip.compress(serialized).decode()
                    compressed = True
                else:
                    value_serialized = serialized.decode()
            else:
                value_serialized = pickle.dumps(value).decode()

            # Create cache entry
            cache_entry = {
                "value": value_serialized,
                "expires": expires.isoformat(),
                "compressed": compressed,
                "cache_type": cache_type.value
            }

            # Write to file
            cache_file = self.localStorage_path / f"{key}.cache"
            cache_file.write_bytes(json.dumps(cache_entry).encode())

            # Update memory cache
            self._local_cache[key] = {
                "value": value,
                "expires": expires
            }

            return True

        except Exception as e:
            logger.warning("Local cache set failed", key=key, error=str(e))
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / max(total_requests, 1) * 100

        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "redis_enabled": self.enable_redis,
            "memory_cache_size": len(self._local_cache)
        }

    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        cleaned = 0

        try:
            # Clean memory cache
            now = datetime.utcnow()
            expired_keys = [
                key for key, entry in self._local_cache.items()
                if entry["expires"] <= now
            ]

            for key in expired_keys:
                del self._local_cache[key]
                cleaned += 1

            # Clean file cache
            for cache_file in self.localStorage_path.glob("*.cache"):
                try:
                    data = json.loads(cache_file.read_bytes().decode())
                    expires = datetime.fromisoformat(data["expires"])
                    if expires <= datetime.utcnow():
                        cache_file.unlink()
                        cleaned += 1
                except:
                    # Invalid cache file, remove it
                    cache_file.unlink()
                    cleaned += 1

            logger.info("Cache cleanup completed", cleaned_entries=cleaned)
            return cleaned

        except Exception as e:
            logger.error("Cache cleanup failed", error=str(e))
            return 0


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService()

    return _cache_service


# Utility functions for specific cache types
async def cache_translation(
    key: str,
    translation: Dict[str, Any],
    language: str
) -> bool:
    """Cache a translation entry."""
    cache = await get_cache_service()
    cache_key = cache._generate_cache_key(
        "translation",
        key,
        lang=language
    )
    return await cache.set(
        cache_key,
        translation,
        CacheType.TRANSLATION
    )


async def get_cached_translation(
    key: str,
    language: str
) -> Optional[Dict[str, Any]]:
    """Get cached translation."""
    cache = await get_cache_service()
    cache_key = cache._generate_cache_key(
        "translation",
        key,
        lang=language
    )
    return await cache.get(cache_key, CacheType.TRANSLATION)


async def cache_user_preference(
    user_id: str,
    preferences: Dict[str, Any]
) -> bool:
    """Cache user preferences."""
    cache = await get_cache_service()
    cache_key = cache._generate_cache_key(
        "user_pref",
        user_id
    )
    return await cache.set(
        cache_key,
        preferences,
        CacheType.USER_PREFERENCE
    )


async def get_cached_user_preference(
    user_id: str
) -> Optional[Dict[str, Any]]:
    """Get cached user preferences."""
    cache = await get_cache_service()
    cache_key = cache._generate_cache_key(
        "user_pref",
        user_id
    )
    return await cache.get(cache_key, CacheType.USER_PREFERENCE)


async def cache_api_response(
    endpoint: str,
    params: Dict[str, Any],
    response: Dict[str, Any],
    ttl: Optional[int] = None
) -> bool:
    """Cache API response."""
    cache = await get_cache_service()
    cache_key = cache._generate_cache_key(
        "api",
        endpoint,
        **params
    )
    return await cache.set(
        cache_key,
        response,
        CacheType.API_RESPONSE,
        ttl=ttl
    )


async def get_cached_api_response(
    endpoint: str,
    params: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Get cached API response."""
    cache = await get_cache_service()
    cache_key = cache._generate_cache_key(
        "api",
        endpoint,
        **params
    )
    return await cache.get(cache_key, CacheType.API_RESPONSE)