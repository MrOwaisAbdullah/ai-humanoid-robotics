#!/usr/bin/env python3
"""Test script to debug the storage issue."""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from rag.embeddings import EmbeddingGenerator
from rag.qdrant_client import QdrantManager
from qdrant_client.models import PointStruct

async def test_storage():
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    print("Initializing components...")

    # Initialize Qdrant manager
    qdrant_manager = QdrantManager(
        url=qdrant_url,
        api_key=qdrant_api_key
    )
    await qdrant_manager.initialize()

    # Clear collection first
    await qdrant_manager.delete_collection()
    await qdrant_manager.ensure_collection_exists()

    # Initialize embedder
    embedder = EmbeddingGenerator(
        api_key=openai_api_key,
        model="text-embedding-3-small",
        batch_size=2
    )

    # Create test chunks
    test_texts = [
        "This is the first test chunk about robotics and AI.",
        "This is the second test chunk about machine learning and neural networks.",
        "This is the third test chunk about computer vision and perception."
    ]

    # Generate embeddings
    print("Generating embeddings...")
    embeddings = await embedder.generate_batch_embeddings(test_texts)

    print(f"Generated {len(embeddings)} embeddings")

    # Check what we got
    for i, emb in enumerate(embeddings):
        if emb.get('embedding'):
            print(f"  Embedding {i}: OK (length: {len(emb['embedding'])})")
        else:
            print(f"  Embedding {i}: FAILED - {emb.get('error', 'Unknown error')}")

    # Prepare chunks like the ingestion does
    chunks = []
    for i, (text, embedding_result) in enumerate(zip(test_texts, embeddings)):
        if embedding_result.get('embedding'):
            chunk = {
                "text": text,
                "embedding": embedding_result["embedding"],
                "metadata": {
                    "chunk_id": f"test-chunk-{i}",
                    "file_path": "test.md",
                    "url": "https://mrowaisabdullah.github.io/ai-humanoid-robotics/docs/test",
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            chunks.append(chunk)

    print(f"\nPrepared {len(chunks)} chunks for storage")

    # Store chunks
    print("\nStoring chunks...")
    result = await qdrant_manager.store_chunks(chunks, batch_size=2)

    print(f"\nStorage result: {result}")

    # Check collection stats
    stats = await qdrant_manager.get_collection_stats()
    print(f"Collection stats: {stats}")

    # Test search
    print("\nTesting search...")
    query_embedding = embeddings[0]["embedding"]
    search_results = await qdrant_manager.search_similar(
        query_embedding=query_embedding,
        limit=5
    )

    print(f"Found {len(search_results)} results")
    for result in search_results:
        print(f"  - Score: {result['score']:.4f}, Content: {result['content'][:50]}...")

    # Close connections
    await embedder.close()
    await qdrant_manager.close()

    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_storage())