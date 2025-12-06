#!/usr/bin/env python3
"""
Test script to check RAG system status and document retrieval.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from rag.qdrant_client import QdrantManager
from rag.embeddings import EmbeddingGenerator
from dotenv import load_dotenv

load_dotenv()

async def check_system():
    """Check RAG system status."""
    print("=" * 60)
    print("RAG SYSTEM STATUS CHECK")
    print("=" * 60)

    # Check environment variables
    print("\n1. Checking environment variables:")
    print(f"   OPENAI_API_KEY: {'[OK] Configured' if os.getenv('OPENAI_API_KEY') else '[ERROR] Missing'}")
    print(f"   QDRANT_URL: {os.getenv('QDRANT_URL', 'Not set')}")
    print(f"   BOOK_CONTENT_PATH: {os.getenv('BOOK_CONTENT_PATH', 'Not set')}")

    # Initialize Qdrant manager
    print("\n2. Connecting to Qdrant...")
    try:
        qdrant_manager = QdrantManager(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        await qdrant_manager.initialize()
        print("   [OK] Connected to Qdrant")

        # List collections
        collections = await qdrant_manager.list_collections()
        print(f"   Collections: {collections}")

        # Get collection stats
        stats = await qdrant_manager.get_collection_stats()
        print(f"   Collection stats: {stats}")

        if stats.get("vector_count", 0) == 0:
            print("   [WARNING] No documents found in collection!")
            print("\n   POSSIBLE SOLUTIONS:")
            print("   1. Run ingestion: python scripts/ingest.py --content-path ./book_content --force-reindex")
            print("   2. Check if BOOK_CONTENT_PATH is correct")
            print("   3. Verify documents exist at the specified path")
        else:
            print(f"   [OK] Found {stats.get('vector_count', 0)} documents in collection")

            # Test search
            print("\n3. Testing document search...")
            try:
                # Initialize embedder
                embedder = EmbeddingGenerator(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model="text-embedding-3-small"
                )

                # Generate query embedding
                test_query = "What is humanoid robotics?"
                query_result = await embedder.generate_embedding(test_query)
                query_embedding = query_result["embedding"]

                # Search for similar documents
                search_results = await qdrant_manager.search_similar(
                    query_embedding=query_embedding,
                    limit=3,
                    score_threshold=0.1  # Very low threshold to get any results
                )

                print(f"   Query: {test_query}")
                print(f"   Results found: {len(search_results)}")

                if search_results:
                    print("\n   Top results:")
                    for i, result in enumerate(search_results):
                        score = result.get("score", 0)
                        content = result.get("content", "")[:200] + "..."
                        file_name = result.get("metadata", {}).get("file_name", "unknown")
                        print(f"\n   Result {i+1}:")
                        print(f"     Score: {score:.4f}")
                        print(f"     File: {file_name}")
                        print(f"     Content: {content}")
                else:
                    print("   [WARNING] No documents retrieved even with low threshold!")

            except Exception as e:
                print(f"   [ERROR] Search test failed: {str(e)}")

        await qdrant_manager.close()

    except Exception as e:
        print(f"   [ERROR] Failed to connect to Qdrant: {str(e)}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(check_system())