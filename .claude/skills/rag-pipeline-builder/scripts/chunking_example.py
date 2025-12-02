#!/usr/bin/env python3
"""
Intelligent Document Chunking for RAG Systems

This script demonstrates advanced chunking strategies that preserve
document structure and optimize for retrieval performance.
"""

import re
import tiktoken
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter


@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata."""
    text: str
    metadata: Dict[str, Any]
    chunk_index: int
    token_count: int


class IntelligentChunker:
    """
    Markdown-aware chunking that preserves structure and optimizes for RAG.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize the chunker with specified parameters.

        Args:
            chunk_size: Target size in tokens
            overlap: Overlap between chunks in tokens
        """
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = chunk_size
        self.overlap = overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=self._count_tokens,
            separators=[
                "\n\n\n",  # Major sections
                "\n\n",    # Paragraphs
                "\n",      # Lines
                ". ",      # Sentences
                " ",       # Words
                "",        # Characters
            ],
            keep_separator=True,
        )

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using the encoding."""
        return len(self.encoding.encode(text))

    def _protect_code_blocks(self, text: str) -> str:
        """Replace code blocks with placeholders to prevent splitting."""
        code_blocks = []

        def replace_block(match):
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks.append(match.group(0))
            return placeholder

        # Replace both inline code and code blocks
        text = re.sub(r'```[\s\S]*?```', replace_block, text)
        text = re.sub(r'`[^`]+`', replace_block, text)

        return text

    def _restore_code_blocks(self, text: str, code_blocks: List[str]) -> str:
        """Restore code blocks from placeholders."""
        for i, block in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", block)
        return text

    def _extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extract metadata from file path and content."""
        import os

        # Basic file metadata
        metadata = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_extension": os.path.splitext(file_path)[1],
        }

        # Try to extract title from first line
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                metadata["title"] = line[2:].strip()
                break
            elif line and not line.startswith('#'):
                metadata["title"] = line[:50] + "..." if len(line) > 50 else line
                break

        # Extract sections (markdown headers)
        sections = []
        for line in lines:
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.strip('#').strip()
                sections.append({"level": level, "title": title})

        metadata["sections"] = sections
        return metadata

    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Chunk a document while preserving structure.

        Args:
            text: Document content
            metadata: Base metadata for the document

        Returns:
            List of DocumentChunk objects
        """
        # Protect code blocks from splitting
        code_blocks = []
        text = self._protect_code_blocks(text)

        # Split into chunks
        chunks = self.splitter.split_text(text)

        # Restore code blocks
        text = self._restore_code_blocks(text, code_blocks)

        # Create DocumentChunk objects
        document_chunks = []
        for i, chunk_text in enumerate(chunks):
            # Restore code blocks in this chunk
            restored_chunk = self._restore_code_blocks(chunk_text, code_blocks)

            chunk = DocumentChunk(
                text=restored_chunk,
                metadata={**metadata, "chunk_index": i},
                chunk_index=i,
                token_count=self._count_tokens(restored_chunk)
            )
            document_chunks.append(chunk)

        return document_chunks

    def chunk_multiple_documents(self, file_paths: List[str]) -> List[DocumentChunk]:
        """
        Chunk multiple documents and return all chunks.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of all DocumentChunk objects
        """
        all_chunks = []

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract metadata
                metadata = self._extract_metadata(file_path, content)

                # Chunk the document
                chunks = self.chunk_document(content, metadata)
                all_chunks.extend(chunks)

                print(f"✅ Processed {file_path}: {len(chunks)} chunks")

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

        return all_chunks

    def analyze_chunks(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Analyze chunk statistics."""
        if not chunks:
            return {"total_chunks": 0}

        token_counts = [chunk.token_count for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_chunk": sum(token_counts) / len(token_counts),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "chunks_within_target": sum(1 for t in token_counts if self.chunk_size * 0.8 <= t <= self.chunk_size * 1.2)
        }


# Example usage
if __name__ == "__main__":
    # Example document
    sample_text = """
# Introduction to RAG Systems

Retrieval-Augmented Generation (RAG) is a powerful approach that combines
retrieval-based methods with generation-based models. This allows for more
accurate and contextually relevant responses.

## Key Components

### Document Processing
Documents need to be processed and chunked effectively:

```python
def chunk_document(text, chunk_size=1000):
    # Implementation here
    pass
```

### Vector Storage
The chunks are stored as vectors in a vector database like Qdrant.

## Best Practices

1. Use appropriate chunk sizes
2. Maintain overlap between chunks
3. Preserve document structure

## Conclusion

RAG systems provide a way to ground AI responses in specific knowledge
bases, reducing hallucinations and improving accuracy.
"""

    # Initialize chunker
    chunker = IntelligentChunker(chunk_size=800, overlap=150)

    # Extract metadata
    metadata = chunker._extract_metadata("sample.md", sample_text)

    # Chunk the document
    chunks = chunker.chunk_document(sample_text, metadata)

    # Analyze results
    analysis = chunker.analyze_chunks(chunks)

    print("📊 Chunk Analysis:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")

    print("\n📄 Sample Chunks:")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\nChunk {i + 1} ({chunk.token_count} tokens):")
        print(f"  {chunk.text[:100]}...")