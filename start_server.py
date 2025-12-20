"""
Startup script for Hugging Face Spaces deployment.
Initializes the database and starts the FastAPI server.
"""
import os
import sys
from pathlib import Path
import subprocess

def main():
    """Initialize database and start the server."""
    print("🚀 Starting server initialization...")

    # Change to backend directory if needed
    if os.path.exists("backend"):
        os.chdir("backend")
        print("Changed to backend directory")

    # Initialize database first
    print("📦 Initializing database...")
    result = subprocess.run([sys.executable, "init_database.py"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Database initialization completed successfully!")
    else:
        print(f"⚠️ Database initialization failed: {result.stderr}")

    # Check if database file exists
    db_path = Path("database/auth.db")
    if db_path.exists():
        print("✅ Database file found!")
    else:
        print("⚠️ Database file not found. The server will create it on startup.")

    # Print environment variables for debugging
    print("🔍 Environment check:")
    print(f"  - OPENAI_API_KEY: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    print(f"  - OPENROUTER_API_KEY: {'✅' if os.getenv('OPENROUTER_API_KEY') else '❌'}")
    print(f"  - DATABASE_URL: {'✅' if os.getenv('DATABASE_URL') else '❌'}")

    # Start the FastAPI server
    print("🌟 Starting FastAPI server...")
    os.execvp(sys.executable, [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"])


if __name__ == "__main__":
    main()