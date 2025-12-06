"""
Response generation for RAG system.

Handles OpenAI API integration, prompt engineering, and citation formatting.
"""

import logging
from typing import List, Dict, Any, Optional
import json

import openai
from openai import AsyncOpenAI
import tiktoken

from .models import Citation, Message

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generates responses using OpenAI with retrieved context."""

    def __init__(
        self,
        openai_api_key: str,
        model: str = "gpt-5-nano",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.encoding = tiktoken.get_encoding("cl100k_base")

    async def generate_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Message]] = None,
        citations: Optional[List[Citation]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response based on query and retrieved context.

        Args:
            query: User's question
            context_documents: Retrieved documents
            conversation_history: Previous messages in conversation
            citations: Citation information

        Returns:
            Generated response with metadata
        """
        try:
            # Build prompt
            messages = self._build_messages(
                query,
                context_documents,
                conversation_history
            )

            # Generate response
            logger.info(f"Generating response for query: {query[:100]}...")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False
            )

            answer = response.choices[0].message.content
            usage = response.usage.model_dump() if response.usage else None

            # Post-process response
            processed_answer = self._post_process_response(
                answer,
                citations or []
            )

            return {
                "answer": processed_answer,
                "raw_answer": answer,
                "model": self.model,
                "usage": usage,
                "citations": [c.model_dump() for c in (citations or [])]
            }

        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            raise

    async def generate_streaming_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Message]] = None,
        citations: Optional[List[Citation]] = None
    ):
        """
        Generate streaming response using OpenAI's streaming API.

        Yields response chunks as they're generated.
        """
        try:
            # Build prompt
            messages = self._build_messages(
                query,
                context_documents,
                conversation_history
            )

            logger.info(f"Starting streaming response for query: {query[:100]}...")

            # Generate streaming response
            async with self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            ) as stream:
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield {
                                "type": "chunk",
                                "content": content
                            }

                # Send completion signal
                yield {
                    "type": "done",
                    "citations": [c.to_markdown() for c in (citations or [])]
                }

        except Exception as e:
            logger.error(f"Streaming response generation failed: {str(e)}")
            yield {
                "type": "error",
                "error": str(e)
            }

    def _build_messages(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Message]] = None
    ) -> List[Dict[str, str]]:
        """Build message list for OpenAI API."""
        messages = []

        # System message
        system_message = self._build_system_message()
        messages.append({"role": "system", "content": system_message})

        # Context message
        if context_documents:
            context_content = self._build_context(context_documents)
            messages.append({
                "role": "system",
                "content": f"Context from the book:\n\n{context_content}"
            })

        # Conversation history
        if conversation_history:
            for msg in conversation_history:
                if msg.role.value != "system":  # Skip system messages from history
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })

        # Current query
        messages.append({
            "role": "user",
            "content": query
        })

        return messages

    def _build_system_message(self) -> str:
        """Build the system message."""
        return (
            "You are an AI assistant for the book 'Physical AI and Humanoid Robotics'. "
            "This book specifically covers Physical AI systems, humanoid robots, robot sensing, "
            "actuation mechanisms, and the convergence of AI with robotics. "
            "Your task is to answer questions based on the provided book context. "
            "Follow these guidelines:\n\n"
            "1. Base your answers primarily on the provided book context\n"
            "2. If the context doesn't contain relevant information, say so clearly\n"
            "3. Use the citation format [Chapter - Section](source) when referencing information\n"
            "4. Provide detailed, accurate information about the book's topics\n"
            "5. If users ask about topics outside this book, respond: 'I can only provide information "
            "about Physical AI, humanoid robots, and the specific topics covered in this book.'\n"
            "6. If appropriate, structure your answer with clear headings and bullet points\n"
            "6. Be conversational but professional"
        )

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []

        for i, doc in enumerate(documents):
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")

            # Build citation header
            parts = []
            if metadata.get("chapter"):
                parts.append(f"Chapter: {metadata['chapter']}")
            if metadata.get("section"):
                parts.append(f"Section: {metadata['section']}")

            if parts:
                header = f"[{' - '.join(parts)}]"
                context_parts.append(f"{header}\n{content}")
            else:
                context_parts.append(f"[Source {i+1}]\n{content}")

        return "\n\n".join(context_parts)

    def _post_process_response(
        self,
        response: str,
        citations: List[Citation]
    ) -> str:
        """
        Post-process the generated response.

        - Ensures citations are properly formatted
        - Adds missing citations if needed
        - Cleans up formatting
        """
        # For now, return the response as-is
        # In production, you might want to:
        # - Ensure all claims have citations
        # - Format citations consistently
        # - Add reference list at the end
        return response

    async def generate_summary(
        self,
        documents: List[Dict[str, Any]],
        max_length: int = 300
    ) -> str:
        """Generate a summary of retrieved documents."""
        if not documents:
            return "No documents available for summary."

        # Combine document content
        combined_text = "\n\n".join([
            f"{doc.get('metadata', {}).get('chapter', 'Source')}: {doc.get('content', '')}"
            for doc in documents[:5]  # Limit to avoid token overflow
        ])

        summary_prompt = (
            "Please provide a concise summary of the following text, "
            "focusing on the main points about Physical AI and Humanoid Robotics:\n\n"
            f"{combined_text}\n\n"
            f"Summary (max {max_length} words):"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful summarizer."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=max_length * 2,  # Rough estimate
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return "Unable to generate summary."

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    async def close(self):
        """Close the OpenAI client."""
        if self.client:
            await self.client.close()