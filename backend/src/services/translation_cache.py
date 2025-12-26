"""
Translation Cache Service

Provides caching functionality for translations with 1-week expiry.
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_

from src.models.translation_openai import TranslationCache
from src.core.database import AsyncSessionLocal


class TranslationCacheService:
    """Service for managing translation cache with 1-week expiry."""

    def __init__(self):
        self.default_ttl_hours = 168  # 7 days

    def _generate_cache_key(
        self,
        text: str,
        source_language: str,
        target_language: str,
        page_url: Optional[str] = None
    ) -> str:
        """Generate a unique cache key for the translation request."""
        # Create a hash of the text and parameters
        key_data = f"{text}|{source_language}|{target_language}"
        if page_url:
            key_data += f"|{page_url}"

        # Use SHA-256 for consistent hashing
        hash_object = hashlib.sha256(key_data.encode('utf-8'))
        return hash_object.hexdigest()

    def _generate_content_hash(self, text: str) -> str:
        """Generate a hash of the content for lookup."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _generate_url_hash(self, page_url: str) -> str:
        """Generate a hash of the URL for privacy."""
        return hashlib.sha256(page_url.encode('utf-8')).hexdigest()

    async def get_cached_translation(
        self,
        text: str,
        source_language: str,
        target_language: str,
        page_url: Optional[str] = None,
        db: AsyncSession = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached translation if available and not expired.

        Args:
            text: Original text to translate
            source_language: Source language code (e.g., 'en')
            target_language: Target language code (e.g., 'ur')
            page_url: Optional page URL for context
            db: Database session

        Returns:
            Cached translation data or None if not found/expired
        """
        async with AsyncSessionLocal() as session:
            # Generate cache key
            cache_key = self._generate_cache_key(text, source_language, target_language, page_url)
            content_hash = self._generate_content_hash(text)

            # Try to find exact match first
            query = select(TranslationCache).where(
                and_(
                    TranslationCache.cache_key == cache_key,
                    TranslationCache.expires_at > datetime.utcnow(),
                    TranslationCache.source_language == source_language,
                    TranslationCache.target_language == target_language
                )
            )

            result = await session.execute(query)
            result = result.scalar_one_or_none()

            if result:
                # Update hit count and last hit timestamp
                update_query = update(TranslationCache).where(
                    TranslationCache.id == result.id
                ).values(
                    hit_count=TranslationCache.hit_count + 1,
                    last_hit_at=datetime.utcnow()
                )
                await session.execute(update_query)
                await session.commit()

                return {
                    "translated_text": result.translated_text,
                    "original_text": result.original_text,
                    "cached": True,
                    "cache_created_at": result.created_at.isoformat(),
                    "cache_expires_at": result.expires_at.isoformat(),
                    "hit_count": result.hit_count + 1,
                    "model": result.model_version,
                    "confidence_score": float(result.quality_score) if result.quality_score else 0.95
                }

            # Try to find match by content hash if page URL is provided
            if page_url:
                url_hash = self._generate_url_hash(page_url)
                query = select(TranslationCache).where(
                    and_(
                        TranslationCache.content_hash == content_hash,
                        TranslationCache.url_hash == url_hash,
                        TranslationCache.source_language == source_language,
                        TranslationCache.target_language == target_language,
                        TranslationCache.expires_at > datetime.utcnow()
                    )
                )

                result = await session.execute(query)
                result = result.scalar_one_or_none()

                if result:
                    # Update hit count and last hit timestamp
                    update_query = update(TranslationCache).where(
                        TranslationCache.id == result.id
                    ).values(
                        hit_count=TranslationCache.hit_count + 1,
                        last_hit_at=datetime.utcnow()
                    )
                    await session.execute(update_query)
                    await session.commit()

                    return {
                        "translated_text": result.translated_text,
                        "original_text": result.original_text,
                        "cached": True,
                        "cache_created_at": result.created_at.isoformat(),
                        "cache_expires_at": result.expires_at.isoformat(),
                        "hit_count": result.hit_count + 1,
                        "model": result.model_version,
                        "confidence_score": float(result.quality_score) if result.quality_score else 0.95
                    }

        return None

    async def cache_translation(
        self,
        text: str,
        translated_text: str,
        source_language: str,
        target_language: str,
        model: str = "gemini-2.0-flash-lite",
        confidence_score: float = 0.95,
        processing_time_ms: int = 0,
        page_url: Optional[str] = None,
        job_id: Optional[str] = None,
        ttl_hours: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Cache a translation result.

        Args:
            text: Original text
            translated_text: Translated text
            source_language: Source language code
            target_language: Target language code
            model: Model name used for translation
            confidence_score: Translation confidence score
            processing_time_ms: Processing time in milliseconds
            page_url: Optional page URL for context
            job_id: Optional job ID reference
            ttl_hours: Time to live in hours (default: 168 = 7 days)
            db: Database session (unused, creates own session)

        Returns:
            Cache entry information
        """
        async with AsyncSessionLocal() as session:
            # Generate hashes and keys
            cache_key = self._generate_cache_key(text, source_language, target_language, page_url)
            content_hash = self._generate_content_hash(text)
            url_hash = self._generate_url_hash(page_url) if page_url else None
            ttl = ttl_hours or self.default_ttl_hours
            expires_at = datetime.utcnow() + timedelta(hours=ttl)

            # Check if cache entry already exists
            existing = await session.execute(
                select(TranslationCache).where(
                    TranslationCache.cache_key == cache_key
                )
            )
            existing = existing.scalar_one_or_none()

            if existing:
                # Update existing entry
                update_query = update(TranslationCache).where(
                    TranslationCache.id == existing.id
                ).values(
                    translated_text=translated_text,
                    processing_time_ms=processing_time_ms,
                    model_version=model,
                    quality_score=confidence_score,
                    expires_at=expires_at,
                    updated_at=datetime.utcnow()
                )
                await session.execute(update_query)
                cache_id = existing.id
            else:
                # Create new cache entry
                cache_entry = TranslationCache(
                    cache_key=cache_key,
                    job_id=uuid.UUID(job_id) if job_id else None,
                    content_hash=content_hash,
                    page_url=page_url,
                    url_hash=url_hash,
                    source_language=source_language,
                    target_language=target_language,
                    original_text=text,
                    translated_text=translated_text,
                    processing_time_ms=processing_time_ms,
                    model_version=model,
                    quality_score=confidence_score,
                    ttl_hours=ttl,
                    expires_at=expires_at
                )
                session.add(cache_entry)
                await session.flush()
                cache_id = cache_entry.id

            await session.commit()

            return {
                "cached": True,
                "cache_id": str(cache_id),
                "cache_key": cache_key,
                "expires_at": expires_at.isoformat(),
                "ttl_hours": ttl
            }

    async def clear_expired_cache(self, db: AsyncSession = None) -> int:
        """
        Remove expired cache entries.

        Args:
            db: Database session (unused, creates own session)

        Returns:
            Number of entries removed
        """
        async with AsyncSessionLocal() as session:
            # Delete expired entries
            delete_query = delete(TranslationCache).where(
                TranslationCache.expires_at <= datetime.utcnow()
            )
            result = await session.execute(delete_query)
            await session.commit()

            return result.rowcount

    async def clear_cache_by_url(
        self,
        page_url: str,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        db: AsyncSession = None
    ) -> int:
        """
        Clear cache entries for a specific URL.

        Args:
            page_url: URL to clear cache for
            source_language: Optional source language filter
            target_language: Optional target language filter
            db: Database session (unused, creates own session)

        Returns:
            Number of entries removed
        """
        async with AsyncSessionLocal() as session:
            url_hash = self._generate_url_hash(page_url)

            conditions = [TranslationCache.url_hash == url_hash]

            if source_language:
                conditions.append(TranslationCache.source_language == source_language)
            if target_language:
                conditions.append(TranslationCache.target_language == target_language)

            delete_query = delete(TranslationCache).where(and_(*conditions))
            result = await session.execute(delete_query)
            await session.commit()

            return result.rowcount

    async def get_cache_stats(self, db: AsyncSession = None) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            db: Database session (unused, creates own session)

        Returns:
            Cache statistics
        """
        async with AsyncSessionLocal() as session:
            # Total entries
            total_entries_result = await session.execute(
                select(TranslationCache)
            )
            total_entries = len(total_entries_result.all())

            # Expired entries
            expired_entries_result = await session.execute(
                select(TranslationCache).where(
                    TranslationCache.expires_at <= datetime.utcnow()
                )
            )
            expired_entries = len(expired_entries_result.all())

            # Active entries
            active_entries = total_entries - expired_entries

            # Total hits
            total_hits_result = await session.execute(
                select(TranslationCache.hit_count)
            )
            total_hits = total_hits_result.all()
            total_hits_sum = sum(hit[0] for hit in total_hits) if total_hits else 0

            # Most popular entries
            popular_query = select(TranslationCache).where(
                TranslationCache.expires_at > datetime.utcnow()
            ).order_by(TranslationCache.hit_count.desc()).limit(5)

            popular_entries_result = await session.execute(popular_query)
            popular_entries = popular_entries_result.all()

            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "total_hits": total_hits_sum,
                "average_hits_per_entry": total_hits_sum / active_entries if active_entries > 0 else 0,
                "most_popular": [
                    {
                        "cache_key": entry.cache_key[:50] + "...",
                        "hit_count": entry.hit_count,
                        "created_at": entry.created_at.isoformat(),
                        "expires_at": entry.expires_at.isoformat()
                    }
                    for entry in popular_entries
                ]
            }


# Global cache service instance
cache_service = TranslationCacheService()