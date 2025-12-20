"""
Pure Python text chunking for Markdown documents.

Implements semantic chunking based on Markdown headers with overlapping context.
"""

import re
import hashlib
from typing import List, Dict, Any, Tuple, Optional
import tiktoken
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


# Default template patterns to exclude
DEFAULT_TEMPLATES = [
    r'^how to use this book$',
    r'^table of contents$',
    r'^foreword$',
    r'^preface$',
    r'^about this book$',
    r'^copyright\s+\d{4}$',
    r'^acknowledgments$',
    r'^legal notice',
    r'^disclaimer',
    r'^about the author$',
    r'^introduction to this edition$'
]

# Production URL configuration
PRODUCTION_URL = "https://mrowaisabdullah.github.io"
BASE_PATH = "/ai-humanoid-robotics/"

@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    token_count: int


class MarkdownChunker:
    """Chunks Markdown documents based on semantic structure."""

    def __init__(
        self,
        target_chunk_size: int = 600,  # Updated to 600 tokens
        overlap_size: int = 100,  # Updated to 100 tokens overlap
        encoding_name: str = "cl100k_base",  # OpenAI's encoding
        template_patterns: Optional[List[str]] = None,
        min_chunk_size: int = 50  # Minimum chunk size to prevent tiny chunks
    ):
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.template_patterns = template_patterns or DEFAULT_TEMPLATES
        self.min_chunk_size = min_chunk_size

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using OpenAI's tiktoken."""
        return len(self.encoding.encode(text))

    def is_template_header(self, header: str) -> bool:
        """Check if a header matches template patterns."""
        header_lower = header.lower().strip()

        for pattern in self.template_patterns:
            if re.match(pattern, header_lower, re.IGNORECASE):
                return True
        return False

    def generate_content_hash(self, content: str) -> str:
        """Generate SHA256 hash for content deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def generate_url_from_path(self, file_path: str) -> str:
        """Generate the correct production URL from file path."""
        # Convert file path to URL path
        relative_path = Path(file_path)

        # Remove extension and convert slashes
        url_path = str(relative_path.with_suffix(''))

        # Normalize path separators
        url_path = url_path.replace('\\', '/')

        # Remove leading directory components
        # Handle both '../docs' and 'docs' prefixes
        if url_path.startswith('../docs/'):
            url_path = url_path[8:]  # Remove '../docs/'
        elif url_path.startswith('docs/'):
            url_path = url_path[5:]  # Remove 'docs/'
        elif url_path.startswith('../'):
            # Remove all '../' components
            while url_path.startswith('../'):
                url_path = url_path[3:]
        elif url_path.startswith('book_content/'):
            url_path = url_path[12:]  # Remove 'book_content/'

        # Ensure leading slash
        if not url_path.startswith('/'):
            url_path = '/' + url_path

        # Handle index files specially
        if url_path.endswith('/index'):
            url_path = url_path[:-6]  # Remove '/index'

        # If path is just '/', make it empty
        if url_path == '/':
            url_path = ''

        # Build final URL
        return f"{PRODUCTION_URL}{BASE_PATH}docs{url_path}"

    def split_by_headers(self, content: str) -> List[Tuple[str, int, int]]:
        """Split content by Markdown headers (##, ###, etc.)."""
        # Pattern to match headers (# ## ### etc.)
        header_pattern = r'^(#{1,6})\s+(.+)$'

        sections = []
        lines = content.split('\n')
        current_section = []
        current_header = None
        current_header_level = 0
        start_line = 0

        for i, line in enumerate(lines):
            header_match = re.match(header_pattern, line)

            if header_match:
                # Save previous section
                if current_section and current_header:
                    sections.append((current_header, start_line, i))

                # Start new section
                current_header = header_match.group(2)
                current_header_level = len(header_match.group(1))
                start_line = i
                current_section = [line]
            else:
                current_section.append(line)

        # Add last section
        if current_section and current_header:
            sections.append((current_header, start_line, len(lines)))

        # If no headers found, treat entire content as one section
        if not sections:
            sections = [("Introduction", 0, len(lines))]

        return sections

    def create_chunks_from_section(
        self,
        section_content: str,
        section_header: str,
        file_path: str,
        chapter: str,
        section_start: int
    ) -> List[Chunk]:
        """Create chunks from a single section with overlap."""
        # Check if this is a template section
        is_template = self.is_template_header(section_header)

        # Skip template sections entirely
        if is_template:
            return []

        chunks = []
        sentences = self._split_into_sentences(section_content)

        current_chunk_sentences = []
        current_tokens = 0

        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)

            # If adding this sentence exceeds target size and we have content, create chunk
            if current_tokens + sentence_tokens > self.target_chunk_size and current_chunk_sentences:
                chunk_content = ' '.join(current_chunk_sentences)

                # Enforce minimum chunk size
                if current_tokens >= self.min_chunk_size:
                    content_hash = self.generate_content_hash(chunk_content)

                    # Create metadata with new fields
                    chunk = Chunk(
                        content=chunk_content,
                        metadata={
                            "file_path": file_path,
                            "chapter": chapter,
                            "section_header": section_header,
                            "section_start_line": section_start,
                            "chunk_type": "section",
                            "sentence_count": len(current_chunk_sentences),
                            "content_hash": content_hash,
                            "is_template": is_template,
                            "url": self.generate_url_from_path(file_path),
                            "created_at": datetime.utcnow().isoformat()
                        },
                        chunk_id=f"{Path(file_path).stem}_{section_header.replace(' ', '_')}_{len(chunks)}",
                        token_count=current_tokens
                    )
                    chunks.append(chunk)

                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk_sentences,
                    sentences[i:]
                )
                current_chunk_sentences = overlap_sentences
                current_tokens = sum(self.count_tokens(s) for s in overlap_sentences)

            # Add current sentence
            current_chunk_sentences.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk if there's remaining content and meets minimum size
        if current_chunk_sentences and len(current_chunk_sentences) > 0:
            chunk_content = ' '.join(current_chunk_sentences)
            final_tokens = sum(self.count_tokens(s) for s in current_chunk_sentences)

            if final_tokens >= self.min_chunk_size:
                content_hash = self.generate_content_hash(chunk_content)

                chunk = Chunk(
                    content=chunk_content,
                    metadata={
                        "file_path": file_path,
                        "chapter": chapter,
                        "section_header": section_header,
                        "section_start_line": section_start,
                        "chunk_type": "section",
                        "sentence_count": len(current_chunk_sentences),
                        "content_hash": content_hash,
                        "is_template": is_template,
                        "url": self.generate_url_from_path(file_path),
                        "created_at": datetime.utcnow().isoformat()
                    },
                    chunk_id=f"{Path(file_path).stem}_{section_header.replace(' ', '_')}_{len(chunks)}",
                    token_count=final_tokens
                )
                chunks.append(chunk)

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure."""
        # Simple sentence splitting - can be enhanced
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_sentences(self, previous_sentences: List[str], remaining_sentences: List[str]) -> List[str]:
        """Get overlapping sentences for context preservation."""
        if not previous_sentences:
            return []

        # Calculate how many sentences from previous chunk to keep for overlap
        overlap_target = self.overlap_size // 10  # Rough estimate of tokens per sentence

        if len(previous_sentences) <= overlap_target:
            return previous_sentences

        # Take last N sentences from previous chunk
        return previous_sentences[-overlap_target:]

    def chunk_document(self, file_path: str) -> List[Chunk]:
        """Chunk a single Markdown document."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract chapter from path with better logic
        path_parts = Path(file_path).parts
        chapter = "Unknown"

        # Try to find chapter in various ways
        for part in path_parts:
            # Look for "chapter" pattern (case insensitive)
            if part.lower().startswith('chapter'):
                chapter = part
                break
            # Look for numeric patterns like "01", "1", "02" etc.
            elif part.isdigit() and len(part) <= 2:
                # Find the context for this number
                part_index = path_parts.index(part)
                if part_index > 0:
                    prev_part = path_parts[part_index - 1].lower()
                    if 'chapter' in prev_part:
                        chapter = f"Chapter {int(part)}"
                    else:
                        # Just use the number as chapter
                        chapter = f"Chapter {int(part)}"
                else:
                    chapter = f"Chapter {int(part)}"
                break
            # Look for patterns like "ch1", "ch01"
            elif part.lower().startswith('ch') and part[2:].isdigit():
                chapter_num = int(part[2:])
                chapter = f"Chapter {chapter_num}"
                break

        # If still unknown, try to extract from filename
        if chapter == "Unknown":
            filename = Path(file_path).stem
            # Try to parse chapter from filename
            chapter_match = re.search(r'chapter\s*(\d+)', filename, re.IGNORECASE)
            if chapter_match:
                chapter = f"Chapter {int(chapter_match.group(1))}"
            else:
                # Use filename as last resort
                chapter = filename.replace('_', ' ').replace('-', ' ').title()

        # Split by headers
        sections = self.split_by_headers(content)
        all_chunks = []

        for header, start_line, end_line in sections:
            # Extract section content
            lines = content.split('\n')
            section_lines = lines[start_line:end_line]
            section_content = '\n'.join(section_lines)

            # Create chunks from this section
            section_chunks = self.create_chunks_from_section(
                section_content,
                header,
                file_path,
                chapter,
                start_line
            )

            all_chunks.extend(section_chunks)

        return all_chunks

    def add_code_blocks_as_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Extract code blocks and add them as separate chunks."""
        additional_chunks = []

        for chunk in chunks:
            # Find code blocks in the content
            code_pattern = r'```(\w+)?\n(.*?)\n```'
            matches = re.finditer(code_pattern, chunk.content, re.DOTALL)

            for match in matches:
                code_content = match.group(2)
                code_language = match.group(1) or "text"

                code_chunk = Chunk(
                    content=code_content,
                    metadata={
                        **chunk.metadata,
                        "chunk_type": "code",
                        "code_language": code_language,
                        "parent_chunk_id": chunk.chunk_id
                    },
                    chunk_id=f"{chunk.chunk_id}_code_{len(additional_chunks)}",
                    token_count=self.count_tokens(code_content)
                )
                additional_chunks.append(code_chunk)

        return chunks + additional_chunks