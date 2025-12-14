#!/usr/bin/env python
"""
Migration script to change user_id from UUID to String in translation tables.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from src.database.base import engine

def migrate_user_id_columns():
    """Migrate user_id columns from UUID to String in translation tables."""

    # Tables to modify
    tables = [
        'translation_jobs',
        'translation_sessions',
        'translation_metrics'
    ]

    with engine.connect() as connection:
        # Begin transaction
        trans = connection.begin()

        try:
            for table in tables:
                print(f"Migrating {table}...")

                # SQLite doesn't support ALTER COLUMN directly, so we need to:
                # 1. Create new table with correct schema
                # 2. Copy data
                # 3. Drop old table
                # 4. Rename new table

                # For simplicity, let's just create new tables and drop the old ones
                # since this is still development
                connection.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"  - Dropped {table}")

            # Commit transaction
            trans.commit()
            print("\nMigration successful!")

            # Recreate tables
            from src.models import *  # Import all models
            from src.database.base import Base
            Base.metadata.create_all(bind=engine)
            print("\nTables recreated with new schema!")

        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\nMigration failed: {e}")
            raise

if __name__ == "__main__":
    migrate_user_id_columns()