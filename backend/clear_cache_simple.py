#!/usr/bin/env python3
"""
Simple script to clear translation cache without complex imports.
"""

import sqlite3
import os
from pathlib import Path

def get_db_path():
    """Get the path to the SQLite database."""
    # Try common database locations
    db_paths = [
        "database/auth.db",
        "../database/auth.db",
        "auth.db"
    ]

    for path in db_paths:
        if Path(path).exists():
            return path
    return "database/auth.db"  # Default path

def clear_translation_cache():
    """Clear all translation cache entries."""
    db_path = get_db_path()
    print(f"Using database at: {db_path}")

    if not Path(db_path).exists():
        print("Database file not found!")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if translation_cache table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='translation_cache'
        """)

        table_exists = cursor.fetchone()
        if not table_exists:
            print("Translation cache table does not exist.")
            return False

        # Count entries before deletion
        cursor.execute("SELECT COUNT(*) FROM translation_cache")
        count_before = cursor.fetchone()[0]
        print(f"Found {count_before} cache entries")

        if count_before > 0:
            # Delete all entries
            cursor.execute("DELETE FROM translation_cache")
            conn.commit()

            # Count after deletion
            cursor.execute("SELECT COUNT(*) FROM translation_cache")
            count_after = cursor.fetchone()[0]

            print(f"Successfully deleted {count_before - count_after} cache entries")
        else:
            print("No cache entries to delete")

        conn.close()
        return True

    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False

if __name__ == "__main__":
    print("\n=== Simple Translation Cache Clearer ===\n")
    success = clear_translation_cache()

    if success:
        print("\nCache cleared successfully!\n")
    else:
        print("\nFailed to clear cache.\n")