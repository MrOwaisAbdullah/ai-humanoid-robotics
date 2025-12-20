#!/usr/bin/env python3
"""
Check database structure and contents.
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

def check_database():
    """Check database structure and contents."""
    db_path = get_db_path()
    print(f"Using database at: {db_path}")

    if not Path(db_path).exists():
        print("Database file not found!")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print("\n=== Tables in database ===")
        for table in tables:
            print(f"- {table[0]}")

        # Check for translation cache specifically
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='translation_cache'
        """)

        translation_table = cursor.fetchone()

        if translation_table:
            print("\n=== Translation Cache Table ===")

            # Get table structure
            cursor.execute("PRAGMA table_info(translation_cache)")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # Count entries
            cursor.execute("SELECT COUNT(*) FROM translation_cache")
            count = cursor.fetchone()[0]
            print(f"\nTotal entries: {count}")

            # Show sample entries if any
            if count > 0:
                cursor.execute("SELECT * FROM translation_cache LIMIT 3")
                sample = cursor.fetchall()
                print("\nSample entries:")
                for row in sample:
                    print(f"  ID: {row[0]}, Original: {row[1][:50]}...")
        else:
            print("\nTranslation cache table does not exist.")

        conn.close()
        return True

    except Exception as e:
        print(f"Error checking database: {e}")
        return False

if __name__ == "__main__":
    print("\n=== Database Checker ===\n")
    check_database()
    print("\n")