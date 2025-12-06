"""
Qdrant vector database operations for RAG system.

Handles collection management, vector storage, and semantic search.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
    SearchRequest,
    FilterSelector,
    HasIdCondition
)
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import CollectionInfo

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manages Qdrant vector database operations."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        embedding_dimension: int = 1536,
        collection_name: str = "robotics_book"
    ):
        self.url = url
        self.api_key = api_key
        self.embedding_dimension = embedding_dimension
        self.collection_name = collection_name
        self.client: Optional[AsyncQdrantClient] = None

    async def initialize(self):
        """Initialize Qdrant client and ensure collection exists."""
        try:
            # Initialize async client
            self.client = AsyncQdrantClient(
                url=self.url,
                api_key=self.api_key
            )

            # Test connection
            collections = await self.client.get_collections()
            logger.info(f"Connected to Qdrant. Existing collections: {[c.name for c in collections.collections]}")

            # Create collection if it doesn't exist
            await self.ensure_collection_exists()

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            raise

    async def ensure_collection_exists(self):
        """Ensure the collection exists with proper configuration."""
        try:
            # Check if collection exists
            try:
                collection_info = await self.client.get_collection(self.collection_name)
                logger.info(f"Collection '{self.collection_name}' already exists")
                logger.info(f"Collection info: {collection_info.config.params}")
                return
            except UnexpectedResponse as e:
                if e.status_code == 404:
                    # Collection doesn't exist, create it
                    pass
                else:
                    raise

            # Create collection
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection '{self.collection_name}' with dimension {self.embedding_dimension}")

        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {str(e)}")
            raise

    async def store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Store document chunks with their embeddings in Qdrant."""
        if not self.client:
            raise ValueError("Qdrant client not initialized")

        if not chunks:
            return {"stored": 0, "errors": []}

        # Prepare points for Qdrant
        points = []
        errors = []

        for chunk in chunks:
            try:
                if not chunk.get("embedding"):
                    errors.append(f"Chunk missing embedding: {chunk.get('metadata', {}).get('chunk_id', 'unknown')}")
                    continue

                point_id = str(uuid.uuid4())

                # Prepare payload with chunk data and metadata
                payload = {
                    "content": chunk.get("text", ""),
                    "metadata": chunk.get("metadata", {}),
                    "stored_at": datetime.utcnow().isoformat(),
                    "chunk_id": chunk.get("metadata", {}).get("chunk_id", point_id)
                }

                # Add any additional fields from metadata
                metadata = chunk.get("metadata", {})
                for key, value in metadata.items():
                    if key not in payload:
                        payload[key] = value

                point = PointStruct(
                    id=point_id,
                    vector=chunk["embedding"],
                    payload=payload
                )
                points.append(point)

            except Exception as e:
                chunk_id = chunk.get("metadata", {}).get("chunk_id", "unknown")
                errors.append(f"Failed to prepare chunk {chunk_id}: {str(e)}")

        # Store points in batches
        stored_count = 0
        total_batches = (len(points) + batch_size - 1) // batch_size

        for i in range(0, len(points), batch_size):
            batch_points = points[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            logger.info(f"Storing batch {batch_num}/{total_batches} with {len(batch_points)} points")

            try:
                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch_points
                )
                stored_count += len(batch_points)

            except Exception as e:
                logger.error(f"Failed to store batch {batch_num}: {str(e)}")
                for point in batch_points:
                    errors.append(f"Failed to store point {point.id}: {str(e)}")

        result = {
            "stored": stored_count,
            "errors": errors,
            "total_chunks": len(chunks)
        }

        logger.info(f"Storage completed: {result}")
        return result

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        if not self.client:
            raise ValueError("Qdrant client not initialized")

        try:
            # Build search filter
            search_filter = self._build_filter(filters) if filters else None

            # Search for similar vectors
            search_result = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False  # Don't return vectors to save bandwidth
            )

            # Convert results to standard format
            results = []
            for scored_point in search_result.points:
                result = {
                    "id": scored_point.id,
                    "score": scored_point.score,
                    "content": scored_point.payload.get("content", ""),
                    "metadata": scored_point.payload.get("metadata", {}),
                    "stored_at": scored_point.payload.get("stored_at"),
                    "chunk_id": scored_point.payload.get("chunk_id", scored_point.id)
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from filter dictionary."""
        conditions = []

        for key, value in filters.items():
            if isinstance(value, list):
                # Match any value in list
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(any=value)
                    )
                )
            else:
                # Match single value
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )

        return Filter(must=conditions) if conditions else None

    async def get_collection_info(self) -> Optional[CollectionInfo]:
        """Get information about the collection."""
        if not self.client:
            return None

        try:
            return await self.client.get_collection(self.collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return None

    async def list_collections(self) -> List[str]:
        """List all collections."""
        if not self.client:
            return []

        try:
            collections = await self.client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            return []

    async def delete_collection(self, collection_name: Optional[str] = None):
        """Delete a collection."""
        if not self.client:
            raise ValueError("Qdrant client not initialized")

        target_collection = collection_name or self.collection_name

        try:
            await self.client.delete_collection(target_collection)
            logger.info(f"Deleted collection '{target_collection}'")
        except Exception as e:
            logger.error(f"Failed to delete collection: {str(e)}")
            raise

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        if not self.client:
            return {}

        try:
            info = await self.get_collection_info()
            if not info:
                return {}

            return {
                "name": self.collection_name,
                "vector_count": info.points_count,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance.value,
                "status": info.status,
                "optimizer_status": info.optimizer_status
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}

    async def close(self):
        """Close the Qdrant client."""
        if self.client:
            await self.client.close()
            self.client = None