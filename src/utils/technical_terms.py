"""
Technical terms transliteration utilities.

Provides functions for transliterating common technical terms with context-aware handling.
Supports various transliteration strategies and maintains technical term consistency.
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)


class TransliterationStrategy(Enum):
    """Transliteration strategies."""
    TRANSLATE = "translate"           # Translate the term
    TRANSLITERATE = "transliterate"   # Keep the English word but write in Urdu script
    KEEP_ENGLISH = "keep_english"     # Keep the English word as is


class TermContext(Enum):
    """Context categories for terms."""
    GENERAL = "general"             # General context
    CODE = "code"                   # In code context
    TECHNICAL = "technical"         # Technical documentation
    TUTORIAL = "tutorial"           # Tutorial/instructional
    REFERENCE = "reference"         # Reference material


@dataclass
class TransliterationEntry:
    """Represents a transliteration entry."""
    english: str
    urdu: str
    urdu_roman: str
    category: str
    strategy: TransliterationStrategy
    variations: Optional[List[str]] = None
    context_rules: Optional[Dict[TermContext, TransliterationStrategy]] = None


class TechnicalTermsTransliterator:
    """
    Transliterator for technical terms with context-aware handling.

    Features:
    - Predefined transliteration map
    - Context-aware strategy selection
    - Pattern matching for term detection
    - Custom transliteration rules
    - Variation handling
    """

    # Default transliteration map from spec
    DEFAULT_TRANSLITERATION_MAP = {
        # AI/ML Terms
        "artificial intelligence": "آرٹیفیشل انٹیلیجنس",
        "machine learning": "مشین لرننگ",
        "deep learning": "ڈیپ لرننگ",
        "neural network": "نیورل نیٹ ورک",
        "algorithm": "الگورتھم",
        "data science": "ڈیٹا سائنس",
        "big data": "بگ ڈیٹا",
        "analytics": "اینالیٹکس",
        "prediction": "پریڈکشن",
        "classification": "کلاسیفیکیشن",
        "regression": "ریگریشن",
        "clustering": "کلسٹرنگ",
        "optimization": "آپٹمائیزیشن",

        # Software Terms
        "database": "ڈیٹا بیس",
        "application": "ایپلی کیشن",
        "interface": "انٹرفیس",
        "framework": "فریم ورک",
        "library": "لائبریری",
        "api": "اے پی آئی",
        "backend": "بیک اینڈ",
        "frontend": "فرنٹ اینڈ",
        "server": "سرور",
        "client": "کلائنٹ",
        "authentication": "آتھنٹیکیشن",
        "authorization": "آتھاریزیشن",
        "encryption": "اینکریپشن",
        "deployment": "ڈپلائمنٹ",
        "version control": "ورژن کنٹرول",

        # Web Terms
        "website": "ویب سائٹ",
        "webpage": "ویب پیج",
        "browser": "براؤزر",
        "hyperlink": "ہائپرلنک",
        "url": "یو آر ایل",
        "domain": "ڈومین",
        "hosting": "ہوسٹنگ",
        "responsive": "رسپانسیو",

        # Programming Terms
        "variable": "وری ایبل",
        "function": "فنکشن",
        "method": "میٹھڈ",
        "class": "کلاس",
        "object": "آبجیکٹ",
        "inheritance": "انہیریٹنس",
        "polymorphism": "پولیمارفزم",
        "encapsulation": "اینکیپسولیشن",
        "abstraction": "ایبسٹریکشن",
        "debugging": "ڈیبگنگ",
        "compilation": "کمپائلیشن",
        "runtime": "رن ٹائم",

        # Hardware Terms
        "processor": "پروسسور",
        "memory": "میموری",
        "storage": "اسٹوریج",
        "motherboard": "درڈ",
        "graphics card": "گرافکس کارڈ",
        "power supply": "پاور سپلائی",
        "cooling system": "کولنگ سسٹم",
        "peripheral": "پیرفرل",

        # Networking Terms
        "network": "نیٹ ورک",
        "router": "روٹر",
        "switch": "سوئچ",
        "firewall": "فائر وال",
        "bandwidth": "بینڈوتھ",
        "latency": "لیٹنسی",
        "protocol": "پروٹوکول",
        "ip address": "آئی پی ایڈریس",
        "packet": "پیکیٹ",
        "port": "پورٹ",
    }

    # Roman transliterations for common terms
    ROMAN_TRANSLITERATIONS = {
        "آرٹیفشل انٹیلیجنس": "artificial intelligence",
        "مشین لرننگ": "machine learning",
        "ڈیپ لرننگ": "deep learning",
        "نیورل نیٹ ورک": "neural network",
        "الگورتھم": "algorithm",
        "ڈیٹا سائنس": "data science",
        "اے پی آئی": "API",
        "بیک اینڈ": "backend",
        "فرنٹ اینڈ": "frontend",
        "سرور": "server",
        "کلائنٹ": "client",
        "ڈیٹا بیس": "database",
        "ورژن کنٹرول": "version control",
        "ویب سائٹ": "website",
        "براؤزر": "browser",
        "یو آر ایل": "URL",
        "پروسسور": "processor",
        "میموری": "memory",
        "نیٹ ورک": "network",
        "روٹر": "router",
        "آئی پی ایڈریس": "IP address",
    }

    # Context patterns for term detection
    CONTEXT_PATTERNS = {
        TermContext.CODE: [
            r'```[\s\S]*?```',      # Code blocks
            r'<code>[\s\S]*?</code>', # HTML code tags
            r'`[^`]+`',              # Inline code
        ],
        TermContext.TECHNICAL: [
            r'\b(technical|implementation|architecture|configuration)\b',
            r'\b(install|setup|configure|deploy)\b',
        ],
        TermContext.TUTORIAL: [
            r'\b(tutorial|guide|how to|step|learn)\b',
            r'\b(example|demo|practice)\b',
        ],
    }

    def __init__(
        self,
        transliteration_map: Optional[Dict[str, str]] = None,
        default_strategy: TransliterationStrategy = TransliterationStrategy.TRANSLITERATE,
        preserve_acronyms: bool = True
    ):
        """
        Initialize technical terms transliterator.

        Args:
            transliteration_map: Custom transliteration map
            default_strategy: Default transliteration strategy
            preserve_acronyms: Whether to preserve common acronyms
        """
        self.transliteration_map = transliteration_map or self.DEFAULT_TRANSLITERATION_MAP
        self.default_strategy = default_strategy
        self.preserve_acronyms = preserve_acronyms

        # Build term variations map
        self.term_variations = self._build_term_variations()

        # Compile context patterns
        self.context_patterns = {
            ctx: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for ctx, patterns in self.CONTEXT_PATTERNS.items()
        }

        logger.info(
            "Technical terms transliterator initialized",
            map_size=len(self.transliteration_map),
            default_strategy=default_strategy.value
        )

    def _build_term_variations(self) -> Dict[str, str]:
        """Build a map of term variations to canonical form."""
        variations = {}

        for term in self.transliteration_map:
            # Add original term
            variations[term.lower()] = term

            # Add singular/plural variations
            if term.endswith('s'):
                variations[term[:-1].lower()] = term
            elif not term.endswith('s'):
                variations[term.lower() + 's'] = term

            # Add common variations
            term_lower = term.lower()
            if ' ' in term_lower:
                # Add hyphenated version
                variations[term_lower.replace(' ', '-')] = term
                # Add camelCase version
                words = term_lower.split()
                variations[''.join(words[0].lower() + w.capitalize() for w in words[1:])] = term

        return variations

    def detect_context(self, text: str, position: int) -> TermContext:
        """
        Detect the context of a term at a given position.

        Args:
            text: Full text
            position: Position of the term

        Returns:
            Detected context
        """
        # Check code context first
        for ctx in [TermContext.CODE, TermContext.TECHNICAL, TermContext.TUTORIAL]:
            if ctx in self.context_patterns:
                for pattern in self.context_patterns[ctx]:
                    if pattern.search(text):
                        return ctx

        return TermContext.GENERAL

    def should_preserve_term(self, term: str, context: TermContext) -> bool:
        """
        Determine if a term should be preserved based on context.

        Args:
            term: Term to check
            context: Detected context

        Returns:
            True if term should be preserved
        """
        # Always preserve in code context
        if context == TermContext.CODE:
            return True

        # Preserve acronyms if enabled
        if self.preserve_acronyms and term.isupper() and len(term) <= 5:
            return True

        # Preserve short technical terms in any context
        if len(term.split()) == 1 and len(term) <= 8:
            return True

        return False

    def find_terms_in_text(self, text: str) -> List[Tuple[str, int, int, TermContext]]:
        """
        Find all technical terms in text with their positions and context.

        Args:
            text: Text to search

        Returns:
            List of (term, start, end, context) tuples
        """
        found_terms = []

        # Sort terms by length (longest first) for better matching
        sorted_terms = sorted(self.transliteration_map.keys(), key=len, reverse=True)

        for term in sorted_terms:
            # Find all occurrences of the term
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)

            for match in pattern.finditer(text):
                start, end = match.span()
                context = self.detect_context(text, start)
                found_terms.append((term, start, end, context))

        # Sort by position
        found_terms.sort(key=lambda x: x[1])

        # Remove overlapping matches
        non_overlapping = []
        last_end = 0

        for term, start, end, context in found_terms:
            if start >= last_end:
                non_overlapping.append((term, start, end, context))
                last_end = end

        return non_overlapping

    def transliterate_term(
        self,
        term: str,
        context: TermContext,
        strategy: Optional[TransliterationStrategy] = None,
        target_format: str = "urdu"
    ) -> str:
        """
        Transliterate a single term.

        Args:
            term: Term to transliterate
            context: Term context
            strategy: Transliteration strategy to use
            target_format: Target format ("urdu" or "urdu-roman")

        Returns:
            Transliterated term
        """
        # Use provided strategy or default
        strategy = strategy or self.default_strategy

        # Check if we should preserve the term
        if self.should_preserve_term(term, context):
            return term

        # Get canonical term
        canonical_term = self.term_variations.get(term.lower(), term)

        # Get transliteration
        if canonical_term in self.transliteration_map:
            if target_format == "urdu":
                return self.transliteration_map[canonical_term]
            elif target_format == "urdu-roman":
                urdu_text = self.transliteration_map[canonical_term]
                return self.ROMAN_TRANSLITERATIONS.get(urdu_text, canonical_term)

        # Fallback: if no transliteration found
        if strategy == TransliterationStrategy.KEEP_ENGLISH:
            return term
        elif strategy == TransliterationStrategy.TRANSLITERATE:
            # Simple phonetic transliteration fallback
            return self._phonetic_transliterate(term)
        else:
            # Default to original term
            return term

    def _phonetic_transliterate(self, term: str) -> str:
        """
        Simple phonetic transliteration fallback.

        Args:
            term: Term to transliterate

        Returns:
            Phonetically transliterated term
        """
        # This is a very basic implementation
        # In a production system, you'd use a proper transliteration library
        phonetic_map = {
            'a': 'ا', 'b': 'ب', 'c': 'ک', 'd': 'ڈ', 'e': 'ے',
            'f': 'ف', 'g': 'گ', 'h': 'ہ', 'i': 'ی', 'j': 'ج',
            'k': 'ک', 'l': 'ل', 'm': 'م', 'n': 'ن', 'o': 'و',
            'p': 'پ', 'q': 'ق', 'r': 'ر', 's': 'س', 't': 'ٹ',
            'u': 'u', 'v': 'و', 'w': 'و', 'x': 'ایکس', 'y': 'ائی',
            'z': 'ذ'
        }

        result = []
        for char in term.lower():
            if char in phonetic_map:
                result.append(phonetic_map[char])
            else:
                result.append(char)

        return ''.join(result)

    def transliterate_text(
        self,
        text: str,
        target_format: str = "urdu",
        preserve_code_blocks: bool = True
    ) -> str:
        """
        Transliterate all technical terms in text.

        Args:
            text: Text to process
            target_format: Target format ("urdu" or "urdu-roman")
            preserve_code_blocks: Whether to preserve code blocks

        Returns:
            Text with transliterated terms
        """
        if preserve_code_blocks:
            # Extract code blocks to preserve them
            code_blocks = []
            modified_text = text
            offset = 0

            code_pattern = re.compile(r'```[\s\S]*?```|`[^`]+`')
            for match in code_pattern.finditer(text):
                code_blocks.append((match.start(), match.end(), match.group()))
                placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
                modified_text = modified_text[:match.start() + offset] + placeholder + modified_text[match.end() + offset:]
                offset += len(placeholder) - len(match.group())
        else:
            modified_text = text

        # Find and replace technical terms
        found_terms = self.find_terms_in_text(modified_text)
        result = list(modified_text)

        # Process terms from end to start to avoid position shifts
        for term, start, end, context in reversed(found_terms):
            transliterated = self.transliterate_term(term, context, target_format=target_format)
            if transliterated != term:
                result[start:end] = transliterated

        # Restore code blocks if preserved
        if preserve_code_blocks and code_blocks:
            result_text = ''.join(result)
            for i, (s, e, code) in enumerate(code_blocks):
                placeholder = f"__CODE_BLOCK_{i + 1}__"
                result_text = result_text.replace(placeholder, code)
            return result_text

        return ''.join(result)

    def add_custom_transliteration(
        self,
        english: str,
        urdu: str,
        urdu_roman: str,
        category: str = "custom",
        strategy: TransliterationStrategy = TransliterationStrategy.TRANSLITERATE
    ):
        """
        Add a custom transliteration entry.

        Args:
            english: English term
            urdu: Urdu transliteration
            urdu_roman: Urdu roman transliteration
            category: Term category
            strategy: Transliteration strategy
        """
        self.transliteration_map[english.lower()] = urdu
        self.ROMAN_TRANSLITERATIONS[urdu] = urdu_roman

        # Update variations
        self._build_term_variations()

        logger.info(
            "Custom transliteration added",
            english=english,
            urdu=urdu,
            category=category
        )

    def get_term_statistics(self) -> Dict[str, any]:
        """
        Get statistics about transliteration coverage.

        Returns:
            Dictionary with statistics
        """
        categories = {}
        for term in self.transliteration_map:
            # Simple categorization based on term content
            if any(word in term for word in ['intelligence', 'learning', 'neural', 'algorithm']):
                categories['ai_ml'] = categories.get('ai_ml', 0) + 1
            elif any(word in term for word in ['database', 'application', 'server', 'client']):
                categories['software'] = categories.get('software', 0) + 1
            elif any(word in term for word in ['web', 'browser', 'url', 'domain']):
                categories['web'] = categories.get('web', 0) + 1
            elif any(word in term for word in ['network', 'router', 'ip', 'protocol']):
                categories['networking'] = categories.get('networking', 0) + 1
            else:
                categories['general'] = categories.get('general', 0) + 1

        return {
            'total_terms': len(self.transliteration_map),
            'variations_count': len(self.term_variations),
            'categories': categories,
            'has_roman_transliterations': len(self.ROMAN_TRANSLITERATIONS)
        }


# Global transliterator instance
_transliterator: Optional[TechnicalTermsTransliterator] = None


def get_technical_terms_transliterator() -> TechnicalTermsTransliterator:
    """Get or create technical terms transliterator instance."""
    global _transliterator

    if _transliterator is None:
        _transliterator = TechnicalTermsTransliterator()

    return _transliterator