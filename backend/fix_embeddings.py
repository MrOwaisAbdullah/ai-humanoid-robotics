"""
Script to clear existing embeddings and re-ingest with consistent dimensions.
"""

import asyncio
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Load environment
load_dotenv()

# Get Qdrant configuration
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

print(f"Connecting to Qdrant at: {qdrant_url}")

# Initialize client
if qdrant_url and qdrant_url.startswith("http"):
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
else:
    client = QdrantClient(path="qdrant_db")

async def fix_embeddings():
    """Clear and recreate the collection with correct dimensions."""

    collection_name = "robotics_book"

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name in collection_names:
            print(f"\n[INFO] Found collection '{collection_name}'")

            # Get collection info
            info = client.get_collection(collection_name)
            print(f"   Points: {info.points_count}")
            print(f"   Vector size: {info.config.params.vectors.size}")

            # Delete the collection to clear mixed dimensions
            print(f"\n[INFO] Deleting collection '{collection_name}'...")
            client.delete_collection(collection_name)
            print("   [OK] Collection deleted")
        else:
            print(f"\n[INFO] Collection '{collection_name}' not found")

        # Recreate collection with correct dimensions (1536 for text-embedding-3-small)
        print(f"\n[INFO] Creating collection '{collection_name}' with 1536 dimensions...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,  # OpenAI text-embedding-3-small dimensions
                distance=Distance.COSINE
            )
        )
        print("   [OK] Collection created successfully")

        print("\n[SUCCESS] Embeddings fixed! Now run the ingestion script:")
        print("   python scripts/ingest.py ../docs")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_embeddings())