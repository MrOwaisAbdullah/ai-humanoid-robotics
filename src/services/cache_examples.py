"""
Cache service usage examples.

This file demonstrates how to use the cache service for various scenarios
including translations, user preferences, and API response caching.
"""

import asyncio
from typing import Dict, Any
from src.services.cache_service import (
    get_cache_service,
    CacheType,
    cache_translation,
    get_cached_translation,
    cache_user_preference,
    get_cached_user_preference,
    cache_api_response,
    get_cached_api_response
)


async def example_basic_usage():
    """Basic cache service usage example."""
    # Get cache service instance
    cache = await get_cache_service()

    # Generate a cache key
    cache_key = cache._generate_cache_key(
        prefix="example",
        identifier="user_123",
        version="v1",
        param1="value1",
        param2="value2"
    )

    # Set a value
    await cache.set(
        key=cache_key,
        value={"message": "Hello, cached world!"},
        cache_type=CacheType.API_RESPONSE,
        ttl=60  # 1 minute
    )

    # Get the value
    cached_value = await cache.get(cache_key, CacheType.API_RESPONSE)
    print(f"Cached value: {cached_value}")

    # Delete the value
    await cache.delete(cache_key)


async def example_translation_caching():
    """Example of caching translations."""
    # Cache a translation
    translation_data = {
        "en": "Hello, World!",
        "ur": "ہیلو، دنیا!",
        "ur-roman": "Hello, Duniya!"
    }

    success = await cache_translation(
        key="greeting.hello_world",
        translation=translation_data,
        language="all"
    )

    if success:
        print("Translation cached successfully")

    # Retrieve cached translation
    cached_translation = await get_cached_translation(
        key="greeting.hello_world",
        language="all"
    )

    if cached_translation:
        print(f"Cached translation: {cached_translation}")


async def example_user_preference_caching():
    """Example of caching user preferences."""
    # Cache user preferences
    user_prefs = {
        "language": "en",
        "theme": "dark",
        "font_size": 16,
        "reading_pace": "medium",
        "show_code_examples": True
    }

    success = await cache_user_preference(
        user_id="user_456",
        preferences=user_prefs
    )

    if success:
        print("User preferences cached successfully")

    # Retrieve cached preferences
    cached_prefs = await get_cached_user_preference("user_456")

    if cached_prefs:
        print(f"Cached preferences: {cached_prefs}")


async def example_api_response_caching():
    """Example of caching API responses."""
    # Cache API response
    api_response = {
        "status": "success",
        "data": [
            {"id": 1, "title": "Chapter 1"},
            {"id": 2, "title": "Chapter 2"}
        ],
        "pagination": {
            "page": 1,
            "total_pages": 10
        }
    }

    success = await cache_api_response(
        endpoint="/api/v1/chapters",
        params={"page": 1, "limit": 10},
        response=api_response,
        ttl=300  # 5 minutes
    )

    if success:
        print("API response cached successfully")

    # Retrieve cached API response
    cached_response = await get_cached_api_response(
        endpoint="/api/v1/chapters",
        params={"page": 1, "limit": 10}
    )

    if cached_response:
        print(f"Cached API response: {cached_response}")


async def example_cache_statistics():
    """Example of retrieving cache statistics."""
    cache = await get_cache_service()

    # Get cache statistics
    stats = cache.get_stats()

    print("Cache Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Cache misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']}%")
    print(f"  Redis hits: {stats['redis_hits']}")
    print(f"  Local hits: {stats['local_hits']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Redis enabled: {stats['redis_enabled']}")
    print(f"  Memory cache size: {stats['memory_cache_size']}")


async def example_cache_cleanup():
    """Example of cleaning up expired cache entries."""
    cache = await get_cache_service()

    # Clean up expired entries
    cleaned_count = await cache.cleanup_expired()
    print(f"Cleaned up {cleaned_count} expired cache entries")

    # Clear all cache entries for a specific type
    cleared_count = await cache.clear(cache_type=CacheType.TRANSLATION)
    print(f"Cleared {cleared_count} translation cache entries")

    # Clear cache entries matching a pattern
    cleared_count = await cache.clear(pattern="api:v1:user_*")
    print(f"Cleared {cleared_count} entries matching pattern")


async def example_concurrent_access():
    """Example demonstrating thread-safe concurrent access."""
    async def worker(worker_id: int):
        cache = await get_cache_service()

        # Each worker uses its own key space
        key = f"worker_{worker_id}:data"

        for i in range(10):
            # Set value
            await cache.set(
                key=key,
                value={"worker": worker_id, "iteration": i},
                cache_type=CacheType.API_RESPONSE,
                ttl=60
            )

            # Get value
            value = await cache.get(key, CacheType.API_RESPONSE)
            print(f"Worker {worker_id}, iteration {i}: {value}")

            # Small delay
            await asyncio.sleep(0.1)

    # Run multiple workers concurrently
    tasks = [worker(i) for i in range(5)]
    await asyncio.gather(*tasks)


async def main():
    """Run all examples."""
    print("=== Basic Usage ===")
    await example_basic_usage()

    print("\n=== Translation Caching ===")
    await example_translation_caching()

    print("\n=== User Preference Caching ===")
    await example_user_preference_caching()

    print("\n=== API Response Caching ===")
    await example_api_response_caching()

    print("\n=== Cache Statistics ===")
    await example_cache_statistics()

    print("\n=== Cache Cleanup ===")
    await example_cache_cleanup()

    print("\n=== Concurrent Access ===")
    await example_concurrent_access()


if __name__ == "__main__":
    asyncio.run(main())