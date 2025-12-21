"""
Semantic retrieval functionality for RAG system.

Handles document retrieval, filtering, deduplication, and relevance scoring.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

from .qdrant_client import QdrantManager
from .embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """Represents a retrieved document chunk."""
    content: str
    metadata: Dict[str, Any]
    score: float
    rank: int
    is_duplicate: bool = False
    id: str = ""


class RetrievalEngine:
    """Handles semantic retrieval of documents from vector store."""

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        embedder: EmbeddingGenerator,
        default_k: int = 5,
        score_threshold: float = 0.5,  # Lowered to 0.5 to better match document scores
        max_context_tokens: int = 4000,
        enable_mmr: bool = True,
        mmr_lambda: float = 0.5
    ):
        self.qdrant_manager = qdrant_manager
        self.embedder = embedder
        self.default_k = default_k
        self.score_threshold = score_threshold
        self.max_context_tokens = max_context_tokens
        self.enable_mmr = enable_mmr
        self.mmr_lambda = mmr_lambda

    async def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        exclude_templates: bool = True,
        use_mmr: Optional[bool] = None,
        mmr_lambda: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query
            k: Number of documents to retrieve
            filters: Metadata filters
            rerank: Whether to apply reranking
            exclude_templates: Whether to exclude template content
            use_mmr: Use Maximal Marginal Relevance
            mmr_lambda: MMR diversity parameter

        Returns:
            List of retrieved documents with scores
        """
        max_results = k or self.default_k
        threshold = self.score_threshold
        use_mmr = use_mmr if use_mmr is not None else self.enable_mmr
        lambda_param = mmr_lambda if mmr_lambda is not None else self.mmr_lambda

        # Validate query
        if not query or len(query.strip()) < 1:
            raise ValueError("Query must be at least 1 character long")

        # Adaptive threshold for very generic queries
        query_words = query.strip().lower().split()
        generic_words = ['tell', 'about', 'the', 'book', 'me', 'show', 'what', 'is', 'are', 'all']
        generic_ratio = len([w for w in query_words if w in generic_words]) / len(query_words) if query_words else 0
        logger.info(f"Query analysis: '{query}', generic_ratio={generic_ratio:.2f}, length={len(query.strip())}")

        # Check for generic query patterns
        is_generic = False
        generic_patterns = [
            'tell me about',
            'what is',
            'what are',
            'what this book',
            'about the book',
            'show me'
        ]
        query_lower = query.strip().lower()
        for pattern in generic_patterns:
            if pattern in query_lower:
                is_generic = True
                logger.info(f"Generic pattern detected: '{pattern}' in query")
                break

        # If query is very generic (>60% generic words) or contains generic patterns, lower the threshold
        if generic_ratio > 0.6 or len(query.strip()) < 20 or is_generic:
            # For extremely generic queries, lower threshold significantly
            if generic_ratio >= 0.8 or is_generic:  # Very high generic ratio or contains pattern
                threshold = 0.35  # Lower threshold for generic queries
                logger.info(f"Generic query detected (ratio: {generic_ratio:.2f}, pattern: {is_generic}), setting threshold to {threshold}")
            else:
                threshold = max(0.4, threshold - 0.3)  # Lower threshold but not below 0.4
                logger.info(f"Semi-generic query detected (ratio: {generic_ratio:.2f}), adjusting threshold to {threshold}")

        try:
            # Generate query embedding
            logger.info(f"Generating embedding for query: {query[:100]}...")

            if self.embedder:
                embedding_result = await self.embedder.generate_embedding(query)
                query_embedding = embedding_result["embedding"]
            else:
                # If no embedder provided, we can't search - this is an error case
                raise ValueError("Embedding generator not provided")

            # Initial retrieval from vector store
            logger.info(f"Retrieving up to {max_results} documents from vector store...")

            # Get more results to account for filtering and deduplication
            search_limit = min(max_results * 3, 100)  # Reasonable upper limit

            raw_results = await self.qdrant_manager.search_similar(
                query_embedding=query_embedding,
                limit=search_limit,
                score_threshold=0.1,  # Use very low threshold for initial search, filter later
                filters=filters
            )

            logger.info(f"Raw search returned {len(raw_results)} results")
            if raw_results:
                scores = [r.get("score", 0) for r in raw_results[:5]]
                logger.info(f"Top 5 similarity scores: {scores}")

            if not raw_results:
                logger.warning("No documents retrieved even with low threshold")
                return []

            # Convert to RetrievedChunk objects
            chunks = []
            for result in raw_results:
                # Get metadata from the correct location
                metadata = result.get("metadata", {}) or result.get("payload", {})

                # Debug: Log metadata for first few chunks
                if len(chunks) < 3:
                    logger.debug(f"Chunk metadata - chapter: {metadata.get('chapter')}, section: {metadata.get('section_header')}, url: {metadata.get('url')}")

                # Apply template filtering if requested
                if exclude_templates and metadata.get("is_template", False):
                    logger.debug(f"Skipping template chunk: {metadata.get('section_header', 'unknown')}")
                    continue

                chunk = RetrievedChunk(
                    content=result.get("content", ""),
                    metadata=metadata,
                    score=result.get("score", 0.0),
                    rank=0,  # Will be set later
                    is_duplicate=False,
                    id=result.get("id", "")
                )
                chunks.append(chunk)

            logger.info(f"Created {len(chunks)} chunks after template filtering")

            # Apply deduplication based on content hash
            chunks = self._deduplicate_chunks(chunks)
            logger.info(f"After deduplication: {len(chunks)} unique chunks")

            # Apply similarity threshold filtering
            logger.info(f"Applying threshold filter: {len(chunks)} chunks before filtering, threshold={threshold}")
            # Debug: Log scores of first few chunks
            for i, chunk in enumerate(chunks[:5]):
                logger.info(f"Chunk {i} score: {chunk.score}, content preview: {chunk.content[:100]}...")
            initial_count = len(chunks)
            chunks = [
                chunk for chunk in chunks
                if chunk.score >= threshold
            ]
            logger.info(f"After threshold filter: {len(chunks)} chunks remaining (filtered out {initial_count - len(chunks)} chunks)")

            # Apply MMR if enabled and we have enough results (but not for very few results)
            if use_mmr and len(chunks) > 3:
                chunks = await self._apply_mmr(query_embedding, chunks, max_results, lambda_param)
            elif use_mmr and len(chunks) <= 3:
                logger.info(f"Skipping MMR due to low result count: {len(chunks)} chunks")

            # Sort by score and limit
            chunks.sort(key=lambda x: x.score, reverse=True)
            chunks = chunks[:max_results]

            # Set final ranks
            for i, chunk in enumerate(chunks):
                chunk.rank = i + 1

            # Convert to list of dictionaries to match original interface
            results = []
            for chunk in chunks:
                results.append({
                    "chunk": chunk,
                    "similarity_score": chunk.score,
                    "metadata": chunk.metadata,
                    "rank": chunk.rank,
                    "is_duplicate": chunk.is_duplicate
                })

            logger.info(f"Retrieved {len(results)} documents after filtering")
            return results

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise

    def _deduplicate_chunks(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Remove duplicate chunks based on content hash.

        Args:
            chunks: List of chunks to deduplicate

        Returns:
            List of chunks with duplicates removed
        """
        seen_hashes: Set[str] = set()
        deduplicated = []
        duplicates = []

        for chunk in chunks:
            content_hash = chunk.metadata.get("content_hash")

            if not content_hash:
                # If no hash, check content equality (slowercase comparison)
                content_hash = chunk.content.lower().strip()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                deduplicated.append(chunk)
            else:
                # Mark as duplicate and add to duplicates list with lower score
                chunk.is_duplicate = True
                duplicates.append(chunk)

        # If we have duplicates, merge them with main chunks
        if duplicates:
            # Sort duplicates by score (highest first)
            duplicates.sort(key=lambda x: x.score, reverse=True)

            for duplicate in duplicates:
                # Find matching chunk in deduplicated list
                for original in deduplicated:
                    original_hash = original.metadata.get("content_hash", original.content.lower().strip())
                    dup_hash = duplicate.metadata.get("content_hash", duplicate.content.lower().strip())

                    if original_hash == dup_hash:
                        # Update metadata to indicate duplicate
                        original.metadata["duplicates"] = original.metadata.get("duplicates", []) + [
                            {
                                "file_path": duplicate.metadata.get("file_path"),
                                "section_header": duplicate.metadata.get("section_header"),
                                "score": duplicate.score
                            }
                        ]
                        break

        return deduplicated

    async def _apply_mmr(
        self,
        query_embedding: List[float],
        chunks: List[RetrievedChunk],
        k: int,
        lambda_param: float = 0.5
    ) -> List[RetrievedChunk]:
        """
        Apply Maximal Marginal Relevance to diversify results.

        Args:
            query_embedding: Query vector
            chunks: Retrieved chunks
            k: Number of results to return
            lambda_param: MMR diversity parameter (0=relevance, 1=diversity)

        Returns:
            Reordered chunks with MMR applied
        """
        selected_indices = []
        remaining_indices = list(range(len(chunks)))

        # Pre-compute chunk embeddings for efficiency
        chunk_embeddings = []
        for chunk in chunks:
            # In a real implementation, you'd retrieve or compute chunk embeddings
            # For now, use dummy embeddings based on content hash
            content_hash = chunk.metadata.get("content_hash", "")
            # Generate 1536-dimensional dummy embedding
            embedding = []
            for i in range(1536):
                # Use content hash to generate consistent pseudo-random values
                val = (hash(content_hash + str(i)) % 10000) / 10000.0
                embedding.append(val)
            chunk_embeddings.append(embedding)

        while len(selected_indices) < k and remaining_indices:
            best_score = -float('inf')
            best_idx = None

            for idx in remaining_indices:
                # Calculate MMR score
                relevance = self._cosine_similarity(
                    query_embedding,
                    chunk_embeddings[idx]
                )

                # Maximum similarity to already selected chunks
                max_sim = 0.0
                if selected_indices:
                    max_sim = max(
                        self._cosine_similarity(
                            chunk_embeddings[idx],
                            chunk_embeddings[sel_idx]
                        )
                        for sel_idx in selected_indices
                    )

                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)

        # Return selected chunks in order
        return [chunks[i] for i in selected_indices]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        v1_array = np.array(v1)
        v2_array = np.array(v2)

        dot_product = np.dot(v1_array, v2_array)
        norm1 = np.linalg.norm(v1_array)
        norm2 = np.linalg.norm(v2_array)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def retrieve_with_context(
        self,
        query: str,
        max_tokens: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Retrieve documents and format as context string within token limit.

        Args:
            query: Search query
            max_tokens: Maximum tokens for context
            filters: Additional filters

        Returns:
            Tuple of (retrieved_documents, context_string)
        """
        max_tokens = max_tokens or self.max_context_tokens

        # Retrieve documents
        results = await self.retrieve(
            query=query,
            k=10,  # Get more to allow for selection
            filters=filters,
            rerank=True,
            exclude_templates=True
        )

        # Extract chunks for formatting
        chunks = [r["chunk"] for r in results]

        # Format context
        context = self._format_context(chunks, max_tokens)

        return results, context

    def _format_document(self, doc: Dict[str, Any]) -> str:
        """Format a document for context."""
        metadata = doc.get("metadata", {})

        # Build citation string
        parts = []
        if metadata.get("chapter"):
            parts.append(f"Chapter: {metadata['chapter']}")
        if metadata.get("section_header"):
            parts.append(f"Section: {metadata['section_header']}")
        elif metadata.get("section"):
            parts.append(f"Section: {metadata['section']}")
        if metadata.get("file_path"):
            parts.append(f"Source: {metadata['file_path']}")

        citation = " - ".join(parts) if parts else "Source"

        # Format document
        formatted = f"[{citation}]\n{doc.get('content', '')}"

        return formatted

    def _format_context(
        self,
        chunks: List[RetrievedChunk],
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Format retrieved chunks as a context string.

        Args:
            chunks: Retrieved chunks
            max_tokens: Maximum tokens for context

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant information found."

        max_tokens = max_tokens or self.max_context_tokens
        context_parts = []
        current_tokens = 0

        for chunk in chunks:
            chunk_text = chunk.content
            chunk_tokens = chunk.metadata.get("token_count", 0)

            # Build citation string
            parts = []
            if chunk.metadata.get("chapter"):
                parts.append(f"Chapter: {chunk.metadata['chapter']}")
            if chunk.metadata.get("section_header"):
                parts.append(f"Section: {chunk.metadata['section_header']}")
            elif chunk.metadata.get("section"):
                parts.append(f"Section: {chunk.metadata['section']}")
            if chunk.metadata.get("file_path"):
                parts.append(f"Source: {chunk.metadata['file_path']}")

            citation = " - ".join(parts) if parts else "Source"

            # Check if adding this chunk would exceed token limit
            estimated_tokens = current_tokens + len(chunk_text.split()) + len(citation.split()) + 20  # Buffer

            if estimated_tokens > max_tokens:
                break

            context_parts.append(f"[{citation}]\n{chunk_text}\n")
            current_tokens = estimated_tokens

        return "\n".join(context_parts)

    async def retrieve_async(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Async wrapper for retrieve method.
        """
        return await self.retrieve(query, **kwargs)