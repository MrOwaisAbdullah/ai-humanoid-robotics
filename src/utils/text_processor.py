"""
Text processing utilities for content chunking and preparation.

Provides functions for chunking content, detecting code blocks, handling mixed languages,
and parsing markdown content.
"""

import re
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

from src.utils.logging import get_logger
from src.utils.errors import ValidationError

logger = get_logger(__name__)


class ContentType(Enum):
    """Supported content types."""
    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    CODE = "code"


@dataclass
class ContentChunk:
    """Represents a chunk of content with metadata."""
    index: int
    content: str
    start_position: int
    end_position: int
    is_code_block: bool
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessedContent:
    """Represents processed content with chunks."""
    original_text: str
    chunks: List[ContentChunk]
    content_hash: str
    total_characters: int
    estimated_reading_time: float  # in minutes
    language_detected: Optional[str] = None


class TextProcessor:
    """
    Text processor for content chunking and preparation.

    Features:
    - Intelligent content chunking (max 50,000 chars)
    - Code block detection and preservation
    - Mixed language handling
    - Markdown parsing
    - Metadata extraction
    """

    # Maximum chunk size (characters)
    MAX_CHUNK_SIZE = 50000

    # Preferred chunk overlap for context
    CHUNK_OVERLAP = 500

    # Code block patterns
    CODE_BLOCK_PATTERNS = [
        r'```[\s\S]*?```',  # Triple backticks
        r'`[^`]+`',         # Inline code
        r'<code>[\s\S]*?</code>',  # HTML code tags
        r'<pre>[\s\S]*?</pre>',    # HTML pre tags
    ]

    # Markdown patterns
    MARKDOWN_PATTERNS = {
        'headers': r'^#{1,6}\s+(.*)$',
        'links': r'\[([^\]]+)\]\(([^)]+)\)',
        'images': r'!\[([^\]]*)\]\(([^)]+)\)',
        'bold': r'\*\*([^\*]+)\*\*|__([^_]+)__',
        'italic': r'\*([^\*]+)\*|_([^_]+)_',
        'lists': r'^\s*[-*+]\s+|^\s*\d+\.\s+',
        'blockquotes': r'^>\s+(.*)$',
    }

    # Language detection patterns (simple heuristic)
    LANGUAGE_PATTERNS = {
        'urdu': r'[\u0600-\u06FF]',
        'arabic': r'[\u0600-\u06FF]',
        'persian': r'[\u0600-\u06FF\u0750-\u077F]',
        'chinese': r'[\u4e00-\u9fff]',
        'japanese': r'[\u3040-\u309f\u30a0-\u30ff]',
        'korean': r'[\uac00-\ud7af]',
        'hindi': r'[\u0900-\u097f]',
        'devanagari': r'[\u0900-\u097f]',
    }

    def __init__(
        self,
        max_chunk_size: int = MAX_CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        preserve_code_blocks: bool = True
    ):
        """
        Initialize text processor.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
            preserve_code_blocks: Whether to preserve code blocks as separate chunks
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_code_blocks = preserve_code_blocks

        # Compile regex patterns
        self.code_block_regex = re.compile('|'.join(self.CODE_BLOCK_PATTERNS), re.MULTILINE)
        self.markdown_regex = {k: re.compile(v, re.MULTILINE) for k, v in self.MARKDOWN_PATTERNS.items()}
        self.language_regex = {k: re.compile(v) for k, v in self.LANGUAGE_PATTERNS.items()}

        logger.info(
            "Text processor initialized",
            max_chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
            preserve_code_blocks=preserve_code_blocks
        )

    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the primary language of the text.

        Args:
            text: Text to analyze

        Returns:
            Detected language code or None
        """
        language_scores = {}

        for lang, pattern in self.language_regex.items():
            matches = pattern.findall(text)
            if matches:
                language_scores[lang] = len(matches) / len(text)

        if language_scores:
            detected_lang = max(language_scores, key=language_scores.get)
            if language_scores[detected_lang] > 0.1:  # Minimum threshold
                return detected_lang

        return None

    def extract_code_blocks(self, text: str) -> Tuple[str, List[ContentChunk]]:
        """
        Extract code blocks from text.

        Args:
            text: Text to process

        Returns:
            Tuple of (text_without_code, code_chunks)
        """
        code_blocks = []
        modified_text = text
        offset = 0

        for match in self.code_block_regex.finditer(text):
            start = match.start() + offset
            end = match.end() + offset

            # Determine the language if it's a markdown code block
            language = None
            if match.group().startswith('```'):
                lines = match.group().split('\n')
                if len(lines) > 1:
                    language = lines[0].replace('```', '').strip()

            # Create code chunk
            chunk = ContentChunk(
                index=len(code_blocks),
                content=match.group(),
                start_position=start,
                end_position=end,
                is_code_block=True,
                language=language
            )
            code_blocks.append(chunk)

            # Replace with placeholder
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            modified_text = modified_text[:match.start() + offset] + placeholder + modified_text[match.end() + offset:]
            offset += len(placeholder) - len(match.group())

        return modified_text, code_blocks

    def restore_code_blocks(self, text: str, code_blocks: List[ContentChunk]) -> str:
        """
        Restore code blocks in processed text.

        Args:
            text: Text with code placeholders
            code_blocks: List of code chunks

        Returns:
            Text with code blocks restored
        """
        for chunk in code_blocks:
            placeholder = f"__CODE_BLOCK_{chunk.index + 1}__"
            text = text.replace(placeholder, chunk.content)

        return text

    def split_into_chunks(self, text: str) -> List[ContentChunk]:
        """
        Split text into chunks respecting sentence boundaries.

        Args:
            text: Text to chunk

        Returns:
            List of content chunks
        """
        if len(text) <= self.max_chunk_size:
            return [ContentChunk(
                index=0,
                content=text,
                start_position=0,
                end_position=len(text),
                is_code_block=False
            )]

        chunks = []
        start = 0

        while start < len(text):
            # Determine end position
            end = start + self.max_chunk_size

            if end >= len(text):
                # Last chunk
                chunks.append(ContentChunk(
                    index=len(chunks),
                    content=text[start:],
                    start_position=start,
                    end_position=len(text),
                    is_code_block=False
                ))
                break

            # Try to split at a sentence boundary
            # Look for period, question mark, or exclamation mark followed by space or newline
            split_patterns = [r'[.!?]\s+(?=[A-Z\u0600-\u06FF])', r'\n(?=\w)', r'[.!?]\s*$']

            best_split = end
            for pattern in split_patterns:
                regex = re.compile(pattern)
                matches = list(regex.finditer(text[start:end]))
                if matches:
                    best_split = start + matches[-1].end()
                    break

            # If no good split found, try to split at word boundary
            if best_split == end:
                word_boundary = text.rfind(' ', start, end)
                if word_boundary > start:
                    best_split = word_boundary

            chunk_content = text[start:best_split].strip()

            chunks.append(ContentChunk(
                index=len(chunks),
                content=chunk_content,
                start_position=start,
                end_position=best_split,
                is_code_block=False
            ))

            # Start next chunk with overlap
            start = best_split - self.chunk_overlap if best_split > self.chunk_overlap else best_split

        return chunks

    def process_markdown(self, text: str) -> Dict[str, Any]:
        """
        Extract markdown metadata.

        Args:
            text: Markdown text

        Returns:
            Dictionary with metadata
        """
        metadata = {
            'headers': [],
            'links': [],
            'images': [],
            'code_language_counts': {},
            'has_list': False,
            'has_blockquote': False,
        }

        # Extract headers
        for match in self.markdown_regex['headers'].finditer(text):
            level = len(match.group().split(' ')[0])
            title = match.group().strip('#').strip()
            metadata['headers'].append({
                'level': level,
                'title': title,
                'position': match.start()
            })

        # Extract links
        for match in self.markdown_regex['links'].finditer(text):
            metadata['links'].append({
                'text': match.group(1),
                'url': match.group(2),
                'position': match.start()
            })

        # Extract images
        for match in self.markdown_regex['images'].finditer(text):
            metadata['images'].append({
                'alt': match.group(1),
                'url': match.group(2),
                'position': match.start()
            })

        # Check for lists and blockquotes
        if self.markdown_regex['lists'].search(text):
            metadata['has_list'] = True

        if self.markdown_regex['blockquotes'].search(text):
            metadata['has_blockquote'] = True

        # Count code languages
        code_block_pattern = re.compile(r'```(\w+)?\n[\s\S]*?```')
        for match in code_block_pattern.finditer(text):
            lang = match.group(1) or 'plain'
            metadata['code_language_counts'][lang] = metadata['code_language_counts'].get(lang, 0) + 1

        return metadata

    def estimate_reading_time(self, text: str, words_per_minute: int = 200) -> float:
        """
        Estimate reading time in minutes.

        Args:
            text: Text to analyze
            words_per_minute: Average reading speed

        Returns:
            Estimated reading time in minutes
        """
        # Simple word count (splits by whitespace)
        word_count = len(text.split())

        # For content with significant code blocks, adjust the reading time
        code_ratio = len(self.code_block_regex.findall(text)) / len(text) if text else 0
        if code_ratio > 0.3:
            # Reduce reading speed for code-heavy content
            words_per_minute = words_per_minute * 0.7

        return word_count / words_per_minute

    def process(
        self,
        text: str,
        content_type: ContentType = ContentType.MARKDOWN,
        user_id: Optional[str] = None
    ) -> ProcessedContent:
        """
        Process text into chunks with metadata.

        Args:
            text: Text to process
            content_type: Type of content
            user_id: Optional user ID for personalization

        Returns:
            ProcessedContent with chunks and metadata
        """
        if not text:
            raise ValidationError("Text cannot be empty")

        # Generate content hash
        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

        # Detect language
        language_detected = self.detect_language(text)

        # Extract code blocks if preserving them
        text_without_code = text
        code_chunks = []

        if self.preserve_code_blocks:
            text_without_code, code_chunks = self.extract_code_blocks(text)

        # Split into chunks
        text_chunks = self.split_into_chunks(text_without_code)

        # Combine with code chunks
        all_chunks = []
        code_index = 0

        for chunk in text_chunks:
            # Check if this chunk contains code placeholders
            while f"__CODE_BLOCK_{code_index + 1}__" in chunk.content:
                # Split chunk around code placeholder
                placeholder = f"__CODE_BLOCK_{code_index + 1}__"
                parts = chunk.content.split(placeholder)

                if parts[0]:  # Text before code
                    all_chunks.append(ContentChunk(
                        index=len(all_chunks),
                        content=parts[0],
                        start_position=chunk.start_position,
                        end_position=chunk.start_position + len(parts[0]),
                        is_code_block=False
                    ))

                # Add code block
                if code_index < len(code_chunks):
                    code_chunk = code_chunks[code_index]
                    all_chunks.append(ContentChunk(
                        index=len(all_chunks),
                        content=code_chunk.content,
                        start_position=code_chunk.start_position,
                        end_position=code_chunk.end_position,
                        is_code_block=True,
                        language=code_chunk.language
                    ))
                    code_index += 1

                # Continue with remaining text
                if len(parts) > 1:
                    remaining_content = ''.join(parts[1:])
                    chunk.content = remaining_content
                    chunk.start_position = chunk.end_position - len(remaining_content)
                else:
                    break
            else:
                if chunk.content:  # Add text chunk if it has content
                    all_chunks.append(chunk)

        # Extract metadata for markdown content
        metadata = {}
        if content_type == ContentType.MARKDOWN:
            metadata = self.process_markdown(text)

        # Calculate reading time
        reading_time = self.estimate_reading_time(text)

        logger.info(
            "Text processed successfully",
            content_hash=content_hash[:8],
            language=language_detected,
            total_chunks=len(all_chunks),
            code_chunks=len(code_chunks),
            characters=len(text)
        )

        return ProcessedContent(
            original_text=text,
            chunks=all_chunks,
            content_hash=content_hash,
            total_characters=len(text),
            estimated_reading_time=reading_time,
            language_detected=language_detected,
            metadata=metadata
        )

    def prepare_for_translation(
        self,
        content: ProcessedContent,
        skip_code_blocks: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Prepare content chunks for translation.

        Args:
            content: Processed content
            skip_code_blocks: Whether to skip code blocks in translation

        Returns:
            List of translation-ready chunks
        """
        translation_chunks = []

        for chunk in content.chunks:
            if chunk.is_code_block and skip_code_blocks:
                continue

            translation_chunks.append({
                'index': chunk.index,
                'content': chunk.content,
                'start_position': chunk.start_position,
                'end_position': chunk.end_position,
                'is_code_block': chunk.is_code_block,
                'language': chunk.language,
                'metadata': chunk.metadata
            })

        return translation_chunks

    def reconstruct_translated(
        self,
        chunks: List[Dict[str, Any]],
        original_content: ProcessedContent
    ) -> str:
        """
        Reconstruct translated content from chunks.

        Args:
            chunks: Translated chunks
            original_content: Original processed content

        Returns:
            Reconstructed translated text
        """
        # Create a map of index to translated content
        translated_map = {chunk['index']: chunk.get('translated_text', chunk['content'])
                         for chunk in chunks}

        # Build the final text
        result_parts = []

        for chunk in original_content.chunks:
            if chunk.index in translated_map:
                result_parts.append(translated_map[chunk.index])
            else:
                # For code blocks that were skipped, use original
                result_parts.append(chunk.content)

        return ''.join(result_parts)


# Global text processor instance
_text_processor: Optional[TextProcessor] = None


def get_text_processor() -> TextProcessor:
    """Get or create text processor instance."""
    global _text_processor

    if _text_processor is None:
        _text_processor = TextProcessor()

    return _text_processor