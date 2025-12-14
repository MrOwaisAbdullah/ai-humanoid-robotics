"""
Startup script for Hugging Face Spaces deployment.
Initializes the database and starts the FastAPI server.
"""
import os
import sys
from pathlib import Path

def main():
    """Initialize database and start the server."""
    print("🚀 Starting server initialization...")

    # Initialize database first
    print("📦 Initializing database...")
    os.system("python init_database.py")

    # Check if database initialization was successful
    db_path = Path("database/auth.db")
    if db_path.exists():
        print("✅ Database initialized successfully!")
    else:
        print("⚠️  Database file not found after initialization. The server will create it on startup.")

    # Start the FastAPI server
    print("🌟 Starting FastAPI server...")
    os.system("uvicorn main:app --host 0.0.0.0 --port 7860 --workers 1")


if __name__ == "__main__":
    main()