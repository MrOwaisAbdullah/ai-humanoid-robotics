"""
HTML Parser for Translation Formatting Preservation.

This module parses HTML content to extract structure, identify
different content types, and prepare for translation while preserving
formatting.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from bs4 import BeautifulSoup, Tag, NavigableString
import markdown

from src.utils.translation_logger import get_translation_logger

logger = get_translation_logger(__name__)


class ContentType(Enum):
    """Content types for translation handling."""
    TEXT = "text"
    CODE = "code"
    HEADING = "heading"
    LIST = "list"
    LINK = "link"
    IMAGE = "image"
    TABLE = "table"
    QUOTE = "quote"
    EMPHASIS = "emphasis"
    STRONG = "strong"
    INLINE_CODE = "inline_code"
    MATH = "math"
    METADATA = "metadata"


@dataclass
class ContentElement:
    """Represents a parsed content element."""
    element_type: ContentType
    content: str
    attributes: Dict[str, Any]
    children: List['ContentElement']
    parent: Optional['ContentElement'] = None
    should_translate: bool = True
    preserve_formatting: bool = True
    position: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.element_type.value,
            "content": self.content,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children],
            "should_translate": self.should_translate,
            "preserve_formatting": self.preserve_formatting,
            "position": self.position
        }


class HTMLParser:
    """
    HTML parser for translation with formatting preservation.

    Features:
    - Recursive HTML parsing
    - Content type identification
    - Code block detection and preservation
    - Formatting marker injection
    - Structure reconstruction support
    """

    # Code block patterns
    CODE_BLOCK_PATTERNS = [
        re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL),  # Markdown code blocks
        re.compile(r'<pre><code[^>]*>(.*?)</code></pre>', re.DOTALL | re.IGNORECASE),  # HTML pre/code blocks
        re.compile(r'<code[^>]*>(.*?)</code>', re.DOTALL | re.IGNORECASE),  # Inline code
    ]

    # Special tags that should not be translated
    NON_TRANSLATABLE_TAGS = {
        'script', 'style', 'noscript', 'iframe', 'object', 'embed',
        'svg', 'math', 'canvas', 'video', 'audio'
    }

    # Tags that preserve inner structure
    STRUCTURE_PRESERVING_TAGS = {
        'pre', 'code', 'kbd', 'samp', 'var'
    }

    # Formatting tags
    FORMATTING_TAGS = {
        'em', 'i', 'strong', 'b', 'mark', 'small', 'del', 'ins',
        'sub', 'sup', 'u', 'tt'
    }

    def __init__(self):
        """Initialize HTML parser."""
        self.position_counter = 0
        self.translation_markers = {
            'start': '{{TRANSLATE_START}}',
            'end': '{{TRANSLATE_END}}',
            'skip': '{{SKIP_TRANSLATION}}'
        }

    def parse_html(
        self,
        html_content: str,
        source_format: str = "html"
    ) -> List[ContentElement]:
        """
        Parse HTML content into structured elements.

        Args:
            html_content: HTML content to parse
            source_format: Format type (html, markdown, etc.)

        Returns:
            List of parsed content elements
        """
        logger.info(
            "Parsing HTML content",
            content_length=len(html_content),
            source_format=source_format
        )

        # Convert markdown to HTML if needed
        if source_format == "markdown":
            html_content = markdown.markdown(
                html_content,
                extensions=['codehilite', 'tables', 'toc']
            )

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract and parse elements
        elements = []
        self.position_counter = 0

        for child in soup.body.children if soup.body else soup.children:
            element = self._parse_node(child)
            if element:
                elements.append(element)

        logger.info(
            "HTML parsing complete",
            elements_count=len(elements),
            translate_elements=len([e for e in self._flatten_elements(elements) if e.should_translate])
        )

        return elements

    def _parse_node(self, node) -> Optional[ContentElement]:
        """
        Parse a BeautifulSoup node into a content element.

        Args:
            node: BeautifulSoup node

        Returns:
            Parsed content element or None
        """
        if isinstance(node, NavigableString):
            # Handle text content
            text = str(node).strip()
            if text:
                return ContentElement(
                    element_type=ContentType.TEXT,
                    content=text,
                    attributes={},
                    children=[],
                    should_translate=True,
                    preserve_formatting=False,
                    position=self.position_counter
                )
            return None

        elif isinstance(node, Tag):
            tag_name = node.name.lower()
            attributes = dict(node.attrs)

            # Determine content type
            element_type = self._determine_content_type(node, tag_name)

            # Check if should translate
            should_translate = self._should_translate_content(node, tag_name)

            # Parse children
            children = []
            for child in node.children:
                child_element = self._parse_node(child)
                if child_element:
                    child_element.parent = node  # type: ignore
                    children.append(child_element)

            # Create element
            element = ContentElement(
                element_type=element_type,
                content=node.get_text(strip=True) if should_translate else "",
                attributes=attributes,
                children=children,
                should_translate=should_translate,
                preserve_formatting=self._should_preserve_formatting(tag_name),
                position=self.position_counter
            )

            self.position_counter += 1
            return element

        return None

    def _determine_content_type(self, node: Tag, tag_name: str) -> ContentType:
        """Determine the content type of a node."""
        # Code blocks
        if tag_name in ['pre', 'code'] or self._has_code_class(node):
            return ContentType.CODE

        # Headings
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return ContentType.HEADING

        # Lists
        elif tag_name in ['ul', 'ol', 'li', 'dl', 'dt', 'dd']:
            return ContentType.LIST

        # Links
        elif tag_name == 'a':
            return ContentType.LINK

        # Images
        elif tag_name == 'img':
            return ContentType.IMAGE

        # Tables
        elif tag_name in ['table', 'thead', 'tbody', 'tr', 'td', 'th']:
            return ContentType.TABLE

        # Quotes
        elif tag_name in ['blockquote', 'q']:
            return ContentType.QUOTE

        # Inline formatting
        elif tag_name in self.FORMATTING_TAGS:
            if tag_name in ['em', 'i']:
                return ContentType.EMPHASIS
            elif tag_name in ['strong', 'b']:
                return ContentType.STRONG
            elif tag_name == 'code' and not self._is_block_code(node):
                return ContentType.INLINE_CODE

        # Math
        elif tag_name in ['math', 'mrow', 'mfrac', 'msqrt', 'mroot']:
            return ContentType.MATH

        # Metadata
        elif tag_name in ['meta', 'title', 'head', 'style', 'script']:
            return ContentType.METADATA

        # Default to text
        else:
            return ContentType.TEXT

    def _should_translate_content(self, node: Tag, tag_name: str) -> bool:
        """Determine if content should be translated."""
        # Don't translate non-translatable tags
        if tag_name in self.NON_TRANSLATABLE_TAGS:
            return False

        # Don't translate code blocks
        if tag_name == 'code' and (node.parent and node.parent.name == 'pre'):
            return False

        if tag_name == 'pre':
            return False

        # Don't translate if class indicates code
        if self._has_code_class(node):
            return False

        # Don't translate image alt text that's purely technical
        if tag_name == 'img' and self._is_technical_alt_text(node.get('alt', '')):
            return False

        return True

    def _should_preserve_formatting(self, tag_name: str) -> bool:
        """Check if formatting should be preserved."""
        return tag_name in (self.STRUCTURE_PRESERVING_TAGS | self.FORMATTING_TAGS)

    def _has_code_class(self, node: Tag) -> bool:
        """Check if node has code-related classes."""
        classes = node.get('class', [])
        if isinstance(classes, str):
            classes = [classes]

        code_indicators = [
            'language-', 'highlight', 'code', ' hljs', 'chroma',
            'source-code', 'pre', 'verbatim', 'literal'
        ]

        return any(
            any(indicator in cls for indicator in code_indicators)
            for cls in classes
        )

    def _is_block_code(self, node: Tag) -> bool:
        """Check if code element is a block code."""
        return (
            node.name == 'code' and
            node.parent and
            node.parent.name == 'pre'
        )

    def _is_technical_alt_text(self, alt_text: str) -> bool:
        """Check if alt text is purely technical."""
        technical_indicators = [
            'diagram', 'chart', 'graph', 'formula', 'equation',
            'algorithm', 'flowchart', 'schema', 'architecture'
        ]

        return any(indicator in alt_text.lower() for indicator in technical_indicators)

    def _flatten_elements(self, elements: List[ContentElement]) -> List[ContentElement]:
        """Flatten nested elements into a single list."""
        flattened = []
        for element in elements:
            flattened.append(element)
            flattened.extend(self._flatten_elements(element.children))
        return flattened

    def extract_translatable_text(self, elements: List[ContentElement]) -> str:
        """
        Extract only translatable text content from elements.

        Args:
            elements: Parsed content elements

        Returns:
            Concatenated translatable text
        """
        translatable_parts = []

        for element in self._flatten_elements(elements):
            if element.should_translate and element.element_type != ContentType.CODE:
                if element.element_type == ContentType.TEXT:
                    translatable_parts.append(element.content)
                else:
                    # Add spacing for block elements
                    if element.element_type == ContentType.HEADING:
                        translatable_parts.append('\n\n')

        return ''.join(translatable_parts).strip()

    def inject_translation_markers(
        self,
        elements: List[ContentElement],
        translated_text: str
    ) -> List[ContentElement]:
        """
        Inject translation markers into elements for reconstruction.

        Args:
            elements: Original parsed elements
            translated_text: Translated text content

        Returns:
            Elements with markers injected
        """
        # This is a simplified version - in practice, you'd want
        # more sophisticated mapping of translated text to elements
        translatable_elements = [
            e for e in self._flatten_elements(elements)
            if e.should_translate and e.element_type != ContentType.CODE
        ]

        if translatable_elements:
            # Inject markers around the whole content
            first = translatable_elements[0]
            last = translatable_elements[-1]

            # Add start marker
            first.attributes['_translation_start'] = True

            # Add end marker
            last.attributes['_translation_end'] = True

        return elements

    def extract_code_blocks(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks from HTML content.

        Args:
            html_content: HTML content to parse

        Returns:
            List of code block information
        """
        code_blocks = []
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all code blocks
        for code_element in soup.find_all(['pre', 'code']):
            if code_element.name == 'pre' or (
                code_element.name == 'code' and
                code_element.parent and
                code_element.parent.name == 'pre'
            ):
                language = None
                classes = code_element.get('class', [])

                # Extract language from classes
                if classes:
                    for cls in classes:
                        if isinstance(cls, str):
                            if cls.startswith('language-'):
                                language = cls[9:]
                            elif cls in ['python', 'javascript', 'java', 'cpp', 'html', 'css', 'sql']:
                                language = cls

                code_content = code_element.get_text()
                code_html = str(code_element)

                code_blocks.append({
                    'language': language or 'text',
                    'content': code_content,
                    'html': code_html,
                    'position': html_content.find(code_html)
                })

        logger.info(
            "Code blocks extracted",
            total_blocks=len(code_blocks),
            languages=[cb['language'] for cb in code_blocks]
        )

        return code_blocks

    def preserve_code_blocks(
        self,
        html_content: str,
        translated_content: str
    ) -> str:
        """
        Preserve code blocks in translated content.

        Args:
            html_content: Original HTML with code blocks
            translated_content: Translated HTML (code blocks might be altered)

        Returns:
            HTML with original code blocks preserved
        """
        # Extract code blocks from original
        original_blocks = self.extract_code_blocks(html_content)

        # Replace code blocks in translated content with originals
        result = translated_content
        for block in original_blocks:
            result = result.replace(block['html'], block['html'], 1)

        logger.info(
            "Code blocks preserved",
            blocks_count=len(original_blocks)
        )

        return result

    def validate_structure(
        self,
        original_elements: List[ContentElement],
        translated_elements: List[ContentElement]
    ) -> List[str]:
        """
        Validate that structure is preserved between original and translated.

        Args:
            original_elements: Original parsed elements
            translated_elements: Translated parsed elements

        Returns:
            List of validation errors
        """
        errors = []

        # Compare structure counts
        original_types = self._count_element_types(original_elements)
        translated_types = self._count_element_types(translated_elements)

        for element_type, count in original_types.items():
            if element_type != ContentType.TEXT:  # Text count may differ
                translated_count = translated_types.get(element_type, 0)
                if count != translated_count:
                    errors.append(
                        f"Element count mismatch for {element_type.value}: "
                        f"original={count}, translated={translated_count}"
                    )

        # Check that code blocks are preserved
        original_code_blocks = len([
            e for e in self._flatten_elements(original_elements)
            if e.element_type == ContentType.CODE
        ])
        translated_code_blocks = len([
            e for e in self._flatten_elements(translated_elements)
            if e.element_type == ContentType.CODE
        ])

        if original_code_blocks != translated_code_blocks:
            errors.append(
                f"Code block count mismatch: "
                f"original={original_code_blocks}, translated={translated_code_blocks}"
            )

        logger.info(
            "Structure validation complete",
            errors_count=len(errors),
            element_types_matched=len(set(original_types.keys()) & set(translated_types.keys()))
        )

        return errors

    def _count_element_types(self, elements: List[ContentElement]) -> Dict[ContentType, int]:
        """Count occurrences of each element type."""
        counts = {}
        for element in self._flatten_elements(elements):
            counts[element.element_type] = counts.get(element.element_type, 0) + 1
        return counts

    def generate_structure_report(
        self,
        elements: List[ContentElement]
    ) -> Dict[str, Any]:
        """
        Generate a report of the content structure.

        Args:
            elements: Parsed content elements

        Returns:
            Structure report
        """
        flattened = self._flatten_elements(elements)
        type_counts = self._count_element_types(elements)

        report = {
            "total_elements": len(flattened),
            "element_types": {
                type_name.value: count
                for type_name, count in type_counts.items()
            },
            "translatable_elements": len([e for e in flattened if e.should_translate]),
            "code_blocks": type_counts.get(ContentType.CODE, 0),
            "headings": type_counts.get(ContentType.HEADING, 0),
            "lists": type_counts.get(ContentType.LIST, 0),
            "links": type_counts.get(ContentType.LINK, 0),
            "images": type_counts.get(ContentType.IMAGE, 0),
            "tables": type_counts.get(ContentType.TABLE, 0)
        }

        return report