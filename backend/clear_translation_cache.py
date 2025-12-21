"""
Script to clear all translation cache from database
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

# Load environment
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

print(f"Connecting to database: {DATABASE_URL}")


async def clear_translation_cache():
    """Clear all translation cache entries."""

    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)

        print("\n[INFO] Clearing translation cache...")

        with engine.connect() as conn:
            # Check if translation cache table exists
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='translation_cache'"
            ))

            if not result.fetchone():
                print("[INFO] Translation cache table not found")
                return

            # Get count before clearing
            result = conn.execute(text("SELECT COUNT(*) FROM translation_cache"))
            count_before = result.scalar()
            print(f"[INFO] Found {count_before} cached translations")

            # Clear all entries
            result = conn.execute(text("DELETE FROM translation_cache"))
            rows_deleted = result.rowcount

            # Verify deletion
            result = conn.execute(text("SELECT COUNT(*) FROM translation_cache"))
            count_after = result.scalar()

            print(f"[SUCCESS] Deleted {rows_deleted} cache entries")
            print(f"[INFO] Remaining cache entries: {count_after}")

            # Also clear any browser localStorage hints in the response
            print("\n[INFO] Browser cache clearing:")
            print("  - Users should clear browser localStorage")
            print("  - Use clear_frontend_cache.js script")

    except Exception as e:
        print(f"\n[ERROR] Failed to clear cache: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(clear_translation_cache())
