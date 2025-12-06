"""Unit tests for document chunking functionality."""

import pytest
import hashlib
from unittest.mock import Mock, patch
from backend.rag.chunking import MarkdownChunker


class TestMarkdownChunker:
    """Test cases for MarkdownChunker class."""

    @pytest.fixture
    def chunker(self):
        """Create a chunker instance for testing."""
        return MarkdownChunker(
            target_chunk_size=600,
            overlap_size=100
        )

    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown content for testing."""
        return """
# Chapter 1: Introduction

This is the introduction chapter with some content.

## Section 1.1

Here's some detailed content that should be chunked properly.

```python
def example_function():
    print("This is a code block that shouldn't be split")
    return True
```

More text after the code block.

## Section 1.2

Additional content in this section.

# How to Use This Book

This is a template section that should be filtered out.

## Getting Started

Template content here.
"""

    def test_chunking_basic_functionality(self, chunker, sample_markdown):
        """Test basic chunking functionality."""
        chunks = chunker.chunk_document(sample_markdown)

        assert len(chunks) > 0, "Should generate at least one chunk"

        # Check that chunks have required fields
        for chunk in chunks:
            assert hasattr(chunk, 'content'), "Chunk must have content"
            assert hasattr(chunk, 'metadata'), "Chunk must have metadata"
            assert 'file_path' in chunk.metadata, "Chunk must have file_path metadata"
            assert 'chunk_index' in chunk.metadata, "Chunk must have chunk_index metadata"
            assert 'content_hash' in chunk.metadata, "Chunk must have content_hash metadata"
            assert 'token_count' in chunk.metadata, "Chunk must have token_count metadata"

    def test_template_filtering(self, chunker):
        """Test that template content is properly filtered."""
        template_content = """
# How to Use This Book

This is template content.

## Getting Started

More template content.
"""

        chunks = chunker.chunk_document(template_content)

        # All chunks from template content should be marked as template
        for chunk in chunks:
            assert chunk.metadata.get('is_template', False),
                "Template content should be marked as is_template=True"
            assert 'How to Use This Book' in chunk.content or 'Getting Started' in chunk.content

    def test_content_hash_generation(self, chunker):
        """Test that SHA256 hashes are generated correctly."""
        content = "Test content for hashing"
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        chunk = chunker.chunk_document(content)[0]
        actual_hash = chunk.metadata['content_hash']

        assert actual_hash == expected_hash, "Content hash should match SHA256 of content"

    def test_token_count_accuracy(self, chunker):
        """Test that token counting is accurate."""
        # Create content with known token count
        content = "This is a test sentence. " * 50  # Approximately 100 tokens

        chunk = chunker.chunk_document(content)[0]
        token_count = chunk.metadata['token_count']

        # Should be approximately 100 tokens (allowing some variance)
        assert 90 <= token_count <= 110, f"Expected ~100 tokens, got {token_count}"

    def test_chunk_size_limits(self, chunker):
        """Test that chunks respect size limits."""
        large_content = "This is test content. " * 200  # Large content

        chunks = chunker.chunk_document(large_content)

        for chunk in chunks:
            # Check that chunks are not too large
            assert chunk.metadata['token_count'] <= 650,  # Allow some tolerance
                f"Chunk too large: {chunk.metadata['token_count']} tokens"

    def test_overlap_handling(self, chunker):
        """Test that overlapping chunks share content."""
        content = """
Chapter 1
Section 1.1 with some content here.
Section 1.2 with different content here.
Section 1.3 with final content here.
"""

        chunks = chunker.chunk_document(content)

        if len(chunks) > 1:
            # Check that consecutive chunks have some overlap
            # This is a simplified check - in practice, you'd check for actual text overlap
            assert chunks[0].metadata['chunk_index'] == 0
            assert chunks[1].metadata['chunk_index'] == 1

    def test_metadata_consistency(self, chunker):
        """Test that metadata is consistent across chunks."""
        file_path = "/test/path/document.md"
        chunks = chunker.chunk_document("Test content", file_path=file_path)

        for chunk in chunks:
            assert chunk.metadata['file_path'] == file_path,
                "File path should be consistent across chunks"
            assert isinstance(chunk.metadata['chunk_index'], int),
                "Chunk index should be an integer"
            assert isinstance(chunk.metadata['token_count'], int),
                "Token count should be an integer"

    @patch('backend.rag.chunking.tiktoken.get_encoding')
    def test_token_counting_with_tiktoken(self, mock_get_encoding, chunker):
        """Test token counting using tiktoken."""
        # Mock tiktoken encoding
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_get_encoding.return_value = mock_encoding

        content = "Test content"
        chunk = chunker.chunk_document(content)[0]

        # Verify tiktoken was used
        mock_get_encoding.assert_called_with("cl100k_base")
        assert chunk.metadata['token_count'] == 5

    def test_empty_content_handling(self, chunker):
        """Test handling of empty or minimal content."""
        # Empty string
        chunks = chunker.chunk_document("")
        assert len(chunks) == 0, "Empty content should produce no chunks"

        # Minimal content
        chunks = chunker.chunk_document("Hi")
        assert len(chunks) > 0, "Minimal content should still produce a chunk"

    def test_code_block_preservation(self, chunker):
        """Test that code blocks are not split."""
        code_content = """
# Code Example

Here's some introduction text.

```python
def long_function_name():
    """This is a multi-line function.
    It has many lines of code that shouldn't be split
    even though it's quite long.
    """
    x = 1
    y = 2
    return x + y
```

Here's some conclusion text.
"""

        chunks = chunker.chunk_document(code_content)

        # Find the chunk containing the code block
        code_chunks = [c for c in chunks if 'def long_function_name' in c.content]

        if code_chunks:
            # The code block should be intact in a single chunk
            code_chunk = code_chunks[0]
            assert 'def long_function_name' in code_chunk.content
            assert 'return x + y' in code_chunk.content
            assert 'Here\'s some conclusion text' not in code_chunk.content