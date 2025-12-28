"""
Script to check the current database state and diagnose foreign key issues.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fix SSL parameter for asyncpg
if "?sslmode=require" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "?ssl=require")

async def check_database():
    """Check the current state of the database."""
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("\n=== Checking existing tables ===")
        result = await conn.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        print("\n=== Checking for users table ===")
        if 'users' in tables:
            print("[OK] users table exists")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            print("Users table columns:")
            for row in result.fetchall():
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")

            # Get a sample user_id
            result = await conn.execute(text("SELECT id FROM users LIMIT 1"))
            user = result.fetchone()
            if user:
                print(f"Sample user_id: {user[0]} (type: {type(user[0]).__name__})")
        else:
            print("[X] users table does NOT exist")

        print("\n=== Checking for saved_personalizations table ===")
        if 'saved_personalizations' in tables:
            print("[OK] saved_personalizations table exists")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'saved_personalizations'
                ORDER BY ordinal_position;
            """))
            print("Saved_personalizations table columns:")
            for row in result.fetchall():
                print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")

            # Check foreign key constraints
            print("\n=== Checking foreign key constraints on saved_personalizations ===")
            result = await conn.execute(text("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = 'saved_personalizations';
            """))
            fk_constraints = result.fetchall()
            if fk_constraints:
                print("Foreign key constraints:")
                for row in fk_constraints:
                    print(f"  - {row[0]}: {row[1]} -> {row[2]}.{row[3]}")
            else:
                print("[X] No foreign key constraints found!")
        else:
            print("[X] saved_personalizations table does NOT exist")

        print("\n=== Checking for personalization_profiles table ===")
        if 'personalization_profiles' in tables:
            print("[OK] personalization_profiles table exists")
        else:
            print("[X] personalization_profiles table does NOT exist")

        print("\n=== Checking alembic version ===")
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.fetchone()
        if version:
            print(f"Current Alembic version: {version[0]}")
        else:
            print("No alembic_version table found")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_database())
