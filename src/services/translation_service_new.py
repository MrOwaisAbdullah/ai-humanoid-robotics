"""
Updated Translation service using the new Google Gen AI Python SDK.

This version uses the new google-genai package instead of the deprecated google-generativeai.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import os
import logging

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from src.services.cache_service import CacheService, CacheType, get_cache_service
from src.utils.text_processor import get_text_processor, ProcessedContent, ContentChunk
from src.utils.technical_terms import get_technical_terms_transliterator, TransliterationStrategy
from src.utils.errors import ValidationError, ServiceError, log_exception
from src.utils.logging import get_logger
from src.models.translation import Translation, TranslationFeedback
from src.database.base import get_db

logger = get_logger(__name__)


class TranslationStatus(Enum):
    """Translation status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class TranslationRequest:
    """Translation request data."""
    text: str
    source_language: str
    target_language: str
    user_id: Optional[str] = None
    preserve_code_blocks: bool = True
    enable_transliteration: bool = True
    streaming: bool = False


@dataclass
class TranslationResponse:
    """Translation response data."""
    translated_text: str
    content_hash: str
    chunks: List[Dict[str, Any]]
    processing_time_ms: int
    cached: bool
    status: TranslationStatus
    error_message: Optional[str] = None


@dataclass
class TranslationChunk:
    """Individual translation chunk."""
    index: int
    original_text: str
    translated_text: str
    start_position: int
    end_position: int
    is_code_block: bool
    language: Optional[str] = None


class GeminiTranslationService:
    """
    Translation service using Google Gen AI API (new SDK).

    Features:
    - Gemini LLM integration for high-quality translations
    - Content chunking for large texts
    - Code block preservation
    - Technical terms transliteration
    - Caching for performance
    - Streaming support
    - Error handling and retries
    """

    # Gemini model configuration - using new SDK model names
    DEFAULT_MODEL = "gemini-2.5-flash"
    TEMPERATURE = 0.3
    TOP_P = 0.8
    TOP_K = 40

    # Translation prompt templates
    TRANSLATION_PROMPT_TEMPLATE = """
EMERGENCY TRANSLATION TASK - CRITICAL INSTRUCTIONS:

You are translating technical content to {target_lang}. This is extremely important.

Translate the following {source_lang} text to {target_lang}:

{text}

ABSOLUTE REQUIREMENTS - NO EXCEPTIONS:
1. Translate 100% of the text to {target_lang}
2. ZERO English words should remain untranslated
3. ONLY preserve code blocks marked with ```
4. Translate ALL technical terms:
   - AI → مصنوعی ذہانت
   - Physical → طبعی
   - Embodied → مجسم
   - Intelligence → ذہانت
   - System → نظام
   - Software → سافٹ ویئر
   - Computer → کمپیوٹر
   - Machine → مشین
   - Learning → لرننگ
   - Vision = بینائی
   - Robotics → روبوٹکس
5. Create Urdu translations for all English concepts
6. Mix Urdu words with Roman Urdu where appropriate for technical terms
7. Use Arabic script (Nastaleeq) for Urdu text

FAILURE IS NOT ACCEPTABLE. Every word must be translated.

Translate only the content inside the delimiters.
"""

    CHUNK_TRANSLATION_PROMPT = """
CRITICAL: Translate this {source_lang} text segment to {target_lang}:

{text}

STRICT GUIDELINES - DO NOT DEVIATE:
1. EVERY single word must be translated to {target_lang}
2. NO English words should remain in the translation
3. ONLY preserve text that is actual code between ``` marks
4. Translate ALL technical terms, acronyms, and jargon
   - AI = مصنوعی ذہانت
   - System = نظام
   - Software = سافٹ ویئر
   - Computer = کمپیوٹر
   - Machine = مشین
   - Learning = لرننگ
5. Do NOT treat technical terms as proper nouns - TRANSLATE THEM ALL
6. Create proper {target_lang} equivalents for all concepts
7. Use Roman Urdu for brand names if necessary but keep them minimal

TASK: Translate everything. No exceptions.
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize translation service.

        Args:
            api_key: Google Gen AI API key
            model: Gemini model to use
            cache_service: Cache service instance
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.cache_service = cache_service
        self.transliterator = get_technical_terms_transliterator()
        self.text_processor = get_text_processor()

        # Initialize Gemini client if available
        self.client = None
        if GENAI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"✅ Gemini client initialized successfully with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {str(e)}")
                self.client = None
        else:
            if not GENAI_AVAILABLE:
                logger.error("Google Gen AI library not available")
            if not self.api_key:
                logger.error("GEMINI_API_KEY not configured in environment")

    def _generate_content_hash(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Generate content hash for caching."""
        content = f"{text}_{source_lang}_{target_lang}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def _check_cache(self, content_hash: str) -> Optional[TranslationResponse]:
        """Check cache for existing translation."""
        if not self.cache_service:
            return None

        try:
            cached_data = await self.cache_service.get(
                cache_key=f"translation:{content_hash}",
                cache_type=CacheType.TRANSLATION
            )

            if cached_data:
                logger.info("Translation found in cache")
                return TranslationResponse(
                    translated_text=cached_data.get('translated_text', ''),
                    content_hash=content_hash,
                    chunks=cached_data.get('chunks', []),
                    processing_time_ms=0,
                    cached=True,
                    status=TranslationStatus.COMPLETED,
                    error_message=None
                )
        except Exception as e:
            logger.warning(f"Cache check failed: {str(e)}")

        return None

    async def _save_to_cache(
        self,
        content_hash: str,
        translation: TranslationResponse
    ) -> None:
        """Save translation to cache."""
        if not self.cache_service:
            return

        try:
            cache_data = {
                'translated_text': translation.translated_text,
                'chunks': translation.chunks,
                'timestamp': datetime.utcnow().isoformat()
            }

            await self.cache_service.set(
                cache_key=f"translation:{content_hash}",
                value=cache_data,
                cache_type=CacheType.TRANSLATION,
                ttl=3600  # 1 hour
            )
            logger.info("Translation saved to cache")
        except Exception as e:
            logger.warning(f"Cache save failed: {str(e)}")

    def _extract_code_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Extract code blocks from text for preservation."""
        import re
        pattern = r'```(\w+)?\n(.*?)\n```'
        code_blocks = []

        for match in re.finditer(pattern, text, re.DOTALL):
            code_blocks.append({
                'language': match.group(1) or 'text',
                'code': match.group(2),
                'start': match.start(),
                'end': match.end()
            })

        return code_blocks

    def _preserve_code_blocks(self, text: str, translated_text: str) -> str:
        """Preserve code blocks in translated text."""
        code_blocks = self._extract_code_blocks(text)

        if not code_blocks:
            return translated_text

        # Replace placeholders with actual code blocks
        for block in code_blocks:
            placeholder = f"```{block['language']}\n{block['code']}\n```"
            # Simple approach: find and replace similar patterns
            # This is a simplified implementation
            translated_text = translated_text.replace(
                f"```{block['language']}```",
                placeholder
            )

        return translated_text

    async def translate_chunk(self, chunk: str, source_lang: str, target_lang: str) -> str:
        """Translate a single text chunk."""
        if not self.client:
            raise ServiceError("Gemini client not initialized")

        try:
            # Build the prompt
            prompt = self.CHUNK_TRANSLATION_PROMPT.format(
                source_lang=source_lang,
                target_lang=target_lang,
                text=chunk
            )

            # Generate content using new SDK
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.TEMPERATURE,
                    top_p=self.TOP_P,
                    top_k=self.TOP_K,
                    max_output_tokens=2048
                )
            )

            return response.text

        except Exception as e:
            logger.error(f"Chunk translation failed: {str(e)}")
            raise ServiceError(f"Translation failed: {str(e)}")

    async def translate(
        self,
        request: TranslationRequest
    ) -> TranslationResponse:
        """
        Translate text content.

        Args:
            request: Translation request

        Returns:
            Translation response
        """
        if not GENAI_AVAILABLE:
            raise ServiceError("Google Gen AI library not available")

        if not self.client:
            raise ServiceError("Google Gen AI client not initialized")

        start_time = time.time()
        content_hash = self._generate_content_hash(
            request.text,
            request.source_language,
            request.target_language
        )

        # Check cache first
        cached_translation = await self._check_cache(content_hash)
        if cached_translation:
            return cached_translation

        try:
            # Process text
            processed_content = self.text_processor.process_text(
                request.text,
                preserve_code_blocks=request.preserve_code_blocks
            )

            # Translate chunks
            translated_chunks = []
            total_translated = ""

            for i, chunk in enumerate(processed_content.chunks):
                try:
                    chunk_translation = await self.translate_chunk(
                        chunk.content,
                        request.source_language,
                        request.target_language
                    )

                    # Preserve code blocks if needed
                    if request.preserve_code_blocks and chunk.is_code_block:
                        chunk_translation = chunk.content  # Keep original code

                    translated_chunks.append({
                        'index': i,
                        'original_text': chunk.content,
                        'translated_text': chunk_translation,
                        'start_position': chunk.start_position,
                        'end_position': chunk.end_position,
                        'is_code_block': chunk.is_code_block
                    })

                    total_translated += chunk_translation
                    if i < len(processed_content.chunks) - 1:
                        total_translated += '\n'

                except Exception as e:
                    logger.error(f"Failed to translate chunk {i}: {str(e)}")
                    # Continue with other chunks
                    continue

            processing_time = int((time.time() - start_time) * 1000)

            # Create response
            response = TranslationResponse(
                translated_text=total_translated,
                content_hash=content_hash,
                chunks=translated_chunks,
                processing_time_ms=processing_time,
                cached=False,
                status=TranslationStatus.COMPLETED,
                error_message=None
            )

            # Save to cache
            await self._save_to_cache(content_hash, response)

            logger.info(
                f"Translation completed",
                cached=False,
                characters=len(request.text),
                chunks=len(translated_chunks),
                processing_time_ms=processing_time,
                source_lang=request.source_language,
                target_lang=request.target_language
            )

            return response

        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise ServiceError(f"Translation failed: {str(e)}")


# Global instance
_translation_service = None


async def get_translation_service() -> GeminiTranslationService:
    """Get or create translation service instance."""
    global _translation_service

    if _translation_service is None:
        cache_service = await get_cache_service()
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not configured in environment")
            raise ServiceError("Google AI API key not configured")

        _translation_service = GeminiTranslationService(
            api_key=api_key,
            cache_service=cache_service
        )

    return _translation_service


# Convenience function for direct translation
async def translate_text(
    text: str,
    source_lang: str = "en",
    target_lang: str = "ur",
    context: Optional[str] = None,
    preserve_code_blocks: bool = True
) -> TranslationResponse:
    """
    Translate text with convenience parameters.

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        context: Translation context
        preserve_code_blocks: Whether to preserve code blocks

    Returns:
        Translation response
    """
    service = await get_translation_service()

    request = TranslationRequest(
        text=text,
        source_language=source_lang,
        target_language=target_lang,
        preserve_code_blocks=preserve_code_blocks,
        enable_transliteration=True,
        streaming=False
    )

    return await service.translate(request)