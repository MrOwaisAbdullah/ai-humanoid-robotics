#!/usr/bin/env python3
"""
Clear translation cache for problematic entries.
Run this script to clear the cache if translations are showing incorrectly cached results.
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database configuration
from database.config import DATABASE_URL, get_db
from src.services.translation_cache import TranslationCache, cache_service


def clear_all_cache():
    """Clear all translation cache entries."""
    print("🗑️ Clearing all translation cache...")

    try:
        # Get database session
        db = next(get_db())

        # Count existing entries
        from sqlalchemy import select, func
        count_query = select(func.count(TranslationCache.id))
        total_count = db.execute(count_query).scalar()
        print(f"   Found {total_count} cache entries")

        # Delete all entries
        delete_query = delete(TranslationCache)
        result = db.execute(delete_query)
        db.commit()

        print(f"   ✅ Cleared {result.rowcount} cache entries")

    except Exception as e:
        print(f"   ❌ Error clearing cache: {e}")
        return False

    return True


def clear_expired_cache():
    """Clear only expired translation cache entries."""
    print("🕒 Clearing expired translation cache...")

    try:
        # Use the cache service method
        cleared = cache_service.clear_expired_cache()
        print(f"   ✅ Cleared {cleared} expired entries")

    except Exception as e:
        print(f"   ❌ Error clearing expired cache: {e}")
        return False

    return True


def clear_url_cache(url_pattern: str = None):
    """Clear cache for specific URLs or all URLs with a pattern."""
    if not url_pattern:
        print("Please provide a URL pattern to clear")
        return False

    print(f"🔗 Clearing cache for URLs matching: {url_pattern}")

    try:
        db = next(get_db())

        # Build query with LIKE pattern
        from sqlalchemy import or_
        query = delete(TranslationCache).where(
            or_(
                TranslationCache.page_url.like(f"%{url_pattern}%"),
                TranslationCache.url_hash.like(f"%{url_pattern}%")
            )
        )

        result = db.execute(query)
        db.commit()

        print(f"   ✅ Cleared {result.rowcount} entries matching pattern")

    except Exception as e:
        print(f"   ❌ Error clearing URL cache: {e}")
        return False

    return True


def main():
    """Main function."""
    print("\n=== Translation Cache Clearer ===")
    print(f"Timestamp: {datetime.now().isoformat()}")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "all":
            clear_all_cache()
        elif command == "expired":
            clear_expired_cache()
        elif command == "url" and len(sys.argv) > 2:
            clear_url_cache(sys.argv[2])
        else:
            print("\nUsage:")
            print("  python clear_translation_cache.py all          # Clear all cache")
            print("  python clear_translation_cache.py expired     # Clear expired entries")
            print("  python clear_translation_cache.py url <pattern>  # Clear URLs matching pattern")
    else:
        print("\nNo command provided. Running expired cache cleanup...")
        clear_expired_cache()

    print("\n✨ Cache cleanup complete!\n")


if __name__ == "__main__":
    main()