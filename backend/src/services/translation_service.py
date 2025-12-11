"""
Translation service with Google Gen AI integration.

Provides translation services using Google Gemini LLM with caching,
technical terms handling, and code block preservation.
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
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
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
    Translation service using Google Gemini API.

    Features:
    - Gemini LLM integration for high-quality translations
    - Content chunking for large texts
    - Code block preservation
    - Technical terms transliteration
    - Caching for performance
    - Streaming support
    - Error handling and retries
    """

    # Gemini model configuration
    DEFAULT_MODEL = "models/gemini-2.5-flash"
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

    # Safety settings - Note: New SDK handles safety differently
    # Safety is configured through the types.GenerateContentConfig if needed

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize translation service.

        Args:
            api_key: Google Generative AI API key
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
        if GEMINI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini client initialized successfully with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {str(e)}")
                self.client = None

        if not self.client:
            logger.error("Gemini client not initialized, translation service will not work")

    def _generate_content_hash(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate hash for caching purposes."""
        content = f"{text}:{source_lang}:{target_lang}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def _check_cache(self, content_hash: str) -> Optional[Translation]:
        """Check if translation is cached."""
        if not self.cache_service:
            return None

        try:
            cache_key = f"translation:{content_hash}"
            cached_data = await self.cache_service.get(cache_key, CacheType.TRANSLATION)

            if cached_data:
                # Convert cached data back to Translation object
                translation = Translation(**cached_data)
                logger.info("Translation found in cache", hash=content_hash[:8])
                return translation

        except Exception as e:
            logger.warning("Cache check failed", error=str(e))

        return None

    async def _cache_translation(self, content_hash: str, translation: Translation) -> bool:
        """Cache a translation."""
        if not self.cache_service:
            return False

        try:
            cache_key = f"translation:{content_hash}"
            # Convert to dict for caching
            translation_data = {
                "id": translation.id,
                "content_hash": translation.content_hash,
                "source_language": translation.source_language,
                "target_language": translation.target_language,
                "original_text": translation.original_text,
                "translated_text": translation.translated_text,
                "created_at": translation.created_at.isoformat(),
                "updated_at": translation.updated_at.isoformat(),
                "translation_model": translation.translation_model,
                "character_count": translation.character_count,
            }

            success = await self.cache_service.set(
                cache_key,
                translation_data,
                CacheType.TRANSLATION
            )

            if success:
                logger.info("Translation cached successfully", hash=content_hash[:8])

            return success

        except Exception as e:
            logger.warning("Cache save failed", error=str(e))
            return False

    async def _translate_with_gemini(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        is_chunk: bool = False
    ) -> str:
        """
        Translate text using Gemini.

        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            is_chunk: Whether this is a chunk translation

        Returns:
            Translated text
        """
        if not self.client:
            raise ServiceError("Gemini model not available")

        try:
            # Select appropriate prompt
            if is_chunk:
                prompt = self.CHUNK_TRANSLATION_PROMPT.format(
                    source_lang=source_lang,
                    target_lang=target_lang,
                    text=text
                )
            else:
                prompt = self.TRANSLATION_PROMPT_TEMPLATE.format(
                    source_lang=source_lang,
                    target_lang=target_lang,
                    text=text
                )

            # Generate translation using new SDK
            if not self.client:
                raise ServiceError("Gemini client not initialized")

            try:
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

                # Extract translated text
                if response.text:
                    return response.text.strip()
                else:
                    raise ServiceError("Empty translation response")

            except Exception as e:
                logger.error(f"Gemini API error: {str(e)}")
                raise ServiceError(f"Translation failed: {str(e)}")

        except Exception as e:
            log_exception(e, "Gemini translation failed")
            raise ServiceError(f"Translation failed: {str(e)}")

    async def _translate_chunk_sequence(
        self,
        chunks: List[ContentChunk],
        source_lang: str,
        target_lang: str,
        enable_transliteration: bool
    ) -> List[TranslationChunk]:
        """
        Translate a sequence of chunks.

        Args:
            chunks: Content chunks to translate
            source_lang: Source language
            target_lang: Target language
            enable_transliteration: Whether to enable technical terms transliteration

        Returns:
            List of translated chunks
        """
        translated_chunks = []

        for chunk in chunks:
            try:
                if chunk.is_code_block:
                    # Skip code blocks
                    translated_chunks.append(TranslationChunk(
                        index=chunk.index,
                        original_text=chunk.content,
                        translated_text=chunk.content,
                        start_position=chunk.start_position,
                        end_position=chunk.end_position,
                        is_code_block=True,
                        language=chunk.language
                    ))
                else:
                    # Translate chunk
                    translated_text = await self._translate_with_gemini(
                        chunk.content,
                        source_lang,
                        target_lang,
                        is_chunk=True
                    )

                    # Apply transliteration if enabled
                    if enable_transliteration:
                        translated_text = self.transliterator.transliterate_text(
                            translated_text,
                            target_format=target_lang,
                            preserve_code_blocks=True
                        )

                    translated_chunks.append(TranslationChunk(
                        index=chunk.index,
                        original_text=chunk.content,
                        translated_text=translated_text,
                        start_position=chunk.start_position,
                        end_position=chunk.end_position,
                        is_code_block=False
                    ))

            except Exception as e:
                logger.error(
                    "Chunk translation failed",
                    chunk_index=chunk.index,
                    error=str(e)
                )
                # Use original text as fallback
                translated_chunks.append(TranslationChunk(
                    index=chunk.index,
                    original_text=chunk.content,
                    translated_text=chunk.content,
                    start_position=chunk.start_position,
                    end_position=chunk.end_position,
                    is_code_block=chunk.is_code_block
                ))

        return translated_chunks

    async def translate(
        self,
        request: TranslationRequest
    ) -> TranslationResponse:
        print(f"*** TRANSLATION SERVICE CALLED: '{request.text[:50]}...' from {request.source_language} to {request.target_language}")
        logger.info(f"Translation service called with text: '{request.text[:50]}...', from {request.source_language} to {request.target_language}")
        """
        Translate text content.

        Args:
            request: Translation request

        Returns:
            Translation response
        """
        if not GEMINI_AVAILABLE:
            raise ServiceError("Google Generative AI library not available")

        if not self.api_key:
            raise ServiceError("Google AI API key not configured")

        start_time = time.time()
        content_hash = self._generate_content_hash(
            request.text,
            request.source_language,
            request.target_language
        )

        # Check cache first
        cached_translation = await self._check_cache(content_hash)
        if cached_translation:
            # Convert chunks to response format
            chunks = [
                {
                    "index": i,
                    "original_text": chunk,
                    "translated_text": chunk,
                    "start_position": 0,
                    "end_position": len(chunk),
                    "is_code_block": False
                }
                for i, chunk in enumerate(cached_translation.translated_text.split('\n\n'))
            ]

            return TranslationResponse(
                translated_text=cached_translation.translated_text,
                content_hash=content_hash,
                chunks=chunks,
                processing_time_ms=int((time.time() - start_time) * 1000),
                cached=True,
                status=TranslationStatus.COMPLETED
            )

        try:
            # Process content into chunks
            processed_content = self.text_processor.process(request.text)

            # Prepare chunks for translation
            translation_chunks = []
            for chunk in processed_content.chunks:
                translation_chunks.append(TranslationChunk(
                    index=chunk.index,
                    original_text=chunk.content,
                    translated_text="",  # Will be filled
                    start_position=chunk.start_position,
                    end_position=chunk.end_position,
                    is_code_block=chunk.is_code_block,
                    language=chunk.language
                ))

            # Translate chunks
            translated_chunks = await self._translate_chunk_sequence(
                processed_content.chunks,
                request.source_language,
                request.target_language,
                request.enable_transliteration
            )

            # Reconstruct translated text
            translated_text = ''.join(chunk.translated_text for chunk in translated_chunks)
            logger.info(f"Translation complete. Original: '{request.text[:50]}...' Translated: '{translated_text[:50]}...'")

            # Convert chunks to response format
            response_chunks = [
                {
                    "index": chunk.index,
                    "original_text": chunk.original_text,
                    "translated_text": chunk.translated_text,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position,
                    "is_code_block": chunk.is_code_block
                }
                for chunk in translated_chunks
            ]

            # Create translation record
            translation = Translation(
                content_hash=content_hash,
                source_language=request.source_language,
                target_language=request.target_language,
                original_text=request.text,
                translated_text=translated_text,
                translation_model=self.model,
                character_count=len(request.text)
            )

            # Cache the translation
            await self._cache_translation(content_hash, translation)

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                "Translation completed",
                source_lang=request.source_language,
                target_lang=request.target_language,
                characters=len(request.text),
                chunks=len(translated_chunks),
                processing_time_ms=processing_time,
                cached=False
            )

            return TranslationResponse(
                translated_text=translated_text,
                content_hash=content_hash,
                chunks=response_chunks,
                processing_time_ms=processing_time,
                cached=False,
                status=TranslationStatus.COMPLETED
            )

        except Exception as e:
            log_exception(e, "Translation failed")
            return TranslationResponse(
                translated_text="",
                content_hash=content_hash,
                chunks=[],
                processing_time_ms=int((time.time() - start_time) * 1000),
                cached=False,
                status=TranslationStatus.FAILED,
                error_message=str(e)
            )

    async def translate_streaming(
        self,
        request: TranslationRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Translate text with streaming response.

        Args:
            request: Translation request

        Yields:
            Streaming translation updates
        """
        if not GEMINI_AVAILABLE:
            raise ServiceError("Google Generative AI library not available")

        if not self.api_key:
            raise ServiceError("Google AI API key not configured")

        start_time = time.time()
        content_hash = self._generate_content_hash(
            request.text,
            request.source_language,
            request.target_language
        )

        # Check cache first
        cached_translation = await self._check_cache(content_hash)
        if cached_translation:
            yield {
                "type": "complete",
                "translated_text": cached_translation.translated_text,
                "content_hash": content_hash,
                "cached": True,
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
            return

        yield {
            "type": "start",
            "content_hash": content_hash,
            "message": "Starting translation..."
        }

        try:
            # Process content into chunks
            processed_content = self.text_processor.process(request.text)
            total_chunks = len(processed_content.chunks)

            # Translate chunks one by one
            translated_chunks = []
            for i, chunk in enumerate(processed_content.chunks):
                yield {
                    "type": "progress",
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "message": f"Translating chunk {i + 1} of {total_chunks}..."
                }

                if chunk.is_code_block and request.preserve_code_blocks:
                    translated_text = chunk.content
                else:
                    translated_text = await self._translate_with_gemini(
                        chunk.content,
                        request.source_language,
                        request.target_language,
                        is_chunk=True
                    )

                    # Apply transliteration if enabled
                    if request.enable_transliteration:
                        translated_text = self.transliterator.transliterate_text(
                            translated_text,
                            target_format=request.target_language,
                            preserve_code_blocks=True
                        )

                translated_chunks.append({
                    "index": i,
                    "translated_text": translated_text,
                    "is_code_block": chunk.is_code_block
                })

                yield {
                    "type": "chunk",
                    "chunk_index": i,
                    "translated_text": translated_text,
                    "is_code_block": chunk.is_code_block
                }

            # Reconstruct final text
            final_text = ''.join(chunk["translated_text"] for chunk in translated_chunks)

            # Cache the result
            translation = Translation(
                content_hash=content_hash,
                source_language=request.source_language,
                target_language=request.target_language,
                original_text=request.text,
                translated_text=final_text,
                translation_model=self.model,
                character_count=len(request.text)
            )
            await self._cache_translation(content_hash, translation)

            processing_time = int((time.time() - start_time) * 1000)

            yield {
                "type": "complete",
                "translated_text": final_text,
                "content_hash": content_hash,
                "chunks": translated_chunks,
                "processing_time_ms": processing_time,
                "cached": False
            }

        except Exception as e:
            log_exception(e, "Streaming translation failed")
            yield {
                "type": "error",
                "error": str(e),
                "content_hash": content_hash
            }

    async def submit_feedback(
        self,
        translation_id: int,
        user_id: str,
        rating: int,
        comment: Optional[str] = None
    ) -> bool:
        """
        Submit feedback for a translation.

        Args:
            translation_id: Translation ID
            user_id: User ID
            rating: Rating (-1 or 1)
            comment: Optional comment

        Returns:
            True if feedback submitted successfully
        """
        if rating not in [-1, 1]:
            raise ValidationError("Rating must be -1 or 1")

        try:
            # Create feedback record
            feedback = TranslationFeedback(
                translation_id=translation_id,
                user_id=user_id,
                rating=rating,
                comment=comment
            )

            # Save to database
            db = next(get_db())
            try:
                db.add(feedback)
                db.commit()
                logger.info(
                    "Translation feedback submitted",
                    translation_id=translation_id,
                    user_id=user_id,
                    rating=rating
                )
                return True
            finally:
                db.close()

        except Exception as e:
            log_exception(e, "Failed to submit feedback")
            raise ServiceError(f"Failed to submit feedback: {str(e)}")


# Global translation service instance
_translation_service: Optional[GeminiTranslationService] = None


async def get_translation_service() -> GeminiTranslationService:
    """Get or create translation service instance."""
    global _translation_service

    if _translation_service is None:
        print("*** Creating translation service instance ***")
        cache_service = await get_cache_service()
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"*** API key found: {bool(api_key)} ***")
        if not api_key:
            logger.error("GEMINI_API_KEY not configured in environment")
            raise ServiceError("Google AI API key not configured")

        _translation_service = GeminiTranslationService(
            api_key=api_key,
            cache_service=cache_service
        )

    return _translation_service