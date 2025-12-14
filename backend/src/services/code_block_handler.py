"""
Code Block Handler for Translation System.

This module handles detection, preservation, and intelligent processing
of code blocks during translation.
"""

import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from bs4 import BeautifulSoup, Tag
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from src.utils.translation_logger import get_translation_logger

logger = get_translation_logger(__name__)


class CodeBlockType(Enum):
    """Types of code blocks."""
    MARKDOWN = "markdown"
    HTML_PRE = "html_pre"
    HTML_INLINE = "html_inline"
    INDENTED = "indented"
    FENCED = "fenced"


@dataclass
class CodeBlock:
    """Represents a detected code block."""
    block_type: CodeBlockType
    language: Optional[str]
    content: str
    original_text: str
    start_position: int
    end_position: int
    attributes: Dict[str, Any]
    preserve_formatting: bool = True
    add_urdu_comments: bool = False
    translated: bool = False


class CodeBlockHandler:
    """
    Handles code block detection, preservation, and processing.

    Features:
    - Multi-format code block detection
    - Language identification
    - Format preservation
    - Urdu comment injection
    - Syntax highlighting
    - Code validation
    """

    # Code block patterns
    PATTERNS = {
        CodeBlockType.MARKDOWN: [
            re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL),
            re.compile(r'~~~(\w+)?\n(.*?)\n~~~', re.DOTALL),
        ],
        CodeBlockType.HTML_PRE: [
            re.compile(r'<pre[^>]*>.*?<code[^>]*>(.*?)</code>.*?</pre>', re.DOTALL | re.IGNORECASE),
        ],
        CodeBlockType.HTML_INLINE: [
            re.compile(r'<code[^>]*>(.*?)</code>', re.DOTALL | re.IGNORECASE),
        ],
        CodeBlockType.INDENTED: [
            # Detect 4+ spaces or tabs at start of line
            re.compile(r'^(    |\t).*$', re.MULTILINE),
        ],
    }

    # Language patterns for detection
    LANGUAGE_PATTERNS = {
        'python': [r'import\s+\w+', r'def\s+\w+', r'class\s+\w+', r'if\s+__name__\s*=='],
        'javascript': [r'function\s+\w+', r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'var\s+\w+\s*='],
        'java': [r'public\s+class\s+\w+', r'private\s+\w+\s+\w+', r'import\s+java\.'],
        'cpp': [r'#include\s*<', r'using\s+namespace\s+', r'::\w+\s*\('],
        'html': [r'<!DOCTYPE\s+html>', r'<html[^>]*>', r'<div[^>]*>'],
        'css': [r'\.[\w-]+\s*{', r'#[\w-]+\s*{', r'@\w+\s*\w+\s*{'],
        'sql': [r'SELECT\s+', r'FROM\s+', r'WHERE\s+', r'INSERT\s+INTO'],
        'json': [r'^\s*{\s*"', r'^\s*\[', r'"[^"]*":\s*'],
        'yaml': [r'^\s*\w+:', r'^\s+-\s+', r'^\s*  \w+:'],
        'bash': [r'#!/bin/bash', r'echo\s+', r'export\s+\w+='],
        'powershell': [r'Write-Host\s+', r'$\w+\s*=', r'Get-'],
        'dockerfile': [r'FROM\s+\w+', r'RUN\s+', r'CMD\s+'],
    }

    # Common programming keywords
    PROGRAMMING_KEYWORDS = [
        'function', 'class', 'import', 'export', 'return', 'if', 'else', 'for', 'while',
        'def', 'var', 'let', 'const', 'try', 'catch', 'throw', 'new', 'this', 'super'
    ]

    def __init__(self):
        """Initialize code block handler."""
        self.detected_languages: Set[str] = set()
        self.urdu_comments = {
            'python': '#',
            'javascript': '//',
            'java': '//',
            'cpp': '//',
            'c': '//',
            'css': '/*',
            'sql': '--',
            'bash': '#',
            'powershell': '#',
        }

    def detect_code_blocks(
        self,
        content: str,
        source_format: str = "html"
    ) -> List[CodeBlock]:
        """
        Detect all code blocks in content.

        Args:
            content: Content to analyze
            source_format: Format type (html, markdown, etc.)

        Returns:
            List of detected code blocks
        """
        logger.info(
            "Detecting code blocks",
            content_length=len(content),
            source_format=source_format
        )

        blocks = []

        # Try each pattern type
        for block_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = list(pattern.finditer(content))
                for match in matches:
                    block = self._create_code_block(
                        match, block_type, content
                    )
                    if block:
                        blocks.append(block)

        # Remove duplicates (blocks that overlap)
        blocks = self._remove_overlapping_blocks(blocks)

        # Detect language for each block
        for block in blocks:
            block.language = self._detect_language(block.content)

        logger.info(
            "Code blocks detected",
            total_blocks=len(blocks),
            languages=list(set(b.language for b in blocks if b.language)),
            block_types=[b.block_type.value for b in blocks]
        )

        return blocks

    def _create_code_block(
        self,
        match: re.Match,
        block_type: CodeBlockType,
        content: str
    ) -> Optional[CodeBlock]:
        """Create a CodeBlock object from a regex match."""
        start_pos = match.start()
        end_pos = match.end()
        original_text = match.group(0)

        if block_type in [CodeBlockType.MARKDOWN, CodeBlockType.FENCED]:
            # Extract language from fence
            language = match.group(1) if match.groups() and match.group(1) else None
            code_content = match.group(2) if match.groups() and len(match.groups()) > 1 else ""
        elif block_type == CodeBlockType.HTML_PRE:
            # Extract from HTML pre/code structure
            soup = BeautifulSoup(original_text, 'html.parser')
            code_tag = soup.find('code')
            if code_tag:
                language = self._extract_language_from_classes(code_tag.get('class', []))
                code_content = code_tag.get_text()
            else:
                language = None
                code_content = original_text
        elif block_type == CodeBlockType.HTML_INLINE:
            # Inline code
            soup = BeautifulSoup(original_text, 'html.parser')
            code_content = soup.get_text()
            language = None
        else:
            # Other types
            code_content = original_text
            language = None

        if not code_content.strip():
            return None

        return CodeBlock(
            block_type=block_type,
            language=language,
            content=code_content,
            original_text=original_text,
            start_position=start_pos,
            end_position=end_pos,
            attributes={'match_groups': match.groups()},
            preserve_formatting=True,
            add_urdu_comments=self._should_add_urdu_comments(code_content, language)
        )

    def _remove_overlapping_blocks(self, blocks: List[CodeBlock]) -> List[CodeBlock]:
        """Remove overlapping code blocks."""
        if not blocks:
            return []

        # Sort by start position
        blocks.sort(key=lambda x: x.start_position)

        filtered_blocks = []
        last_end = -1

        for block in blocks:
            if block.start_position >= last_end:
                filtered_blocks.append(block)
                last_end = block.end_position

        return filtered_blocks

    def _detect_language(self, code_content: str) -> Optional[str]:
        """Detect the programming language of code content."""
        # Try language hints first
        language = self._detect_language_from_hints(code_content)
        if language:
            return language

        # Try pattern matching
        language = self._detect_language_from_patterns(code_content)
        if language:
            return language

        # Use pygments as fallback
        try:
            lexer = guess_lexer(code_content)
            if lexer:
                return lexer.name.lower()
        except:
            pass

        return None

    def _detect_language_from_hints(self, code_content: str) -> Optional[str]:
        """Detect language from explicit hints."""
        # Check for shebang
        shebang_match = re.match(r'^#!\s*/.*(?:python|node|bash|perl|ruby|php)\s*', code_content, re.MULTILINE)
        if shebang_match:
            shebang = shebang_match.group()
            if 'python' in shebang:
                return 'python'
            elif 'node' in shebang:
                return 'javascript'
            elif 'bash' in shebang:
                return 'bash'
            elif 'perl' in shebang:
                return 'perl'
            elif 'ruby' in shebang:
                return 'ruby'
            elif 'php' in shebang:
                return 'php'

        # Check for language comments
        if code_content.strip().startswith('#!'):
            return 'bash'  # Likely shell script

        return None

    def _detect_language_from_patterns(self, code_content: str) -> Optional[str]:
        """Detect language using pattern matching."""
        scores = {}

        for language, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(list(re.finditer(pattern, code_content, re.MULTILINE)))
                score += matches

            if score > 0:
                scores[language] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return None

    def _extract_language_from_classes(self, classes: List[str]) -> Optional[str]:
        """Extract language from CSS classes."""
        for cls in classes:
            if isinstance(cls, str):
                # Check for language- prefixed classes
                if cls.startswith('language-'):
                    return cls[9:]
                # Check for known language classes
                if cls.lower() in ['python', 'javascript', 'java', 'cpp', 'c', 'html', 'css', 'sql', 'json']:
                    return cls.lower()
                # Check for highlight.js classes
                if cls.startswith('hljs-'):
                    lang = cls[5:]
                    if lang != 'language':
                        return lang

        return None

    def _should_add_urdu_comments(self, code_content: str, language: Optional[str]) -> bool:
        """Determine if Urdu comments should be added."""
        if not language or language not in self.urdu_comments:
            return False

        # Don't add comments to very short code blocks
        if len(code_content.split('\n')) < 3:
            return False

        # Don't add if there are already comments in the target language
        comment_char = self.urdu_comments[language]
        if comment_char and comment_char in code_content:
            # Check for non-English characters in comments
            comment_pattern = re.compile(f'{re.escape(comment_char)}.*[^\x00-\x7F]+')
            if comment_pattern.search(code_content):
                return False

        return True

    def add_urdu_comments(self, code_block: CodeBlock) -> str:
        """
        Add Urdu explanatory comments to code block.

        Args:
            code_block: Code block to enhance

        Returns:
            Code block with Urdu comments added
        """
        if not code_block.language or not code_block.add_urdu_comments:
            return code_block.content

        language = code_block.language
        comment_char = self.urdu_comments[language]

        lines = code_block.content.split('\n')
        enhanced_lines = []

        for i, line in enumerate(lines):
            enhanced_lines.append(line)

            # Add comments after key lines
            if self._is_comment_line(line, language):
                continue

            # Add Urdu comment after function definitions
            if re.search(r'^(def|function|class|interface)\s+\w+', line):
                # Extract function/class name
                match = re.search(r'(def|function|class|interface)\s+(\w+)', line)
                if match:
                    name = match.group(2)
                    urdu_translation = self._translate_code_name(name)
                    enhanced_lines.append(f"{comment_char} {urdu_translation}")

            # Add comment after important statements
            elif re.search(r'\b(return|break|continue|pass)\b', line):
                urdu_comment = self._translate_statement(line.strip())
                if urdu_comment:
                    enhanced_lines.append(f"{comment_char} {urdu_comment}")

            # Add comment after imports
            elif re.match(r'^(import|from|include)\s+', line):
                urdu_comment = self._translate_import(line.strip())
                if urdu_comment:
                    enhanced_lines.append(f"{comment_char} {urdu_comment}")

        return '\n'.join(enhanced_lines)

    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if line is already a comment."""
        comment_char = self.urdu_comments.get(language, '')
        return comment_char and line.strip().startswith(comment_char)

    def _translate_code_name(self, name: str) -> str:
        """Translate a code identifier to Urdu."""
        # Common translations
        translations = {
            'main': 'مین',
            'init': 'ابتدائی',
            'start': 'شروع',
            'setup': 'سیٹ اپ',
            'run': 'چلائیں',
            'process': 'عملدرس',
            'handle': 'ہینڈل کریں',
            'update': 'اپڈیٹ کرنا',
            'get': 'حاصل کریں',
            'set': 'سیٹ کرنا',
            'create': 'بنانا',
            'delete': 'حذف کرنا',
            'calculate': 'حساب لگانا',
            'validate': 'تصدیق کرنا',
            'convert': 'تبدیل کرنا',
            'transform': 'تبدیل کرنا',
            'parse': 'پارس کرنا',
            'render': 'رینڈر کرنا',
            'fetch': 'لانا',
            'send': 'بھیجنا',
            'receive': 'صول کرنا',
            'connect': 'ربط جوڑنا',
            'close': 'بند کرنا',
            'open': 'کھولنا',
            'save': 'محفوظ کرنا',
            'load': 'لوڈ کرنا',
            'read': 'پڑھنا',
            'write': 'لکھنا',
        }

        return translations.get(name, name)

    def _translate_statement(self, statement: str) -> str:
        """Translate a code statement to Urdu."""
        # Common statement translations
        translations = {
            'return': 'واپس کریں',
            'break': 'روک جائیں',
            'continue': 'جاری رکھیں',
            'pass': 'چھوٹ دیں',
            'yield': 'دیں',
            'raise': 'پھلاؤ',
            'try': 'کوشش کریں',
            'except': 'چھوٹ',
            'finally': 'آخر میں',
            'assert': 'تصدیق کریں',
            'del': 'حذف کریں',
        }

        # Extract keyword
        match = re.search(r'\b(' + '|'.join(translations.keys()) + r')\b', statement)
        if match:
            keyword = match.group(1)
            translated = translations.get(keyword, keyword)
            return statement.replace(keyword, translated, 1)

        return None

    def _translate_import(self, import_statement: str) -> str:
        """Translate an import statement to Urdu."""
        if 'import ' in import_statement:
            return 'لائبریری امپورٹ کریں'
        elif 'from ' in import_statement:
            return 'سے امپورٹ کریں'
        elif 'include ' in import_statement:
            return 'شامل کریں'

        return None

    def preserve_code_blocks(
        self,
        original_content: str,
        translated_content: str,
        code_blocks: List[CodeBlock]
    ) -> str:
        """
        Preserve code blocks in translated content.

        Args:
            original_content: Original content with code blocks
            translated_content: Translated content
            code_blocks: Detected code blocks

        Returns:
            Content with original code blocks preserved
        """
        logger.info(
            "Preserving code blocks",
            original_blocks=len(code_blocks)
        )

        # Replace translated code blocks with original ones
        result = translated_content
        blocks_preserved = 0

        for block in code_blocks:
            # Find and replace the corresponding block in translated content
            # This is simplified - in practice, you'd want more precise matching
            translated_block_content = self._find_translated_block(
                result, block, original_content
            )

            if translated_block_content is not None:
                # Replace with original
                result = result.replace(
                    translated_block_content,
                    block.original_text,
                    1
                )
                blocks_preserved += 1

                # Add Urdu comments if configured
                if block.add_urdu_comments:
                    enhanced_code = self.add_urdu_comments(block)
                    result = result.replace(
                        block.original_text,
                        enhanced_code,
                        1
                    )

        logger.info(
            "Code blocks preserved",
            blocks_preserved=blocks_preserved,
            blocks_total=len(code_blocks)
        )

        return result

    def _find_translated_block(
        self,
        content: str,
        original_block: CodeBlock,
        original_content: str
    ) -> Optional[str]:
        """Find the translated version of a code block."""
        # This is a simplified implementation
        # In practice, you'd track blocks more precisely during translation

        # Look for the block content in the translated content
        # This might not work perfectly due to translation changes
        if original_block.content in content:
            return original_block.content

        # Try to find by looking for unique lines
        original_lines = original_block.content.split('\n')
        if len(original_lines) > 3:
            # Use first and last lines as markers
            first_line = original_lines[0]
            last_line = original_lines[-1]

            if first_line in content and last_line in content:
                # Extract content between markers
                start = content.find(first_line)
                end = content.rfind(last_line) + len(last_line)
                return content[start:end]

        return None

    def add_syntax_highlighting(
        self,
        code_block: CodeBlock,
        theme: str = "default"
    ) -> str:
        """
        Add syntax highlighting to a code block.

        Args:
            code_block: Code block to highlight
            theme: Highlighting theme

        Returns:
            HTML with syntax highlighting
        """
        try:
            lexer = get_lexer_by_name(code_block.language or 'text')
            formatter = HtmlFormatter(
                style=theme,
                linenos=True,
                cssclass="highlight"
            )
            return highlight(code_block.content, lexer, formatter)
        except:
            # Fallback to plain code block
            return f'<pre><code>{code_block.content}</code></pre>'

    def validate_code_blocks(
        self,
        code_blocks: List[CodeBlock],
        content: str
    ) -> Dict[str, Any]:
        """
        Validate detected code blocks.

        Args:
            code_blocks: Detected code blocks
            content: Original content

        Returns:
            Validation report
        """
        report = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'stats': {
                'total_blocks': len(code_blocks),
                'languages_detected': list(set(b.language for b in code_blocks if b.language)),
                'blocks_with_languages': len([b for b in code_blocks if b.language])
            }
        }

        for block in code_blocks:
            # Check for empty blocks
            if not block.content.strip():
                report['warnings'].append(
                    f"Empty code block at position {block.start_position}"
                )

            # Check for very long blocks
            if len(block.content) > 10000:
                report['warnings'].append(
                    f"Very long code block ({len(block.content)} chars) at position {block.start_position}"
                )

            # Check for potential formatting issues
            if block.block_type == CodeBlockType.INDENTED and block.content.strip():
                report['warnings'].append(
                    f"Indented code block detected at position {block.start_position} - might be unintentional"
                )

        logger.info(
            "Code block validation complete",
            total_warnings=len(report['warnings']),
            total_errors=len(report['errors'])
        )

        return report