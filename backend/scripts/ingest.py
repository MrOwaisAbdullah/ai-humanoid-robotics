#!/usr/bin/env python3
"""
Standalone ingestion script for RAG backend.

Usage with uv:
    uv run rag-ingest --content-path ./book_content
    uv run rag-ingest --content-path ./book_content --force-reindex
    uv run rag-ingest --content-path ./book_content --batch-size 50

Usage with python:
    python scripts/ingest.py --content-path ./book_content
    python scripts/ingest.py --content-path ./book_content --force-reindex
    python scripts/ingest.py --content-path ./book_content --batch-size 50
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from rag.ingestion import DocumentIngestor
from rag.qdrant_client import QdrantManager
from rag.embeddings import EmbeddingGenerator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(description='Ingest documents into RAG system')
    parser.add_argument(
        '--content-path',
        type=str,
        default='./book_content',
        help='Path to directory containing Markdown files'
    )
    parser.add_argument(
        '--force-reindex',
        action='store_true',
        help='Clear existing collection and reindex all documents'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing (default: 100)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Target chunk size in tokens (default: 1000)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='Chunk overlap in tokens (default: 200)'
    )
    parser.add_argument(
        '--qdrant-url',
        type=str,
        default=None,
        help='Qdrant server URL (overrides environment variable)'
    )
    parser.add_argument(
        '--qdrant-api-key',
        type=str,
        default=None,
        help='Qdrant API key (overrides environment variable)'
    )

    args = parser.parse_args()

    # Validate content path
    content_path = Path(args.content_path)
    if not content_path.exists():
        logger.error(f"Content path does not exist: {content_path}")
        sys.exit(1)

    if not content_path.is_dir():
        logger.error(f"Content path is not a directory: {content_path}")
        sys.exit(1)

    # Get configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable is required")
        sys.exit(1)

    qdrant_url = args.qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = args.qdrant_api_key or os.getenv("QDRANT_API_KEY")

    logger.info(f"Starting ingestion from: {content_path}")
    logger.info(f"Force reindex: {args.force_reindex}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Chunk size: {args.chunk_size}")
    logger.info(f"Chunk overlap: {args.chunk_overlap}")

    try:
        # Initialize Qdrant manager
        logger.info("Initializing Qdrant manager...")
        qdrant_manager = QdrantManager(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        await qdrant_manager.initialize()

        # Force reindex if requested
        if args.force_reindex:
            logger.info("Clearing existing collection...")
            await qdrant_manager.delete_collection()
            await qdrant_manager.ensure_collection_exists()

        # Initialize embedder
        logger.info("Initializing embedding generator...")
        embedder = EmbeddingGenerator(
            api_key=openai_api_key,
            model="text-embedding-3-small",
            batch_size=args.batch_size
        )

        # Initialize document ingestor
        logger.info("Initializing document ingestor...")
        ingestor = DocumentIngestor(
            qdrant_manager=qdrant_manager,
            embedder=embedder,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size
        )

        # Start ingestion
        logger.info("Starting document ingestion...")
        start_time = asyncio.get_event_loop().time()

        result = await ingestor.ingest_directory(
            directory_path=str(content_path),
            pattern="*.md",
            recursive=True
        )

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Report results
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Files processed: {result.get('files_processed', 0)}")
        logger.info(f"Chunks created: {result.get('chunks_created', 0)}")
        logger.info(f"Embeddings generated: {result.get('embeddings_generated', 0)}")

        errors = result.get('errors', [])
        if errors:
            logger.warning(f"Encountered {len(errors)} errors:")
            for i, error in enumerate(errors[:5]):  # Show first 5 errors
                logger.warning(f"  {i+1}. {error}")
            if len(errors) > 5:
                logger.warning(f"  ... and {len(errors) - 5} more errors")

        # Get collection stats
        stats = await qdrant_manager.get_collection_stats()
        logger.info(f"Collection stats: {stats}")

        # Close connections
        await embedder.close()
        await qdrant_manager.close()

        logger.info("Ingestion completed successfully!")

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())