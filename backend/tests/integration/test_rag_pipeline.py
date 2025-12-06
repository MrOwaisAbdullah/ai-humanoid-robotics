"""Integration tests for the complete RAG pipeline."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
from backend.rag.ingestion import DocumentIngestor
from backend.rag.retrieval import RetrievalEngine
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.qdrant_client import QdrantManager


class TestRAGPipeline:
    """Integration tests for the complete RAG pipeline."""

    @pytest.fixture
    async def test_environment(self):
        """Set up test environment with temporary files."""
        # Create temporary directory for test documents
        self.temp_dir = tempfile.mkdtemp()

        # Create sample markdown files
        sample_files = {
            "chapter1.md": """
# Chapter 1: Introduction to Physical AI

Physical AI represents the convergence of artificial intelligence and robotics in physical systems.

## 1.1 What is Physical AI?

Physical AI refers to AI systems that can perceive, reason about, and interact with the physical world through robotic bodies.

## 1.2 Key Components

The main components of Physical AI include:
- Perception systems
- Decision-making algorithms
- Actuation mechanisms
""",
            "chapter2.md": """
# Chapter 2: Humanoid Robots

Humanoid robots are designed to mimic human form and function.

## 2.1 Design Principles

Humanoid robot design follows several key principles.
""",
            "template.md": """
# How to Use This Book

This section explains how to use this book effectively.

## Getting Started

Follow these steps to get started.
"""
        }

        # Write files to temp directory
        for filename, content in sample_files.items():
            filepath = Path(self.temp_dir) / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        yield self.temp_dir

        # Cleanup
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_qdrant(self):
        """Create a mock Qdrant client."""
        mock_client = AsyncMock()
        mock_client.upsert.return_value = {"operation_id": "test-op-123"}
        mock_client.search.return_value = []
        mock_client.delete_collection.return_value = True
        mock_client.create_collection.return_value = True
        return mock_client

    @pytest.fixture
    def mock_openai(self):
        """Create a mock OpenAI client."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.data = [
            AsyncMock(embedding=[0.1, 0.2, 0.3] * 512)  # 1536 dimensions
        ]
        mock_client.embeddings.create.return_value = mock_response
        return mock_client

    @pytest.mark.asyncio
    async def test_end_to_end_ingestion_and_retrieval(self, test_environment, mock_qdrant, mock_openai):
        """Test the complete pipeline from ingestion to retrieval."""

        # Initialize components
        qdrant_manager = QdrantManager(
            client=mock_qdrant,
            collection_name="test_collection"
        )

        with patch('backend.rag.embeddings.AsyncOpenAI', return_value=mock_openai):
            embedder = EmbeddingGenerator(api_key="test-key")

        ingestor = DocumentIngestor(
            qdrant_manager=qdrant_manager,
            embedder=embedder,
            chunk_size=600,
            chunk_overlap=100
        )

        # Step 1: Ingest documents
        ingestion_job = await ingestor.ingest_directory(
            directory_path=test_environment,
            force_reindex=True
        )

        # Verify ingestion completed
        assert ingestion_job.status == "completed", "Ingestion should complete successfully"
        assert ingestion_job.files_processed == 3, "Should process 3 files"
        assert ingestion_job.chunks_created > 0, "Should create chunks"

        # Step 2: Test retrieval
        retrieval_engine = RetrievalEngine(
            qdrant_client=mock_qdrant,
            collection_name="test_collection",
            similarity_threshold=0.7
        )

        # Mock search results
        mock_qdrant.search.return_value = [
            {
                "id": "chunk1",
                "payload": {
                    "content": "Physical AI represents the convergence of artificial intelligence",
                    "content_hash": "abc123",
                    "file_path": "chapter1.md",
                    "section_header": "Introduction to Physical AI",
                    "is_template": False,
                    "token_count": 45
                },
                "score": 0.89
            }
        ]

        # Test retrieval
        results = retrieval_engine.retrieve(
            query="What is Physical AI?",
            max_results=5,
            exclude_templates=True
        )

        assert len(results) > 0, "Should retrieve results"
        assert results[0].similarity_score >= 0.7, "Results should meet threshold"

    @pytest.mark.asyncio
    async def test_template_filtering(self, test_environment, mock_qdrant, mock_openai):
        """Test that template content is properly filtered during retrieval."""

        # Setup components
        qdrant_manager = QdrantManager(client=mock_qdrant, collection_name="test_collection")

        with patch('backend.rag.embeddings.AsyncOpenAI', return_value=mock_openai):
            embedder = EmbeddingGenerator(api_key="test-key")

        ingestor = DocumentIngestor(
            qdrant_manager=qdrant_manager,
            embedder=embedder,
            chunk_size=600
        )

        # Ingest documents (including template)
        await ingestor.ingest_directory(
            directory_path=test_environment,
            force_reindex=True
        )

        # Mock search results including template
        mock_qdrant.search.return_value = [
            {
                "id": "content1",
                "payload": {
                    "content": "Physical AI represents the convergence",
                    "content_hash": "hash1",
                    "file_path": "chapter1.md",
                    "section_header": "Introduction",
                    "is_template": False,
                    "token_count": 40
                },
                "score": 0.89
            },
            {
                "id": "template1",
                "payload": {
                    "content": "How to Use This Book",
                    "content_hash": "hash2",
                    "file_path": "template.md",
                    "section_header": "How to Use This Book",
                    "is_template": True,
                    "token_count": 20
                },
                "score": 0.78
            }
        ]

        # Test retrieval with template filtering
        retrieval_engine = RetrievalEngine(
            qdrant_client=mock_qdrant,
            collection_name="test_collection"
        )

        results = retrieval_engine.retrieve(
            query="test query",
            exclude_templates=True
        )

        # Should not include template content
        template_results = [r for r in results if r.chunk.metadata.get('is_template')]
        assert len(template_results) == 0, "Template content should be filtered out"

    @pytest.mark.asyncio
    async def test_deduplication(self, test_environment, mock_qdrant, mock_openai):
        """Test that duplicate content is deduplicated during retrieval."""

        # Setup components
        qdrant_manager = QdrantManager(client=mock_qdrant, collection_name="test_collection")

        with patch('backend.rag.embeddings.AsyncOpenAI', return_value=mock_openai):
            embedder = EmbeddingGenerator(api_key="test-key")

        # Create duplicate chunks with same content but different sources
        duplicate_results = [
            {
                "id": "chunk1",
                "payload": {
                    "content": "Physical AI represents the convergence of artificial intelligence",
                    "content_hash": "same_hash",  # Same hash!
                    "file_path": "chapter1.md",
                    "section_header": "Introduction",
                    "is_template": False,
                    "token_count": 40
                },
                "score": 0.89
            },
            {
                "id": "chunk2",
                "payload": {
                    "content": "Physical AI represents the convergence of artificial intelligence",
                    "content_hash": "same_hash",  # Same hash!
                    "file_path": "chapter1_duplicate.md",
                    "section_header": "Introduction",
                    "is_template": False,
                    "token_count": 40
                },
                "score": 0.87
            }
        ]

        mock_qdrant.search.return_value = duplicate_results

        # Test retrieval with deduplication
        retrieval_engine = RetrievalEngine(
            qdrant_client=mock_qdrant,
            collection_name="test_collection"
        )

        results = retrieval_engine.retrieve("test query")

        # Should only have one result after deduplication
        assert len(results) == 1, f"Expected 1 result after deduplication, got {len(results)}"
        assert not results[0].is_duplicate, "First occurrence should not be duplicate"

    @pytest.mark.asyncio
    async def test_similarity_threshold_enforcement(self, mock_qdrant):
        """Test that similarity threshold is properly enforced."""

        # Mock results with mixed scores
        mixed_results = [
            {
                "id": "high1",
                "payload": {"content": "High similarity content"},
                "score": 0.85
            },
            {
                "id": "medium1",
                "payload": {"content": "Medium similarity content"},
                "score": 0.75
            },
            {
                "id": "low1",
                "payload": {"content": "Low similarity content"},
                "score": 0.65  # Below threshold
            },
            {
                "id": "low2",
                "payload": {"content": "Another low similarity"},
                "score": 0.60  # Below threshold
            }
        ]

        mock_qdrant.search.return_value = mixed_results

        retrieval_engine = RetrievalEngine(
            qdrant_client=mock_qdrant,
            collection_name="test_collection",
            similarity_threshold=0.7
        )

        results = retrieval_engine.retrieve("test query")

        # Should only include results at or above threshold
        for result in results:
            assert result.similarity_score >= 0.7,
                f"Result score {result.similarity_score} below threshold 0.7"

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_qdrant):
        """Test error handling in the pipeline."""

        # Test ingestion errors
        qdrant_manager = QdrantManager(client=mock_qdrant, collection_name="test_collection")

        with patch('backend.rag.embeddings.AsyncOpenAI') as mock_openai:
            mock_openai.return_value.embeddings.create.side_effect = Exception("API Error")

            embedder = EmbeddingGenerator(api_key="test-key")
            ingestor = DocumentIngestor(
                qdrant_manager=qdrant_manager,
                embedder=embedder
            )

            # Should handle ingestion errors gracefully
            with pytest.raises(Exception):
                await ingestor.ingest_directory("/nonexistent/path")

        # Test retrieval errors
        mock_qdrant.search.side_effect = Exception("Search Error")

        retrieval_engine = RetrievalEngine(
            qdrant_client=mock_qdrant,
            collection_name="test_collection"
        )

        with pytest.raises(Exception):
            retrieval_engine.retrieve("test query")

    @pytest.mark.asyncio
    async def test_performance_metrics(self, test_environment, mock_qdrant, mock_openai):
        """Test that performance metrics are collected."""

        # Setup components with monitoring
        qdrant_manager = QdrantManager(client=mock_qdrant, collection_name="test_collection")

        with patch('backend.rag.embeddings.AsyncOpenAI', return_value=mock_openai):
            embedder = EmbeddingGenerator(api_key="test-key")
            ingestor = DocumentIngestor(
                qdrant_manager=qdrant_manager,
                embedder=embedder
            )

            # Track ingestion metrics
            start_time = asyncio.get_event_loop().time()

            job = await ingestor.ingest_directory(
                directory_path=test_environment,
                force_reindex=True
            )

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            # Verify metrics
            assert job.files_processed > 0, "Should have processed files"
            assert job.chunks_created > 0, "Should have created chunks"
            assert duration < 30, f"Ingestion should complete quickly, took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_empty_result_handling(self, mock_qdrant):
        """Test handling when no results are found."""

        mock_qdrant.search.return_value = []

        retrieval_engine = RetrievalEngine(
            qdrant_client=mock_qdrant,
            collection_name="test_collection"
        )

        results = retrieval_engine.retrieve("no matching query")

        assert len(results) == 0, "Should return empty list when no results found"