"""
Content Reconstructor for Translation System.

This module reconstructs HTML content from parsed elements,
injecting translated text while preserving original formatting
and structure.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag, NavigableString
import re
import markdown

from src.services.html_parser import ContentElement, ContentType
from src.utils.translation_logger import get_translation_logger

logger = get_translation_logger(__name__)


@dataclass
class ReconstructionConfig:
    """Configuration for content reconstruction."""
    preserve_classes: bool = True
    preserve_ids: bool = True
    preserve_data_attributes: bool = False
    preserve_style: bool = True
    add_translation_markers: bool = False
    cleanup_empty_elements: bool = True


class ContentReconstructor:
    """
    Reconstructs HTML content from parsed elements with translations.

    Features:
    - Recursive HTML reconstruction
    - Formatting preservation
    - Code block protection
    - Translation marker injection
    - Structure validation
    """

    def __init__(self, config: Optional[ReconstructionConfig] = None):
        """
        Initialize content reconstructor.

        Args:
            config: Reconstruction configuration
        """
        self.config = config or ReconstructionConfig()
        self.translation_markers = {
            'translated': 'data-translated="true"',
            'original': 'data-original="',
            'preserve': 'data-preserve="true"'
        }

    def reconstruct_html(
        self,
        elements: List[ContentElement],
        translated_map: Dict[str, str],
        base_format: str = "html"
    ) -> str:
        """
        Reconstruct HTML from parsed elements with translations.

        Args:
            elements: Parsed content elements
            translated_map: Mapping of original text to translated text
            base_format: Base format (html, markdown, etc.)

        Returns:
            Reconstructed HTML content
        """
        logger.info(
            "Reconstructing HTML content",
            elements_count=len(elements),
            translations_count=len(translated_map),
            base_format=base_format
        )

        # Create base document
        if base_format == "html":
            soup = BeautifulSoup("", "html.parser")
            body = soup.new_tag("body")
            soup.append(body)
        else:
            soup = BeautifulSoup("", "html.parser")

        # Reconstruct elements
        container = soup.body if soup.body else soup
        for element in elements:
            reconstructed = self._reconstruct_element(element, translated_map, soup)
            if reconstructed:
                container.append(reconstructed)

        # Post-processing
        html_content = str(soup)

        if self.config.cleanup_empty_elements:
            html_content = self._cleanup_empty_elements(html_content)

        logger.info(
            "HTML reconstruction complete",
            output_length=len(html_content)
        )

        return html_content

    def _reconstruct_element(
        self,
        element: ContentElement,
        translated_map: Dict[str, str],
        soup: BeautifulSoup
    ) -> Optional[Tag]:
        """
        Reconstruct a single element.

        Args:
            element: Content element to reconstruct
            translated_map: Translation mapping
            soup: BeautifulSoup document

        Returns:
            Reconstructed HTML tag
        """
        # Handle special content types
        if element.element_type == ContentType.CODE:
            return self._reconstruct_code_element(element, soup)
        elif element.element_type == ContentType.IMAGE:
            return self._reconstruct_image_element(element, soup)
        elif element.element_type == ContentType.LINK:
            return self._reconstruct_link_element(element, soup)
        elif element.element_type == ContentType.METADATA:
            return None  # Skip metadata

        # Create appropriate tag
        tag = self._create_tag(element.element_type, soup, element)

        # Add attributes
        self._add_attributes(tag, element)

        # Add content or children
        if element.should_translate and element.element_type == ContentType.TEXT:
            # Add translated text
            translated_text = translated_map.get(element.content, element.content)
            tag.string = translated_text

            # Add translation marker if configured
            if self.config.add_translation_markers:
                tag['data-translated'] = 'true'
                tag['data-original'] = element.content

        elif element.children:
            # Reconstruct children
            for child in element.children:
                child_tag = self._reconstruct_element(child, translated_map, soup)
                if child_tag:
                    tag.append(child_tag)

        elif element.content:
            # Add original content for non-translatable elements
            tag.string = element.content
            if element.element_type != ContentType.CODE:
                tag['data-preserve'] = 'true'

        return tag

    def _reconstruct_code_element(
        self,
        element: ContentElement,
        soup: BeautifulSoup
    ) -> Tag:
        """Reconstruct a code element."""
        # Determine if it's inline or block code
        is_inline = (
            element.element_type == ContentType.INLINE_CODE or
            not element.attributes.get('class', [])
        )

        if is_inline:
            tag = soup.new_tag("code")
        else:
            tag = soup.new_tag("pre")
            code_tag = soup.new_tag("code")
            tag.append(code_tag)
            tag = code_tag

        # Add language class if specified
        if 'language' in element.attributes:
            tag['class'] = f"language-{element.attributes['language']}"

        # Add original content
        tag.string = element.content
        tag['data-preserve'] = 'true'

        return tag

    def _reconstruct_image_element(
        self,
        element: ContentElement,
        soup: BeautifulSoup
    ) -> Tag:
        """Reconstruct an image element."""
        tag = soup.new_tag("img")

        # Add attributes
        for attr, value in element.attributes.items():
            if attr in ['src', 'alt', 'title', 'width', 'height', 'class', 'id']:
                tag[attr] = value

        # Ensure essential attributes
        if 'src' not in element.attributes and 'data-src' in element.attributes:
            tag['src'] = element.attributes['data-src']

        tag['data-preserve'] = 'true'
        return tag

    def _reconstruct_link_element(
        self,
        element: ContentElement,
        soup: BeautifulSoup
    ) -> Tag:
        """Reconstruct a link element."""
        tag = soup.new_tag("a")

        # Add attributes
        for attr, value in element.attributes.items():
            if attr in ['href', 'title', 'target', 'class', 'id']:
                tag[attr] = value

        # Add content (typically don't translate URLs)
        tag.string = element.content
        tag['data-preserve'] = 'true'

        return tag

    def _create_tag(self, element_type: ContentType, soup: BeautifulSoup, element=None) -> Tag:
        """Create appropriate HTML tag for element type."""
        tag_mapping = {
            ContentType.TEXT: "p",
            ContentType.HEADING: "p",  # Will be updated based on attributes
            ContentType.LIST: "ul",  # Default to unordered list
            ContentType.QUOTE: "blockquote",
            ContentType.EMPHASIS: "em",
            ContentType.STRONG: "strong",
            ContentType.TABLE: "table",
            ContentType.CODE: "code",
        }

        tag_name = tag_mapping.get(element_type, "div")

        if element_type == ContentType.HEADING and element and 'level' in element.attributes:
            level = element.attributes['level']
            if isinstance(level, int) and 1 <= level <= 6:
                tag_name = f"h{level}"

        return soup.new_tag(tag_name)

    def _add_attributes(self, tag: Tag, element: ContentElement) -> None:
        """Add attributes to reconstructed tag."""
        for attr, value in element.attributes.items():
            # Skip internal attributes
            if attr.startswith('_'):
                continue

            # Skip content attributes
            if attr in ['content', 'text']:
                continue

            # Attribute filtering based on config
            if attr == 'class' and not self.config.preserve_classes:
                continue
            elif attr == 'id' and not self.config.preserve_ids:
                continue
            elif attr.startswith('data-') and not self.config.preserve_data_attributes:
                continue
            elif attr == 'style' and not self.config.preserve_style:
                continue

            tag[attr] = value

    def _cleanup_empty_elements(self, html: str) -> str:
        """Remove empty elements from HTML."""
        # Remove empty tags
        html = re.sub(r'<([a-z]+)[^>]*>\s*</\1>', '', html)

        # Remove extra whitespace
        html = re.sub(r'\s+', ' ', html)

        # Clean up around tags
        html = re.sub(r'>\s+<', '><', html)
        html = re.sub(r'\s+', ' ', html)

        return html.strip()

    def inject_translated_text(
        self,
        html_content: str,
        translated_segments: List[Dict[str, Any]]
    ) -> str:
        """
        Inject translated text segments into HTML content.

        Args:
            html_content: Original HTML content
            translated_segments: List of translated text segments with positions

        Returns:
            HTML content with translated text injected
        """
        logger.info(
            "Injecting translated text",
            segments_count=len(translated_segments)
        )

        # Sort segments by position (reverse order to maintain indices)
        segments = sorted(translated_segments, key=lambda x: x.get('position', 0), reverse=True)

        result = html_content
        for segment in segments:
            start = segment.get('start', 0)
            end = segment.get('end', len(result))
            translated_text = segment.get('translated_text', '')

            # Replace the segment
            result = result[:start] + translated_text + result[end:]

        return result

    def create_translation_markers(
        self,
        elements: List[ContentElement]
    ) -> List[Dict[str, Any]]:
        """
        Create marker positions for text segments to be translated.

        Args:
            elements: Parsed content elements

        Returns:
            List of marker positions
        """
        markers = []
        current_position = 0

        for element in elements:
            if element.should_translate and element.element_type == ContentType.TEXT:
                text = element.content
                if text.strip():
                    markers.append({
                        'start': current_position,
                        'end': current_position + len(text),
                        'original_text': text,
                        'element_id': id(element)
                    })
                    current_position += len(text)

        logger.info(
            "Created translation markers",
            markers_count=len(markers),
            text_length=current_position
        )

        return markers

    def validate_reconstruction(
        self,
        original_html: str,
        reconstructed_html: str,
        original_elements: List[ContentElement],
        reconstructed_elements: List[ContentElement]
    ) -> Dict[str, Any]:
        """
        Validate the reconstruction process.

        Args:
            original_html: Original HTML content
            reconstructed_html: Reconstructed HTML content
            original_elements: Original parsed elements
            reconstructed_elements: Reconstructed elements

        Returns:
            Validation report
        """
        report = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {
                'original_length': len(original_html),
                'reconstructed_length': len(reconstructed_html),
                'original_elements': len(original_elements),
                'reconstructed_elements': len(reconstructed_elements)
            }
        }

        # Check element counts
        original_types = self._count_elements_by_type(original_elements)
        reconstructed_types = self._count_elements_by_type(reconstructed_elements)

        for element_type, count in original_types.items():
            reconstructed_count = reconstructed_types.get(element_type, 0)
            if count != reconstructed_count:
                report['errors'].append(
                    f"Element count mismatch for {element_type.value}: "
                    f"original={count}, reconstructed={reconstructed_count}"
                )
                report['is_valid'] = False

        # Check code blocks preservation
        original_code = len([e for e in original_elements if e.element_type == ContentType.CODE])
        reconstructed_code = len([e for e in reconstructed_elements if e.element_type == ContentType.CODE])

        if original_code != reconstructed_code:
            report['errors'].append(
                f"Code blocks not preserved: original={original_code}, reconstructed={reconstructed_code}"
            )
            report['is_valid'] = False

        # Check for preserved attributes
        preserved_attributes = self._check_preserved_attributes(
            original_elements,
            reconstructed_elements
        )
        if not preserved_attributes['all_preserved']:
            report['warnings'].extend(preserved_attributes['missing_attributes'])

        logger.info(
            "Reconstruction validation complete",
            is_valid=report['is_valid'],
            errors_count=len(report['errors']),
            warnings_count=len(report['warnings'])
        )

        return report

    def _count_elements_by_type(self, elements: List[ContentElement]) -> Dict[ContentType, int]:
        """Count elements by type."""
        counts = {}
        for element in elements:
            counts[element.element_type] = counts.get(element.element_type, 0) + 1
        return counts

    def _check_preserved_attributes(
        self,
        original_elements: List[ContentElement],
        reconstructed_elements: List[ContentElement]
    ) -> Dict[str, Any]:
        """Check if important attributes are preserved."""
        result = {
            'all_preserved': True,
            'missing_attributes': []
        }

        important_attrs = ['id', 'class', 'href', 'src', 'alt']

        # This is a simplified check
        # In practice, you'd want more sophisticated comparison
        for orig_elem in original_elements:
            for attr in important_attrs:
                if attr in orig_elem.attributes:
                    result['missing_attributes'].append(
                        f"Attribute '{attr}' may not be preserved in element {orig_elem.element_type.value}"
                    )

        if result['missing_attributes']:
            result['all_preserved'] = False

        return result