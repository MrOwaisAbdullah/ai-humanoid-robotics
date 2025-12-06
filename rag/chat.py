"""
Chat functionality for RAG system.

Handles conversation context, retrieval, generation, and streaming responses.
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
import uuid
from datetime import datetime

import openai
from openai import AsyncOpenAI
import tiktoken

from .qdrant_client import QdrantManager
from .embeddings import EmbeddingGenerator
from .retrieval import RetrievalEngine
from .models import (
    Message, MessageRole, ConversationContext, Citation,
    ChatRequest, ChatResponse
)

logger = logging.getLogger(__name__)


class ChatHandler:
    """Handles chat functionality with RAG retrieval and streaming responses."""

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        openai_api_key: str,
        model: str = "gpt-4-turbo-preview",
        embedding_model: str = "text-embedding-3-small",
        max_context_messages: int = 3,
        context_window_size: int = 4000,
        max_retries: int = 3
    ):
        self.qdrant_manager = qdrant_manager
        self.model = model
        self.embedding_model = embedding_model
        self.max_context_messages = max_context_messages
        self.context_window_size = context_window_size
        self.max_retries = max_retries

        # Initialize clients
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.embedder = EmbeddingGenerator(
            api_key=openai_api_key,
            model=embedding_model
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Initialize retrieval engine with improved settings
        self.retrieval_engine = RetrievalEngine(
            qdrant_manager=qdrant_manager,
            embedder=self.embedder,
            score_threshold=0.7,  # Updated to 0.7 for better precision
            enable_mmr=True,
            mmr_lambda=0.5
        )

        # In-memory conversation context (for production, use Redis or database)
        self.conversations: Dict[str, ConversationContext] = {}

    def get_adaptive_threshold(self, query_length: int, result_count: int) -> float:
        """
        Get adaptive similarity threshold based on query characteristics.

        Args:
            query_length: Length of the query in characters
            result_count: Number of results found in initial search

        Returns:
            Adaptive threshold value
        """
        base_threshold = 0.7

        # Lower threshold for very specific queries (longer)
        if query_length > 100:
            return max(0.5, base_threshold - 0.2)

        # Raise threshold if too many results found
        if result_count > 20:
            return min(0.9, base_threshold + 0.2)

        # Lower threshold if very few results found
        if result_count < 3:
            return max(0.5, base_threshold - 0.1)

        return base_threshold

    async def stream_chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = 5,
        context_window: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response with Server-Sent Events.

        Yields JSON-formatted SSE messages.
        """
        start_time = datetime.utcnow()

        try:
            # Generate or retrieve session ID
            if not session_id:
                session_id = str(uuid.uuid4())

            # Get or create conversation context
            context = self._get_or_create_context(session_id)

            # Add user message to context
            user_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.USER,
                content=query,
                token_count=self.count_tokens(query)
            )
            context.add_message(user_message)

            # Retrieve relevant documents using RetrievalEngine
            logger.info(f"Retrieving {k} relevant documents...")

            # Get adaptive threshold if needed
            retrieved_docs = await self.retrieval_engine.retrieve(
                query=query,
                k=k * 3,  # Get more to account for filtering
                filters=filters,
                exclude_templates=True,
                use_mmr=True
            )

            # Limit to k results after filtering and deduplication
            retrieved_docs = retrieved_docs[:k]

            # Check if any documents were retrieved
            if not retrieved_docs:
                # If no documents found, try with a lower threshold for very short queries
                if len(query.strip()) < 20:
                    logger.info(f"Short query with no results, retrying with lower threshold...")
                    retrieved_docs = await self.retrieval_engine.retrieve(
                        query=query,
                        k=k,
                        filters=filters,
                        exclude_templates=True,
                        use_mmr=False  # Disable MMR for retry
                    )
                    retrieved_docs = retrieved_docs[:k]

                # If still no results, handle appropriately
                if not retrieved_docs:
                    logger.info(f"No content found for query: {query[:100]}...")
                    from api.exceptions import ContentNotFoundError
                    raise ContentNotFoundError(
                        query=query,
                        threshold=self.retrieval_engine.score_threshold
                    )

            # Log monitoring metrics
            logger.info(
                "Retrieval metrics - query_length=%d, retrieved_count=%d, threshold=%.2f, session_id=%s",
                len(query),
                len(retrieved_docs),
                self.retrieval_engine.score_threshold,
                session_id
            )

            # Log similarity scores for monitoring
            scores = [result["similarity_score"] for result in retrieved_docs]
            if scores:
                logger.info(
                    "Similarity scores - min=%.3f, max=%.3f, avg=%.3f, count=%d",
                    min(scores),
                    max(scores),
                    sum(scores) / len(scores),
                    len(scores)
                )

            # Create citations
            citations = []
            source_context = []

            for i, result in enumerate(retrieved_docs):
                chunk = result["chunk"]
                metadata = chunk.metadata

                citation = Citation(
                    id=str(uuid.uuid4()),
                    chunk_id=chunk.id,
                    document_id=metadata.get("document_id", ""),
                    text_snippet=chunk.content[:200] + "...",
                    relevance_score=result["similarity_score"],
                    chapter=metadata.get("chapter"),
                    section=metadata.get("section_header") or metadata.get("section"),
                    confidence=result["similarity_score"]
                )
                citations.append(citation)

                # Add to context with citation marker
                source_text = chunk.content
                if source_text:
                    source_context.append(f"[Source {i+1}]: {source_text}")

            # Build context with conversation history and retrieved documents
            context_messages = self._build_context_messages(
                context,
                source_context,
                context_window or self.context_window_size
            )

            # Send initial metadata
            yield self._format_sse_message({
                "type": "start",
                "session_id": session_id,
                "sources": [citation.to_markdown() for citation in citations],
                "retrieved_docs": len(retrieved_docs)
            })

            # Generate streaming response
            logger.info("Generating streaming response...")
            full_response = ""  # Initialize response accumulator

            stream = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=context_messages,
                stream=True,
                max_completion_tokens=1000
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        yield self._format_sse_message({
                            "type": "chunk",
                            "content": content
                        })

            # Create assistant message and add to context
            assistant_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=full_response,
                token_count=self.count_tokens(full_response),
                citations=[citation.id for citation in citations]
            )
            context.add_message(assistant_message)

            # Send completion message
            response_time = (datetime.utcnow() - start_time).total_seconds()
            yield self._format_sse_message({
                "type": "done",
                "session_id": session_id,
                "response_time": response_time,
                "tokens_used": user_message.token_count + assistant_message.token_count
            })

        except Exception as e:
            logger.error(f"Chat streaming failed: {str(e)}", exc_info=True)
            yield self._format_sse_message({
                "type": "error",
                "error": str(e)
            })

    async def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = 5,
        context_window: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Non-streaming chat response.

        Returns complete response with citations.
        """
        start_time = datetime.utcnow()

        try:
            # Generate or retrieve session ID
            if not session_id:
                session_id = str(uuid.uuid4())

            # Get or create conversation context
            context = self._get_or_create_context(session_id)

            # Add user message to context
            user_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.USER,
                content=query,
                token_count=self.count_tokens(query)
            )
            context.add_message(user_message)

            # Retrieve relevant documents using RetrievalEngine
            logger.info(f"Retrieving {k} relevant documents...")
            retrieved_docs = await self.retrieval_engine.retrieve(
                query=query,
                k=k * 3,  # Get more to account for filtering
                filters=filters,
                exclude_templates=True,
                use_mmr=True
            )

            # Limit to k results after filtering and deduplication
            retrieved_docs = retrieved_docs[:k]

            # Check if any documents were retrieved
            if not retrieved_docs:
                # If no documents found, try with a lower threshold for very short queries
                if len(query.strip()) < 20:
                    logger.info(f"Short query with no results, retrying with lower threshold...")
                    retrieved_docs = await self.retrieval_engine.retrieve(
                        query=query,
                        k=k,
                        filters=filters,
                        exclude_templates=True,
                        use_mmr=False  # Disable MMR for retry
                    )
                    retrieved_docs = retrieved_docs[:k]

                # If still no results, handle appropriately
                if not retrieved_docs:
                    logger.info(f"No content found for query: {query[:100]}...")
                    from api.exceptions import ContentNotFoundError
                    raise ContentNotFoundError(
                        query=query,
                        threshold=self.retrieval_engine.score_threshold
                    )

            # Log monitoring metrics
            logger.info(
                "Retrieval metrics - query_length=%d, retrieved_count=%d, threshold=%.2f, session_id=%s",
                len(query),
                len(retrieved_docs),
                self.retrieval_engine.score_threshold,
                session_id
            )

            # Log similarity scores for monitoring
            scores = [result["similarity_score"] for result in retrieved_docs]
            if scores:
                logger.info(
                    "Similarity scores - min=%.3f, max=%.3f, avg=%.3f, count=%d",
                    min(scores),
                    max(scores),
                    sum(scores) / len(scores),
                    len(scores)
                )

            # Create citations
            citations = []
            source_context = []

            for result in retrieved_docs:
                chunk = result["chunk"]
                metadata = chunk.metadata

                citation = Citation(
                    id=str(uuid.uuid4()),
                    chunk_id=chunk.id,
                    document_id=metadata.get("document_id", ""),
                    text_snippet=chunk.content[:200] + "...",
                    relevance_score=result["similarity_score"],
                    chapter=metadata.get("chapter"),
                    section=metadata.get("section_header") or metadata.get("section"),
                    confidence=result["similarity_score"]
                )
                citations.append(citation)

                # Add to context
                source_text = chunk.content
                if source_text:
                    source_context.append(f"[Source]: {source_text}")

            # Build context with conversation history and retrieved documents
            context_messages = self._build_context_messages(
                context,
                source_context,
                context_window or self.context_window_size
            )

            # Generate response
            logger.info("Generating response...")
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=context_messages,
                                max_completion_tokens=1000
            )

            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Create assistant message and add to context
            assistant_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=answer,
                token_count=self.count_tokens(answer),
                citations=[citation.id for citation in citations]
            )
            context.add_message(assistant_message)

            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()

            return ChatResponse(
                answer=answer,
                sources=citations,
                session_id=session_id,
                query=query,
                response_time=response_time,
                tokens_used=tokens_used,
                model=self.model
            )

        except Exception as e:
            logger.error(f"Chat failed: {str(e)}", exc_info=True)
            raise

    def _get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing conversation context or create new one."""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext(
                session_id=session_id,
                max_messages=self.max_context_messages,
                messages=[
                    Message(
                        id=str(uuid.uuid4()),
                        role=MessageRole.SYSTEM,
                        content=(
                            "You are an AI assistant for the book 'Physical AI and Humanoid Robotics'. "
                            "This book covers topics including physical AI systems, humanoid robots, "
                            "robot sensing, actuation mechanisms, and the convergence of AI with robotics. "
                            "Provide accurate, detailed answers based on the provided book content. "
                            "Always cite your sources using the format [Chapter - Section](source). "
                            "If users ask about topics outside this book (other books, movies, general knowledge), "
                            "politely explain: 'I can only provide information about Physical AI, humanoid robots, "
                            "and the specific topics covered in this book.' "
                            "If the book context doesn't contain relevant information, say so clearly."
                        ),
                        token_count=self.count_tokens(
                            "You are an AI assistant for the book 'Physical AI and Humanoid Robotics'. "
                            "This book covers topics including physical AI systems, humanoid robots, "
                            "robot sensing, actuation mechanisms, and the convergence of AI with robotics. "
                            "Provide accurate, detailed answers based on the provided book content. "
                            "Always cite your sources using the format [Chapter - Section](source). "
                            "If users ask about topics outside this book (other books, movies, general knowledge), "
                            "politely explain: 'I can only provide information about Physical AI, humanoid robots, "
                            "and the specific topics covered in this book.' "
                            "If the book context doesn't contain relevant information, say so clearly."
                        )
                    )
                ]
            )
        return self.conversations[session_id]

    def _build_context_messages(
        self,
        context: ConversationContext,
        source_texts: List[str],
        max_tokens: int
    ) -> List[Dict[str, str]]:
        """Build context messages for OpenAI API."""
        messages = []
        current_tokens = 0

        # Add system message
        system_msg = context.messages[0] if context.messages else None
        if system_msg:
            messages.append({
                "role": system_msg.role.value,
                "content": system_msg.content
            })
            current_tokens += system_msg.token_count

        # Add context from retrieved documents
        if source_texts:
            context_content = "\n\n".join(source_texts)
            context_message = {
                "role": "system",
                "content": f"Context from the book:\n\n{context_content}"
            }
            context_tokens = self.count_tokens(context_content)

            # Only add if within token limit
            if current_tokens + context_tokens < max_tokens * 0.6:  # Reserve 40% for conversation
                messages.append(context_message)
                current_tokens += context_tokens

        # Add conversation history
        for msg in context.get_context_messages():
            if msg.role != MessageRole.SYSTEM:  # System message already added
                msg_tokens = msg.token_count

                # Check if we have space for this message
                if current_tokens + msg_tokens < max_tokens * 0.9:  # Leave some buffer
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
                    current_tokens += msg_tokens
                else:
                    # Break if we're running out of space
                    break

        return messages

    def _format_sse_message(self, data: Dict[str, Any]) -> str:
        """Format message for Server-Sent Events."""
        return f"data: {json.dumps(data)}\n\n"

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    async def clear_context(self, session_id: str):
        """Clear conversation context for a session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared context for session: {session_id}")

    async def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session."""
        return self.conversations.get(session_id)

    async def close(self):
        """Close clients and cleanup."""
        if self.openai_client:
            await self.openai_client.close()
        if self.embedder:
            await self.embedder.close()