#!/usr/bin/env python3
"""Test script to check chunking output."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from rag.chunking import MarkdownChunker
from rag.embeddings import EmbeddingGenerator
from rag.qdrant_client import QdrantManager

async def test_chunking():
    load_dotenv()

    # Initialize chunker
    chunker = MarkdownChunker(target_chunk_size=1000, overlap_size=200)

    # Find a markdown file
    docs_path = Path("../docs")
    md_files = list(docs_path.glob("*.md"))

    if not md_files:
        print("No markdown files found in docs directory")
        return

    test_file = md_files[0]
    print(f"Testing with file: {test_file}")

    # Chunk the document
    chunks = chunker.chunk_document(str(test_file))
    chunks = chunker.add_code_blocks_as_chunks(chunks)

    print(f"Created {len(chunks)} chunks")

    # Check first few chunks
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i + 1}:")
        print(f"  Length: {len(chunk.content)}")
        print(f"  Token count: {chunk.token_count}")
        print(f"  Metadata keys: {list(chunk.metadata.keys())}")
        print(f"  Has URL: {'url' in chunk.metadata}")
        if 'url' in chunk.metadata:
            print(f"  URL: {chunk.metadata['url']}")
        print(f"  Content preview: {chunk.content[:100]}...")

    # Test embedding generation
    print("\n\nTesting embedding generation...")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    embedder = EmbeddingGenerator(
        api_key=openai_api_key,
        model="text-embedding-3-small",
        batch_size=2
    )

    # Prepare chunks for embedding
    chunk_texts = [chunk.content for chunk in chunks[:5]]
    metadata_list = [chunk.metadata for chunk in chunks[:5]]

    embeddings = await embedder.generate_batch_embeddings(chunk_texts, metadata_list)

    print(f"Generated {len(embeddings)} embeddings")

    # Check embedding results
    for i, emb in enumerate(embeddings):
        if emb.get('embedding'):
            print(f"  Embedding {i}: OK (length: {len(emb['embedding'])})")
        else:
            print(f"  Embedding {i}: FAILED - {emb.get('error', 'Unknown error')}")

    # Prepare chunks like ingestion does
    prepared_chunks = []
    for i, (chunk, embedding_result) in enumerate(zip(chunks[:5], embeddings)):
        if embedding_result.get('embedding'):
            chunk_dict = {
                "text": chunk.content,
                "embedding": embedding_result["embedding"],
                "metadata": {
                    **chunk.metadata,
                    "chunk_id": chunk.chunk_id,
                    "ingested_at": "2024-01-01T00:00:00"
                }
            }
            prepared_chunks.append(chunk_dict)

    print(f"\nPrepared {len(prepared_chunks)} chunks for storage")

    # Test storage
    print("\nTesting storage...")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    qdrant_manager = QdrantManager(url=qdrant_url, api_key=qdrant_api_key)
    await qdrant_manager.initialize()

    # Clear and recreate collection
    await qdrant_manager.delete_collection()
    await qdrant_manager.ensure_collection_exists()

    # Store chunks
    result = await qdrant_manager.store_chunks(prepared_chunks, batch_size=2)
    print(f"Storage result: {result}")

    # Check stats
    stats = await qdrant_manager.get_collection_stats()
    print(f"Collection stats: {stats}")

    await embedder.close()
    await qdrant_manager.close()

    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_chunking())