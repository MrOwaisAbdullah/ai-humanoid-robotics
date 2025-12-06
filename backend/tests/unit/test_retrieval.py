"""Unit tests for document retrieval functionality."""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from backend.rag.retrieval import RetrievalEngine


class TestRetrievalEngine:
    """Test cases for RetrievalEngine class."""

    @pytest.fixture
    def retrieval_engine(self):
        """Create a retrieval engine instance for testing."""
        mock_qdrant = Mock()
        mock_qdrant.search = AsyncMock(return_value=[])
        mock_embedder = Mock()
        mock_embedder.generate_embedding = AsyncMock(return_value={"embedding": [0.1, 0.2, 0.3] * 512})
        return RetrievalEngine(
            qdrant_manager=mock_qdrant,
            embedder=mock_embedder,
            score_threshold=0.7
        )

    @pytest.fixture
    def sample_chunks(self):
        """Sample document chunks for testing."""
        return [
            {
                "id": "chunk1",
                "payload": {
                    "content": "This is about Physical AI and robotics",
                    "content_hash": "abc123",
                    "file_path": "book/chapter1.md",
                    "section_header": "Introduction",
                    "is_template": False,
                    "token_count": 45
                },
                "score": 0.89
            },
            {
                "id": "chunk2",
                "payload": {
                    "content": "This is about Humanoid Robots design",
                    "content_hash": "def456",
                    "file_path": "book/chapter2.md",
                    "section_header": "Robot Design",
                    "is_template": False,
                    "token_count": 52
                },
                "score": 0.85
            },
            {
                "id": "chunk3",
                "payload": {
                    "content": "How to Use This Book",
                    "content_hash": "abc123",  # Duplicate hash
                    "file_path": "book/intro.md",
                    "section_header": "How to Use This Book",
                    "is_template": True,
                    "token_count": 15
                },
                "score": 0.78
            }
        ]

    def test_similarity_threshold_enforcement(self, retrieval_engine, sample_chunks):
        """Test that similarity threshold is properly enforced."""
        # Mock search results with mixed scores
        retrieval_engine.qdrant_manager.search.return_value = sample_chunks

        # Query with threshold of 0.7
        results = retrieval_engine.retrieve("test query", k=5)

        # Should filter out results below threshold
        for result in results:
            assert result["similarity_score"] >= 0.7, \
                f"Result score {result['similarity_score']} below threshold 0.7"

    def test_deduplication_by_content_hash(self, retrieval_engine, sample_chunks):
        """Test that duplicate chunks are removed."""
        retrieval_engine.qdrant_manager.search.return_value = sample_chunks

        results = retrieval_engine.retrieve("test query", k=10)

        # Should have only 2 results (chunk3 is duplicate of chunk1)
        assert len(results) == 2, f"Expected 2 results after deduplication, got {len(results)}"

        # Check that first result is not marked as duplicate
        assert not results[0]["is_duplicate"], "First occurrence should not be duplicate"

        # Check that duplicate is marked and has lower score
        if len(results) == 2:
            # First result should have higher score
            assert results[0]["similarity_score"] >= results[1]["similarity_score"]

    def test_template_content_filtering(self, retrieval_engine):
        """Test that template content is filtered out."""
        template_chunk = {
            "id": "template1",
            "payload": {
                "content": "How to Use This Book",
                "content_hash": "template123",
                "file_path": "book/intro.md",
                "section_header": "How to Use This Book",
                "is_template": True,
                "token_count": 15
            },
            "score": 0.95
        }

        retrieval_engine.qdrant_manager.search.return_value = [template_chunk]

        # With template filtering enabled (default)
        results = retrieval_engine.retrieve("test query", exclude_templates=True)
        assert len(results) == 0, "Template content should be filtered out"

        # With template filtering disabled
        results = retrieval_engine.retrieve("test query", exclude_templates=False)
        assert len(results) == 1, "Template content should be included when filtering is disabled"

    def test_result_ranking(self, retrieval_engine, sample_chunks):
        """Test that results are properly ranked by similarity score."""
        retrieval_engine.qdrant_manager.search.return_value = sample_chunks

        results = retrieval_engine.retrieve("test query", k=5)

        # Results should be sorted by score (descending)
        for i in range(len(results) - 1):
            assert results[i]["similarity_score"] >= results[i + 1]["similarity_score"], \
                f"Results not properly ranked at index {i}"

    def test_max_results_limit(self, retrieval_engine):
        """Test that max_results limit is respected."""
        # Create more mock results than the limit
        many_results = [
            {
                "id": f"chunk{i}",
                "payload": {
                    "content": f"Content {i}",
                    "content_hash": f"hash{i}",
                    "file_path": f"file{i}.md",
                    "section_header": f"Section {i}",
                    "is_template": False,
                    "token_count": 50
                },
                "score": 0.9 - (i * 0.01)
            }
            for i in range(20)
        ]

        retrieval_engine.qdrant_manager.search.return_value = many_results

        # Request only 5 results
        results = retrieval_engine.retrieve("test query", k=5)

        assert len(results) == 5, f"Expected exactly 5 results, got {len(results)}"

    @pytest.mark.asyncio
    async def test_empty_results_handling(self, retrieval_engine):
        """Test handling when no results are found."""
        retrieval_engine.qdrant_manager.search.return_value = []

        results = await retrieval_engine.retrieve_async("no match query")

        assert len(results) == 0, "Should return empty list when no results found"

    def test_metadata_preservation(self, retrieval_engine, sample_chunks):
        """Test that chunk metadata is preserved in results."""
        retrieval_engine.qdrant_manager.search.return_value = sample_chunks

        results = retrieval_engine.retrieve("test query", k=5)

        for result in results:
            chunk = result["chunk"]
            assert hasattr(chunk, 'content'), "Chunk should have content"
            assert hasattr(chunk, 'metadata'), "Chunk should have metadata"

            # Check required metadata fields
            required_fields = ['content_hash', 'file_path', 'section_header', 'is_template']
            for field in required_fields:
                assert field in chunk.metadata, f"Missing required field: {field}"

    def test_mmr_diversification(self, retrieval_engine):
        """Test Maximal Marginal Relevance (MMR) diversification."""
        # Create similar chunks that would benefit from MMR
        similar_chunks = [
            {
                "id": f"chunk{i}",
                "payload": {
                    "content": "Artificial Intelligence and Machine Learning",
                    "content_hash": f"hash{i}",
                    "file_path": "book/chapter1.md",
                    "section_header": "AI Basics",
                    "is_template": False,
                    "token_count": 50
                },
                "score": 0.9
            }
            for i in range(5)
        ]

        retrieval_engine.qdrant_manager.search.return_value = similar_chunks

        # With MMR enabled
        results = retrieval_engine.retrieve(
            "test query",
            k=3,
            use_mmr=True,
            mmr_lambda=0.5
        )

        # Should still get results, but potentially reordered for diversity
        assert len(results) <= 3, f"MMR should not exceed max_results, got {len(results)}"

    def test_error_handling_on_search_failure(self, retrieval_engine):
        """Test error handling when search fails."""
        retrieval_engine.qdrant_manager.search.side_effect = Exception("Search failed")

        with pytest.raises(Exception):
            retrieval_engine.retrieve("test query")

    def test_content_validation(self, retrieval_engine):
        """Test validation of query content."""
        # Empty query
        with pytest.raises(ValueError):
            retrieval_engine.retrieve("", k=5)

        # Very short query
        with pytest.raises(ValueError):
            retrieval_engine.retrieve("hi", k=5)

    def test_performance_metrics(self, retrieval_engine):
        """Test that performance metrics are tracked."""
        # This is a placeholder - in a real implementation, you'd track
        # metrics like search time, cache hits, etc.
        pass

    @pytest.mark.asyncio
    async def test_concurrent_retrieval(self, retrieval_engine):
        """Test concurrent retrieval requests."""
        import asyncio

        retrieval_engine.qdrant_manager.search.return_value = []

        # Run multiple retrievals concurrently
        queries = ["query 1", "query 2", "query 3"]
        tasks = [retrieval_engine.retrieve_async(q) for q in queries]
        results = await asyncio.gather(*tasks)

        assert len(results) == len(queries), "Should get result for each query"
        for result in results:
            assert isinstance(result, list), "Each result should be a list"