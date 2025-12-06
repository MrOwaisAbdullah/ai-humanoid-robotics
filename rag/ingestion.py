"""
Document ingestion system for RAG.

Handles loading, chunking, embedding generation, and storage of Markdown documents.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from .chunking import MarkdownChunker
from .embeddings import EmbeddingGenerator
from .qdrant_client import QdrantManager

logger = logging.getLogger(__name__)


class DocumentIngestor:
    """Handles ingestion of Markdown documents into the RAG system."""

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        chunker: Optional[MarkdownChunker] = None,
        embedder: Optional[EmbeddingGenerator] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        batch_size: int = 100
    ):
        self.qdrant_manager = qdrant_manager
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        self.chunker = chunker or MarkdownChunker(
            target_chunk_size=600,  # Updated to 600 tokens
            overlap_size=100,     # Updated to 100 tokens overlap
            min_chunk_size=50     # Minimum 50 tokens
        )
        self.embedder = embedder
        self.ingestion_stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "errors": []
        }

        # Initialize embedder if not provided
        if not self.embedder:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.embedder = EmbeddingGenerator(api_key=api_key)

    async def ingest_directory(
        self,
        directory_path: str,
        pattern: str = "*.md*",
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest all Markdown files in a directory.

        Args:
            directory_path: Path to directory containing Markdown files
            pattern: File pattern to match (default: "*.md")
            recursive: Whether to search recursively in subdirectories

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting ingestion of directory: {directory_path}")

        # Reset stats
        self.ingestion_stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "chunks_skipped": 0,  # Track template chunks skipped
            "embeddings_generated": 0,
            "errors": [],
            "start_time": datetime.utcnow().isoformat()
        }

        try:
            # Find all Markdown files
            md_files = self._find_markdown_files(directory_path, pattern, recursive)
            logger.info(f"Found {len(md_files)} Markdown files to process")

            if not md_files:
                logger.warning(f"No Markdown files found in {directory_path}")
                return {
                    **self.ingestion_stats,
                    "message": "No Markdown files found"
                }

            # Process all files
            all_chunks = []
            for file_path in md_files:
                try:
                    chunks = await self._process_file(file_path)
                    all_chunks.extend(chunks)
                    self.ingestion_stats["files_processed"] += 1
                except Exception as e:
                    error_msg = f"Failed to process file {file_path}: {str(e)}"
                    logger.error(error_msg)
                    self.ingestion_stats["errors"].append(error_msg)

            self.ingestion_stats["chunks_created"] = len(all_chunks)
            logger.info(f"Created {len(all_chunks)} chunks from {self.ingestion_stats['files_processed']} files")

            # Generate embeddings for all chunks
            if all_chunks:
                embeddings = await self._generate_embeddings(all_chunks)
                self.ingestion_stats["embeddings_generated"] = len(
                    [e for e in embeddings if e.get("embedding")]
                )

                # Store in Qdrant
                storage_result = await self.qdrant_manager.store_chunks(embeddings)
                self.ingestion_stats["storage_result"] = storage_result

                # Update stats with storage errors
                self.ingestion_stats["errors"].extend(storage_result.get("errors", []))

            # Add completion time
            self.ingestion_stats["end_time"] = datetime.utcnow().isoformat()
            self.ingestion_stats["success"] = len(self.ingestion_stats["errors"]) == 0

            logger.info(f"Ingestion completed: {self.ingestion_stats}")
            return self.ingestion_stats

        except Exception as e:
            error_msg = f"Directory ingestion failed: {str(e)}"
            logger.error(error_msg)
            self.ingestion_stats["errors"].append(error_msg)
            self.ingestion_stats["success"] = False
            self.ingestion_stats["end_time"] = datetime.utcnow().isoformat()
            return self.ingestion_stats

    async def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest a single Markdown file."""
        logger.info(f"Ingesting file: {file_path}")

        stats = {
            "file_path": file_path,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "errors": []
        }

        try:
            # Process file
            chunks = await self._process_file(file_path)
            stats["chunks_created"] = len(chunks)

            # Generate embeddings
            embeddings = await self._generate_embeddings(chunks)
            stats["embeddings_generated"] = len(
                [e for e in embeddings if e.get("embedding")]
            )

            # Store in Qdrant
            storage_result = await self.qdrant_manager.store_chunks(embeddings)
            stats["storage_result"] = storage_result
            stats["errors"] = storage_result.get("errors", [])
            stats["success"] = len(stats["errors"]) == 0

            logger.info(f"File ingestion completed: {stats}")
            return stats

        except Exception as e:
            error_msg = f"File ingestion failed: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            stats["success"] = False
            return stats

    def _find_markdown_files(
        self,
        directory_path: str,
        pattern: str = "*.md*",
        recursive: bool = True
    ) -> List[str]:
        """Find all Markdown files in directory."""
        path = Path(directory_path)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        # Filter only files (not directories)
        return [str(f) for f in files if f.is_file()]

    async def _process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a single file and return chunks."""
        logger.debug(f"Processing file: {file_path}")

        # Create chunks (template filtering is handled inside chunk_document)
        chunks = self.chunker.chunk_document(file_path)

        # Add code blocks as separate chunks
        chunks = self.chunker.add_code_blocks_as_chunks(chunks)

        # Note: Template filtering is already handled in chunk_document()
        # The chunker returns [] for template sections, so no additional filtering needed

        # Convert chunks to dictionaries with additional metadata
        chunk_dicts = []
        for chunk in chunks:
            chunk_dict = {
                "text": chunk.content,
                "metadata": {
                    **chunk.metadata,
                    "file_path": file_path,
                    "relative_path": os.path.relpath(file_path),
                    "file_name": os.path.basename(file_path),
                    "chunk_id": chunk.chunk_id,
                    "token_count": chunk.token_count,
                    "ingested_at": datetime.utcnow().isoformat()
                }
            }
            chunk_dicts.append(chunk_dict)

        logger.debug(f"Created {len(chunk_dicts)} chunks from {file_path}")
        return chunk_dicts

    async def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for chunks."""
        if not chunks:
            return []

        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Extract texts and metadata
        texts = [chunk["text"] for chunk in chunks]
        metadata_list = [chunk.get("metadata", {}) for chunk in chunks]

        # Generate embeddings in batches
        embeddings = await self.embedder.generate_batch_embeddings(
            texts,
            metadata_list
        )

        # Add original chunk data to embedding results
        for i, embedding_result in enumerate(embeddings):
            if i < len(chunks):
                embedding_result["chunk_data"] = chunks[i]

        successful_embeddings = [e for e in embeddings if e.get("embedding")]
        logger.info(f"Successfully generated {len(successful_embeddings)} embeddings")

        return embeddings

    async def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get current ingestion statistics."""
        # Add collection stats
        collection_stats = await self.qdrant_manager.get_collection_stats()
        self.ingestion_stats["collection_stats"] = collection_stats

        return self.ingestion_stats

    async def reindex_all(
        self,
        directory_path: str,
        clear_existing: bool = True
    ) -> Dict[str, Any]:
        """Reindex all documents from scratch."""
        logger.info(f"Starting reindex with clear_existing={clear_existing}")

        try:
            if clear_existing:
                # Delete and recreate collection
                logger.info("Clearing existing collection...")
                await self.qdrant_manager.delete_collection()
                await self.qdrant_manager.ensure_collection_exists()

            # Run full ingestion
            result = await self.ingest_directory(directory_path)
            result["reindexed"] = True
            return result

        except Exception as e:
            error_msg = f"Reindex failed: {str(e)}"
            logger.error(error_msg)
            return {
                "reindexed": False,
                "error": error_msg,
                "success": False
            }