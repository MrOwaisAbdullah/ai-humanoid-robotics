"""
OpenAI embeddings generation for RAG system.

Handles batch embedding generation with proper error handling and retries.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import tiktoken
import openai
from openai import AsyncOpenAI
import backoff

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings using OpenAI's API."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        max_retries: int = 3,
        batch_size: int = 100
    ):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.client = AsyncOpenAI(api_key=api_key)
        self.encoding = tiktoken.get_encoding("cl100k_base")

    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError),
        max_tries=5,
        base=2,
        max_value=60
    )
    async def generate_embedding(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a single embedding with retry logic."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding

            result = {
                "embedding": embedding,
                "text": text,
                "model": self.model,
                "usage": response.usage.model_dump() if response.usage else None
            }

            if metadata:
                result["metadata"] = metadata

            return result

        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for multiple texts in batches."""
        if not texts:
            return []

        # Ensure metadata list matches texts length
        if metadata_list is None:
            metadata_list = [None] * len(texts)
        elif len(metadata_list) != len(texts):
            metadata_list = metadata_list + [None] * (len(texts) - len(metadata_list))

        # Filter out empty texts and track indices
        valid_data = []
        for i, text in enumerate(texts):
            if text and text.strip():  # Only process non-empty texts
                # Check token count and truncate if necessary (model limit is ~8192 tokens)
                clean_text = text.strip()
                token_count = self.get_token_count(clean_text)
                if token_count > 8000:  # Leave some buffer
                    # Truncate the text
                    tokens = self.encoding.encode(clean_text)[:8000]
                    clean_text = self.encoding.decode(tokens)
                    logger.warning(f"Truncated text from {token_count} to 8000 tokens for embedding")

                valid_data.append((i, clean_text, metadata_list[i]))

        if not valid_data:
            logger.warning("No valid texts found for embedding generation")
            return []

        # Prepare filtered arrays
        original_indices = [data[0] for data in valid_data]
        filtered_texts = [data[1] for data in valid_data]
        filtered_metadata = [data[2] for data in valid_data]

        all_embeddings = [None] * len(texts)  # Initialize result array

        logger.info(f"Generating embeddings for {len(filtered_texts)} valid texts (filtered from {len(texts)})")

        # Process one by one to avoid batch API issues
        for i, (text, metadata) in enumerate(zip(filtered_texts, filtered_metadata)):
            try:
                # Generate single embedding
                result = await self.generate_embedding(text, metadata)

                # Place embedding back in original position
                original_idx = original_indices[i]
                result["original_index"] = original_idx
                all_embeddings[original_idx] = result

                # Small delay to avoid rate limits
                if i < len(filtered_texts) - 1:
                    await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"Failed to generate embedding for text {i}: {str(e)}")
                # Add empty embedding for failed text
                original_idx = original_indices[i]
                all_embeddings[original_idx] = {
                    "embedding": None,
                    "text": text,
                    "error": str(e),
                    "metadata": metadata,
                    "original_index": original_idx
                }

        # Fill in None entries for empty texts
        for i, text in enumerate(texts):
            if all_embeddings[i] is None:
                all_embeddings[i] = {
                    "embedding": None,
                    "text": text,
                    "error": "Empty text skipped",
                    "metadata": metadata_list[i],
                    "original_index": i
                }

        successful_count = sum(1 for e in all_embeddings if e.get('embedding'))
        logger.info(f"Successfully generated {successful_count} embeddings out of {len(texts)} texts")
        return all_embeddings

    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError),
        max_tries=3,
        base=2,
        max_value=60
    )
    async def _generate_batch_with_retry(
        self,
        texts: List[str],
        metadata_list: List[Optional[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for a batch with retry logic."""
        try:
            # Filter out empty strings and None values
            valid_texts = []
            valid_metadata = []
            valid_indices = []

            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_metadata.append(metadata_list[i] if i < len(metadata_list) else None)
                    valid_indices.append(i)

            if not valid_texts:
                logger.warning("No valid texts found in batch for embedding generation")
                return []

            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )

            results = []
            for i, data in enumerate(response.data):
                result = {
                    "embedding": data.embedding,
                    "text": valid_texts[i],
                    "model": self.model,
                    "index": data.index,
                    "original_index": valid_indices[i]
                }

                if valid_metadata[i]:
                    result["metadata"] = valid_metadata[i]

                results.append(result)

            # Add usage information to first result
            if response.usage and results:
                results[0]["usage"] = response.usage.model_dump()

            return results

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            raise

    def get_token_count(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model."""
        # text-embedding-3-small: 1536 dimensions
        # text-embedding-3-large: 3072 dimensions
        # text-embedding-ada-002: 1536 dimensions
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return dimensions.get(self.model, 1536)

    async def close(self):
        """Close the OpenAI client."""
        if self.client:
            await self.client.close()