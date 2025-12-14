"""
OpenAI Translation Service using Gemini API.

This service implements the core translation functionality using
OpenAI Agents SDK with Gemini's OpenAI-compatible endpoint.
"""

import asyncio
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from src.models.translation_openai import (
    TranslationJob, TranslationChunk, TranslationError, TranslationSession,
    TranslationCache, TranslationJobStatus, ChunkStatus, ErrorSeverity
)
from src.services.openai_translation.client import GeminiOpenAIClient, get_gemini_client
from src.services.cache_service import CacheService, get_cache_service
from src.database.base import get_db
from src.utils.translation_errors import (
    TranslationError as TranslationServiceError, APIError, RateLimitError,
    with_translation_error_handling, retry_with_exponential_backoff
)
from src.utils.translation_logger import get_translation_logger, log_translation_performance

logger = get_translation_logger(__name__)


@dataclass
class OpenAITranslationRequest:
    """Translation request with comprehensive parameters."""
    text: str
    source_language: str
    target_language: str
    page_url: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # OpenAI parameters
    model: str = "gemini-2.0-flash-lite"
    temperature: float = 0.3
    max_tokens: int = 2048

    # Processing options
    preserve_code_blocks: bool = True
    enable_transliteration: bool = True
    chunk_size: int = 2000
    max_chunks: int = 100

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    # Streaming
    streaming: bool = False

    # Session context
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class OpenAITranslationResponse:
    """Translation response with comprehensive metadata."""
    job_id: str
    translated_text: str
    status: TranslationJobStatus
    progress: float  # 0-100
    chunks: List[Dict[str, Any]]
    processing_time_ms: int
    cached: bool

    # Cost tracking
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float

    # Quality metrics
    confidence_score: Optional[float] = None
    quality_score: Optional[float] = None

    # Error information
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # Cache information
    cache_key: Optional[str] = None
    cache_hit: bool = False


class OpenAITranslationService:
    """
    Translation service using OpenAI Agents SDK with Gemini API.

    Features:
    - OpenAI Agents SDK with Gemini 2.0 Flash model
    - Content chunking for large texts
    - Enhanced caching with page URL support
    - Progress tracking and streaming
    - Error handling and retries
    - Session management
    - Cost and quality tracking
    """

    # Translation prompt templates
    TRANSLATION_PROMPT_TEMPLATE = """
You are a professional translator. Translate the following text from {source_lang} to {target_lang}.

CRITICAL REQUIREMENTS:
1. Translate ALL text to {target_lang} - no English words should remain
2. ONLY preserve code blocks marked with ```
3. Translate technical terms with context (e.g., AI → مصنوعی ذہانت)
4. Use Urdu script (Nastaleeq) for Urdu text
5. Maintain formatting and structure
6. Mix Urdu with Roman Urdu for technical terms where appropriate

Text to translate:
{text}

Translate only the content above.
"""

    CHUNK_TRANSLATION_PROMPT = """
Translate this text segment from {source_lang} to {target_lang}.

Context: This is part {current_part} of {total_parts} of a larger document.

Requirements:
- Maintain consistency with the overall document
- Translate accurately while preserving meaning
- Handle technical terms appropriately
- Keep the flow natural
- Use Urdu script (Nastaleeq)

Text:
{text}

Translation:
"""

    # Model pricing (approximate USD per 1K tokens)
    MODEL_PRICING = {
        "gemini-2.0-flash-lite": {
            "input": 0.000075,  # $0.075 per 1M input tokens
            "output": 0.00015   # $0.15 per 1M output tokens
        }
    }

    def __init__(
        self,
        gemini_client: Optional[GeminiOpenAIClient] = None,
        cache_service: Optional[CacheService] = None,
        enable_analytics: bool = True
    ):
        """
        Initialize OpenAI translation service.

        Args:
            gemini_client: Gemini OpenAI client
            cache_service: Cache service instance
            enable_analytics: Whether to collect detailed analytics
        """
        self.gemini_client = gemini_client
        self.cache_service = cache_service
        self.enable_analytics = enable_analytics

        # Initialize services if not provided
        if not self.gemini_client:
            self.gemini_client = get_gemini_client()

        if not self.cache_service:
            self.cache_service = get_cache_service()

        logger.info(
            "OpenAI Translation Service initialized",
            model="gemini-2.0-flash-lite",
            analytics_enabled=enable_analytics
        )

    def _generate_content_hash(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate SHA-256 hash for content identification."""
        content = f"{text}:{source_lang}:{target_lang}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _generate_cache_key(self, content_hash: str, page_url: Optional[str] = None) -> str:
        """Generate comprehensive cache key including page URL."""
        if page_url:
            url_hash = hashlib.sha256(page_url.encode('utf-8')).hexdigest()[:16]
            return f"openai_translation:{content_hash}:{url_hash}"
        return f"openai_translation:{content_hash}"

    async def _check_cache(
        self,
        content_hash: str,
        page_url: Optional[str] = None
    ) -> Optional[TranslationCache]:
        """Check if translation is cached in database."""
        cache_key = self._generate_cache_key(content_hash, page_url)

        db = next(get_db())
        try:
            cache_entry = db.query(TranslationCache).filter(
                TranslationCache.cache_key == cache_key,
                TranslationCache.expires_at > datetime.utcnow()
            ).first()

            if cache_entry:
                # Update hit statistics
                cache_entry.hit_count += 1
                cache_entry.last_hit_at = datetime.utcnow()
                db.commit()
                logger.info(
                    "Cache hit found",
                    cache_key=cache_key[:20],
                    hits=cache_entry.hit_count
                )
                return cache_entry

        finally:
            db.close()

        return None

    async def _cache_translation(
        self,
        job: TranslationJob,
        cache_key: str,
        quality_score: Optional[float] = None
    ) -> bool:
        """Cache a successful translation."""
        try:
            db = next(get_db())

            # Determine TTL based on quality
            if quality_score and quality_score >= 4.5:
                ttl_hours = 30 * 24  # 30 days for high quality
            elif quality_score and quality_score < 3.0:
                ttl_hours = 24  # 1 day for low quality
            else:
                ttl_hours = 7 * 24  # 7 days default

            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

            cache_entry = TranslationCache(
                cache_key=cache_key,
                job_id=job.id,
                content_hash=job.content_hash,
                page_url=job.page_url,
                source_language=job.source_language,
                target_language=job.target_language,
                original_text=job.original_text,
                translated_text=job.translated_text,
                model_version=job.model_name,
                processing_time_ms=job.processing_time_ms,
                ttl_hours=ttl_hours,
                expires_at=expires_at,
                quality_score=quality_score,
                is_validated=quality_score is not None
            )

            db.add(cache_entry)
            db.commit()

            logger.info(
                "Translation cached",
                cache_key=cache_key[:20],
                ttl_hours=ttl_hours
            )
            return True

        except Exception as e:
            logger.error("Failed to cache translation", error=str(e))
            return False
        finally:
            db.close()

    async def _translate_with_gemini(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        model: str,
        temperature: float,
        max_tokens: int,
        is_chunk: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Translate text using Gemini via OpenAI SDK.

        Returns:
            Dict containing translated_text, tokens_used, and response metadata
        """
        client = self.gemini_client.get_client()

        try:
            # Select appropriate prompt
            if is_chunk and context:
                prompt = self.CHUNK_TRANSLATION_PROMPT.format(
                    source_lang=source_lang,
                    target_lang=target_lang,
                    current_part=context.get('current_part', 1),
                    total_parts=context.get('total_parts', 1),
                    text=text
                )
            else:
                prompt = self.TRANSLATION_PROMPT_TEMPLATE.format(
                    source_lang=source_lang,
                    target_lang=target_lang,
                    text=text
                )

            # Call Gemini API via OpenAI SDK
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract translation and metrics
            translated_text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            # Calculate cost
            pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING["gemini-2.0-flash-lite"])
            estimated_cost = (
                (input_tokens / 1000 * pricing["input"]) +
                (output_tokens / 1000 * pricing["output"])
            )

            return {
                "translated_text": translated_text.strip() if translated_text else "",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost": estimated_cost,
                "model": model,
                "response_id": response.id
            }

        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            raise TranslationServiceError(
                f"Translation failed: {str(e)}",
                error_type="API_ERROR",
                is_retriable=True
            )

    def _split_text_into_chunks(
        self,
        text: str,
        chunk_size: int,
        max_chunks: int,
        preserve_code_blocks: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks for processing.

        Returns:
            List of chunks with text, position, and metadata
        """
        chunks = []

        if preserve_code_blocks:
            # Handle code blocks separately
            import re
            code_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)

            last_end = 0
            chunk_index = 0

            for match in code_pattern.finditer(text):
                # Process text before code block
                text_before = text[last_end:match.start()]
                if text_before:
                    text_chunks = self._split_plain_text(text_before, chunk_size - 200)
                    for chunk_text in text_chunks:
                        if chunk_index >= max_chunks:
                            break
                        chunks.append({
                            "text": chunk_text,
                            "start": last_end,
                            "end": last_end + len(chunk_text),
                            "is_code_block": False,
                            "index": chunk_index
                        })
                        chunk_index += 1
                        last_end += len(chunk_text)

                # Add code block as separate chunk
                if chunk_index < max_chunks:
                    code_lang = match.group(1) or "unknown"
                    code_content = match.group(2)
                    full_code = f"```{code_lang}\n{code_content}\n```"
                    chunks.append({
                        "text": full_code,
                        "start": match.start(),
                        "end": match.end(),
                        "is_code_block": True,
                        "code_language": code_lang,
                        "index": chunk_index
                    })
                    chunk_index += 1
                    last_end = match.end()

            # Process remaining text
            if last_end < len(text) and chunk_index < max_chunks:
                remaining_text = text[last_end:]
                text_chunks = self._split_plain_text(remaining_text, chunk_size)
                for chunk_text in text_chunks:
                    if chunk_index >= max_chunks:
                        break
                    chunks.append({
                        "text": chunk_text,
                        "start": last_end,
                        "end": last_end + len(chunk_text),
                        "is_code_block": False,
                        "index": chunk_index
                    })
                    chunk_index += 1
                    last_end += len(chunk_text)
        else:
            # Simple text splitting
            text_chunks = self._split_plain_text(text, chunk_size)
            chunks = [
                {
                    "text": chunk,
                    "start": i * chunk_size,
                    "end": (i + 1) * chunk_size,
                    "is_code_block": False,
                    "index": i
                }
                for i, chunk in enumerate(text_chunks[:max_chunks])
            ]

        return chunks

    def _split_plain_text(self, text: str, chunk_size: int) -> List[str]:
        """Split plain text into chunks, trying to preserve sentences."""
        import re

        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @log_translation_performance
    async def translate(
        self,
        request: OpenAITranslationRequest
    ) -> OpenAITranslationResponse:
        """
        Translate text with comprehensive tracking and caching.

        Args:
            request: Translation request with all parameters

        Returns:
            Translation response with metadata
        """
        start_time = time.time()
        job_id = str(uuid.uuid4())
        content_hash = self._generate_content_hash(
            request.text,
            request.source_language,
            request.target_language
        )
        cache_key = self._generate_cache_key(content_hash, request.page_url)

        logger.bind_request(request_id=job_id).log_translation_request(
            text_length=len(request.text),
            source_lang=request.source_language,
            target_lang=request.target_language,
            page_url=request.page_url
        )

        # Check cache first
        cached_translation = await self._check_cache(content_hash, request.page_url)
        if cached_translation:
            processing_time = int((time.time() - start_time) * 1000)

            logger.log_translation_response(
                translated_length=len(cached_translation.translated_text),
                chunks_count=1,
                cached=True
            )

            return OpenAITranslationResponse(
                job_id=job_id,
                translated_text=cached_translation.translated_text,
                status=TranslationJobStatus.COMPLETED,
                progress=100.0,
                chunks=[],
                processing_time_ms=processing_time,
                cached=True,
                input_tokens=0,
                output_tokens=0,
                estimated_cost_usd=0.0,
                cache_key=cache_key,
                cache_hit=True
            )

        # Create translation job
        db = next(get_db())
        try:
            job = TranslationJob(
                job_id=job_id,
                user_id=request.user_id,
                session_id=request.session_id,
                content_hash=content_hash,
                page_url=request.page_url,
                source_language=request.source_language,
                target_language=request.target_language,
                original_text=request.text,
                model_name=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                preserve_code_blocks=request.preserve_code_blocks,
                enable_transliteration=request.enable_transliteration,
                chunk_size=request.chunk_size,
                max_chunks=request.max_chunks,
                user_agent=request.user_agent,
                ip_address=request.ip_address
            )

            db.add(job)
            db.commit()

            # Split text into chunks
            chunks_data = self._split_text_into_chunks(
                request.text,
                request.chunk_size,
                request.max_chunks,
                request.preserve_code_blocks
            )

            job.chunks_total = len(chunks_data)
            job.status = TranslationJobStatus.PROCESSING.value
            job.started_at = datetime.utcnow()
            db.commit()

            # Process chunks
            translated_chunks = []
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0.0

            for i, chunk_data in enumerate(chunks_data):
                try:
                    # Create chunk record
                    chunk = TranslationChunk(
                        job_id=job.id,
                        chunk_index=i,
                        original_text=chunk_data["text"],
                        start_position=chunk_data["start"],
                        end_position=chunk_data["end"],
                        is_code_block=chunk_data["is_code_block"],
                        code_language=chunk_data.get("code_language"),
                        word_count=len(chunk_data["text"].split()),
                        status=ChunkStatus.PROCESSING.value,
                        started_at=datetime.utcnow()
                    )
                    db.add(chunk)
                    db.commit()

                    # Translate or skip code blocks
                    if chunk_data["is_code_block"] and request.preserve_code_blocks:
                        translated_text = chunk_data["text"]
                        chunk.status = ChunkStatus.COMPLETED.value
                        chunk.translated_text = translated_text
                        chunk.completed_at = datetime.utcnow()
                    else:
                        # Translate chunk with retry logic
                        async def translate_chunk():
                            return await self._translate_with_gemini(
                                chunk_data["text"],
                                request.source_language,
                                request.target_language,
                                request.model,
                                request.temperature,
                                request.max_tokens,
                                is_chunk=True,
                                context={
                                    "current_part": i + 1,
                                    "total_parts": len(chunks_data)
                                } if len(chunks_data) > 1 else None
                            )

                        result = await retry_with_exponential_backoff(
                            translate_chunk,
                            max_retries=request.max_retries
                        )

                        translated_text = result["translated_text"]
                        chunk.translated_text = translated_text
                        chunk.input_tokens = result["input_tokens"]
                        chunk.output_tokens = result["output_tokens"]
                        chunk.status = ChunkStatus.COMPLETED.value
                        chunk.completed_at = datetime.utcnow()

                        total_input_tokens += result["input_tokens"]
                        total_output_tokens += result["output_tokens"]
                        total_cost += result["estimated_cost"]

                    # Update job progress
                    job.chunks_completed += 1
                    job.progress_percentage = (job.chunks_completed / job.chunks_total) * 100
                    db.commit()

                    # Add to response chunks
                    translated_chunks.append({
                        "index": i,
                        "original_text": chunk_data["text"],
                        "translated_text": translated_text,
                        "start_position": chunk_data["start"],
                        "end_position": chunk_data["end"],
                        "is_code_block": chunk_data["is_code_block"],
                        "code_language": chunk_data.get("code_language")
                    })

                except Exception as e:
                    # Handle chunk error
                    chunk.status = ChunkStatus.FAILED.value
                    chunk.last_error = str(e)
                    job.chunks_failed += 1

                    # Log error
                    logger.log_error(e, chunk_index=i)

                    db.commit()
                    logger.error(f"Chunk {i} translation failed", error=str(e))

            # Reconstruct final translation
            final_translation = ''.join(chunk["translated_text"] for chunk in translated_chunks)

            # Update job completion
            job.translated_text = final_translation
            job.input_tokens = total_input_tokens
            job.output_tokens = total_output_tokens
            job.estimated_cost_usd = total_cost
            job.status = (
                TranslationJobStatus.COMPLETED.value
                if job.chunks_failed == 0
                else TranslationJobStatus.FAILED.value
            )
            job.completed_at = datetime.utcnow()
            job.processing_time_ms = int((time.time() - start_time) * 1000)
            job.progress_percentage = 100.0
            db.commit()

            # Cache successful translation
            if job.chunks_failed == 0:
                await self._cache_translation(job, cache_key)

            processing_time = int((time.time() - start_time) * 1000)

            logger.log_translation_response(
                translated_length=len(final_translation),
                chunks_count=len(translated_chunks),
                tokens_used=total_input_tokens + total_output_tokens,
                cost_usd=total_cost,
                cached=False
            )

            logger.info(
                "Translation completed",
                job_id=job_id,
                chunks=len(chunks_data),
                failed=job.chunks_failed,
                processing_time_ms=processing_time,
                total_cost=total_cost
            )

            return OpenAITranslationResponse(
                job_id=job_id,
                translated_text=final_translation,
                status=TranslationJobStatus(job.status),
                progress=100.0,
                chunks=translated_chunks,
                processing_time_ms=processing_time,
                cached=False,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                estimated_cost_usd=total_cost,
                cache_key=cache_key,
                cache_hit=False,
                error_message=(
                    f"{job.chunks_failed} chunks failed"
                    if job.chunks_failed > 0
                    else None
                )
            )

        except Exception as e:
            # Update job status to failed
            if 'job' in locals():
                job.status = TranslationJobStatus.FAILED.value
                job.completed_at = datetime.utcnow()
                db.commit()

            logger.log_error(e, job_id=job_id)
            raise TranslationServiceError(
                f"Translation failed: {str(e)}",
                error_type="SYSTEM_ERROR"
            )

        finally:
            db.close()

    async def get_translation_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a translation job."""
        db = next(get_db())
        try:
            job = db.query(TranslationJob).filter(
                TranslationJob.job_id == job_id
            ).first()

            if not job:
                raise TranslationServiceError(
                    "Translation job not found",
                    error_type="VALIDATION_ERROR"
                )

            return {
                "job_id": job.job_id,
                "status": job.status,
                "progress": float(job.progress_percentage),
                "chunks_total": job.chunks_total,
                "chunks_completed": job.chunks_completed,
                "chunks_failed": job.chunks_failed,
                "processing_time_ms": job.processing_time_ms,
                "estimated_cost_usd": float(job.estimated_cost_usd),
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }

        finally:
            db.close()

    async def stream_translation_status(self, job_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream translation status updates."""
        # Implementation for streaming status updates
        # This would typically check status periodically and yield updates
        yield {"type": "start", "job_id": job_id, "message": "Starting stream..."}

        # In a real implementation, you would:
        # 1. Get initial job status
        # 2. Poll status changes
        # 3. Yield updates as they occur
        # 4. Close stream when job completes

    async def check_cache(self, content_hash: str, page_url: Optional[str] = None) -> Optional[TranslationCache]:
        """Check cache for translation."""
        return await self._check_cache(content_hash, page_url)

    def generate_cache_key(self, content_hash: str, page_url: Optional[str] = None) -> str:
        """Generate cache key."""
        return self._generate_cache_key(content_hash, page_url)

    async def clear_cache(self, page_url: Optional[str] = None, older_than_hours: Optional[int] = None) -> int:
        """Clear translation cache entries."""
        db = next(get_db())
        try:
            query = db.query(TranslationCache)

            if page_url:
                query = query.filter(TranslationCache.page_url == page_url)

            if older_than_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
                query = query.filter(TranslationCache.created_at < cutoff_time)

            # Get count before deleting
            count = query.count()

            # Delete entries
            query.delete()
            db.commit()

            logger.info(
                "Cache cleared",
                entries_deleted=count,
                page_url=page_url,
                older_than_hours=older_than_hours
            )

            return count

        finally:
            db.close()

    async def health_check(self) -> bool:
        """Check if the service is healthy."""
        try:
            # Test Gemini connection
            await self.gemini_client.test_connection()
            return True
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False

    async def get_metrics(self, period: str = "24h") -> Dict[str, Any]:
        """Get translation metrics."""
        # Implementation would aggregate metrics from database
        # This is a placeholder
        return {
            "period": period,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hit_rate": 0.0,
            "avg_processing_time_ms": 0.0,
            "total_cost_usd": 0.0
        }


# Global service instance
_translation_service: Optional[OpenAITranslationService] = None


async def get_translation_service() -> OpenAITranslationService:
    """Get or create OpenAI translation service instance."""
    global _translation_service

    if _translation_service is None:
        _translation_service = OpenAITranslationService()
        # Initialize the async client
        _translation_service.gemini_client = get_gemini_client()

    return _translation_service