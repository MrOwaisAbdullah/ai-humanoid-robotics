"""
Re-ingest Book with Correct URLs
This script re-ingests the book content using the updated chunking module that generates correct production URLs.
"""

import os
import sys
from pathlib import Path

# Check if backend directory exists
backend_dir = Path("backend")
if not backend_dir.exists():
    print("Error: backend directory not found!")
    print("Please run this script from the project root directory.")
    sys.exit(1)

# Instructions for the user
print("=" * 70)
print("RE-INGEST BOOK WITH CORRECT URLS")
print("=" * 70)
print("\nThe chunking module has been updated to generate correct production URLs.")
print("Now you need to re-run the ingestion to apply these changes.\n")
print("To re-ingest the book with correct URLs, run one of the following commands:\n")

# Check if we have the right files
ingest_script = backend_dir / "scripts" / "ingest.py"
if ingest_script.exists():
    print("Option 1: Using the backend ingestion script")
    print("=====================================================")
    print(f"cd {backend_dir}")
    print("uv run scripts/ingest.py --content-path ../docs --force-reindex")
    print()
    print("Or with python directly:")
    print("python scripts/ingest.py --content-path ../docs --force-reindex")
    print()

# Alternative: Docker command
print("Option 2: Using Docker (if applicable)")
print("=======================================")
print("docker exec -it your-container-name bash")
print("cd /app/backend")
print("python scripts/ingest.py --content-path /app/docs --force-reindex")
print()

print("=" * 70)
print("IMPORTANT NOTES:")
print("=" * 70)
print("1. Make sure Qdrant is running (http://localhost:6333)")
print("2. The --force-reindex flag will clear and rebuild the collection")
print("3. New URLs will use: https://mrowaisabdullah.github.io/ai-humanoid-robotics/")
print("4. This ensures citations link to the correct GitHub Pages")
print("=" * 70)