"""
Robust startup script for Hugging Face Spaces deployment.
Initializes the database and starts the FastAPI server with comprehensive error handling.
"""
import os
import sys
import time
import logging
import asyncio
from pathlib import Path
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking environment variables...")

    required_vars = ['OPENAI_API_KEY', 'OPENROUTER_API_KEY']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.error(f"❌ {var} is not set")
        else:
            logger.info(f"✅ {var} is set")

    # Optional variables
    optional_vars = ['DATABASE_URL', 'QDRANT_URL', 'HF_SPACE_ID']
    for var in optional_vars:
        if os.getenv(var):
            logger.info(f"✅ {var} is set")
        else:
            logger.info(f"⚠️ {var} is not set (optional)")

    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False

    return True

def initialize_database():
    """Initialize the database with retries."""
    logger.info("📦 Initializing database...")
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # Check if init_database.py exists
            if not Path("init_database.py").exists():
                logger.warning("⚠️ init_database.py not found, skipping database initialization")
                return True

            result = subprocess.run(
                [sys.executable, "init_database.py"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("✅ Database initialization completed successfully!")
                if result.stdout:
                    logger.info(f"Database init output: {result.stdout}")
                return True
            else:
                logger.error(f"⚠️ Database initialization attempt {attempt + 1} failed: {result.stderr}")
                if attempt < max_retries - 1:
                    time.sleep(2)

        except subprocess.TimeoutExpired:
            logger.error(f"⚠️ Database initialization timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            logger.error(f"⚠️ Database initialization error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)

    logger.error("❌ Database initialization failed after all attempts")
    return False

def verify_database_file():
    """Check if database file exists and is accessible."""
    db_path = Path("database/auth.db")
    if db_path.exists():
        try:
            size = db_path.stat().st_size
            logger.info(f"✅ Database file found! Size: {size} bytes")
            return True
        except Exception as e:
            logger.error(f"❌ Error accessing database file: {str(e)}")
            return False
    else:
        logger.info("⚠️ Database file not found. The server will create it on startup.")
        return True

def create_directories():
    """Create necessary directories."""
    directories = ['database', 'logs', '.cache/huggingface', '.cache/transformers']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directory {directory} ready")

def start_server():
    """Start the FastAPI server with error handling."""
    logger.info("🌟 Starting FastAPI server...")

    # Get port from environment or use default
    port = int(os.getenv('PORT', 7860))
    host = os.getenv('HOST', '0.0.0.0')
    workers = int(os.getenv('WORKERS', 1))

    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", host,
        "--port", str(port),
        "--workers", str(workers),
        "--log-level", "info",
        "--access-log"
    ]

    logger.info(f"Command: {' '.join(cmd)}")

    try:
        # Replace current process with uvicorn
        os.execvp(sys.executable, cmd)
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        sys.exit(1)

def main():
    """Main startup function."""
    logger.info("🚀 Starting server initialization for Hugging Face Spaces...")
    logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Working directory: {os.getcwd()}")

    # Change to backend directory if needed
    if os.path.exists("backend") and not os.getcwd().endswith("backend"):
        os.chdir("backend")
        logger.info(f"Changed to backend directory: {os.getcwd()}")

    try:
        # Create necessary directories
        create_directories()

        # Check environment
        if not check_environment():
            logger.error("❌ Environment check failed. Exiting...")
            sys.exit(1)

        # Initialize database
        if not initialize_database():
            logger.error("❌ Database initialization failed. Continuing anyway...")

        # Verify database file
        verify_database_file()

        # Print final status
        logger.info("🎉 Initialization completed successfully!")
        logger.info(f"🌍 Environment: {'HF Spaces' if os.getenv('SPACE_ID') else 'Local'}")
        logger.info(f"🔧 Port: {os.getenv('PORT', 7860)}")

        # Start server
        start_server()

    except KeyboardInterrupt:
        logger.info("⏹️ Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error during startup: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()