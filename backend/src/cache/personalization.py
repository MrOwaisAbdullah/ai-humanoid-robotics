"""
Personalization Cache Utilities
Handles caching of personalized content for performance optimization
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Try to import Redis, but don't fail if not available
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class PersonalizationCache:
    """
    Cache for personalized content with Redis support and in-memory fallback
    """

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600):
        """
        Initialize the cache

        Args:
            redis_url: Redis connection URL (optional)
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.default_ttl = default_ttl
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info("Personalization cache initialized with Redis")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}. Using in-memory cache.")

    @staticmethod
    def _generate_cache_key(content: str, user_profile: Dict[str, Any]) -> str:
        """
        Generate a cache key based on content and user profile

        Args:
            content: The content being personalized
            user_profile: User's profile information

        Returns:
            A unique cache key
        """
        # Create a deterministic key from content and profile
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        profile_hash = hashlib.sha256(
            json.dumps(user_profile, sort_keys=True).encode()
        ).hexdigest()

        return f"personalization:{content_hash}:{profile_hash}"

    async def get(self, content: str, user_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached personalized content

        Args:
            content: Original content
            user_profile: User's profile

        Returns:
            Cached personalized content or None
        """
        cache_key = self._generate_cache_key(content, user_profile)

        # Try Redis first
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return data
            except Exception as e:
                logger.warning(f"Redis get failed: {e}. Falling back to memory cache.")

        # Fall back to memory cache
        memory_data = self.memory_cache.get(cache_key)
        if memory_data:
            # Check if expired
            now = datetime.utcnow()
            if now < memory_data.get("expires_at"):
                logger.debug(f"Memory cache hit for key: {cache_key}")
                return memory_data.get("data")
            else:
                # Remove expired entry
                del self.memory_cache[cache_key]

        return None

    async def set(
        self,
        content: str,
        user_profile: Dict[str, Any],
        personalized_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache personalized content

        Args:
            content: Original content
            user_profile: User's profile
            personalized_data: The personalized content data
            ttl: Time to live in seconds (optional, uses default)
        """
        cache_key = self._generate_cache_key(content, user_profile)
        ttl = ttl or self.default_ttl

        # Prepare cache data with metadata
        cache_data = {
            "data": personalized_data,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": ttl
        }

        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(cache_data)
                )
                logger.debug(f"Cached to Redis: {cache_key}")
                return
            except Exception as e:
                logger.warning(f"Redis set failed: {e}. Falling back to memory cache.")

        # Fall back to memory cache
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self.memory_cache[cache_key] = {
            "data": personalized_data,
            "expires_at": expires_at
        }

        # Simple cleanup when cache gets too large
        if len(self.memory_cache) > 1000:
            await self._cleanup_memory_cache()

        logger.debug(f"Cached to memory: {cache_key}")

    async def invalidate(self, content: str, user_profile: Dict[str, Any]) -> bool:
        """
        Invalidate cached content

        Args:
            content: Original content
            user_profile: User's profile

        Returns:
            True if cache entry was invalidated
        """
        cache_key = self._generate_cache_key(content, user_profile)

        # Try Redis first
        if self.redis_client:
            try:
                result = await self.redis_client.delete(cache_key)
                if result:
                    logger.debug(f"Invalidated Redis cache: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # Remove from memory cache
        memory_existed = cache_key in self.memory_cache
        if memory_existed:
            del self.memory_cache[cache_key]
            logger.debug(f"Invalidated memory cache: {cache_key}")

        return memory_existed

    async def clear_user_cache(self, user_profile: Dict[str, Any]) -> int:
        """
        Clear all cache entries for a specific user

        Args:
            user_profile: User's profile to clear cache for

        Returns:
            Number of cache entries cleared
        """
        # This is more complex with pattern matching
        # For now, we'll implement a simple approach
        cleared_count = 0

        # Clear memory cache entries
        keys_to_remove = []
        for key in self.memory_cache.keys():
            # This is a simplified check - in production, you might want
            # to store user_id separately for easier invalidation
            if key.startswith("personalization:"):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.memory_cache[key]
            cleared_count += 1

        # Redis implementation would require SCAN with pattern matching
        if self.redis_client:
            try:
                # This is a placeholder - implement based on your Redis version
                cursor = "0"
                pattern = "personalization:*"
                while cursor != 0:
                    cursor, keys = await self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )
                    if keys:
                        # Here you'd check if each key belongs to the user
                        # This is simplified - you might store user_id in the key
                        await self.redis_client.delete(*keys)
                        cleared_count += len(keys)
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        return cleared_count

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_keys": list(self.memory_cache.keys())[:10],  # First 10 keys
            "redis_enabled": self.redis_client is not None
        }

        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats["redis_memory_used"] = info.get("used_memory_human")
                stats["redis_connected_clients"] = info.get("connected_clients")
                stats["redis_keyspace_hits"] = info.get("keyspace_hits", 0)
                stats["redis_keyspace_misses"] = info.get("keyspace_misses", 0)

                # Calculate hit rate
                hits = stats["redis_keyspace_hits"]
                misses = stats["redis_keyspace_misses"]
                total = hits + misses
                if total > 0:
                    stats["redis_hit_rate"] = f"{(hits / total * 100):.2f}%"
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")

        return stats

    async def _cleanup_memory_cache(self) -> None:
        """
        Clean up expired entries from memory cache
        """
        now = datetime.utcnow()
        keys_to_remove = []

        for key, value in self.memory_cache.items():
            if now >= value.get("expires_at"):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.memory_cache[key]

        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} expired cache entries")


# Global cache instance
_personalization_cache: Optional[PersonalizationCache] = None


def get_personalization_cache() -> PersonalizationCache:
    """
    Get the global personalization cache instance

    Returns:
        PersonalizationCache instance
    """
    global _personalization_cache

    if _personalization_cache is None:
        redis_url = None  # Could get from config or environment
        _personalization_cache = PersonalizationCache(redis_url=redis_url)

    return _personalization_cache


# Cache decorator for functions
def cache_personalization(ttl: int = 3600):
    """
    Decorator to cache personalization function results

    Args:
        ttl: Time to live in seconds
    """
    def decorator(func):
        async def wrapper(content: str, user_profile: Dict[str, Any], *args, **kwargs):
            cache = get_personalization_cache()

            # Check cache first
            cached_result = await cache.get(content, user_profile)
            if cached_result:
                return cached_result

            # Execute function
            result = await func(content, user_profile, *args, **kwargs)

            # Cache result
            await cache.set(content, user_profile, result, ttl)

            return result
        return wrapper
    return decorator