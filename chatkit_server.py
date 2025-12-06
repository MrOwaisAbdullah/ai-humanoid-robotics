"""
Custom ChatKit Server Implementation
Integrates RAG system with ChatKit Python SDK
"""
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import asyncio
import uuid
import structlog

logger = structlog.get_logger()

from chatkit.server import ChatKitServer
from chatkit.types import (
    ThreadStreamEvent,
    ThreadMetadata,
    UserMessageItem,
    AssistantMessageItem,
    ThreadItemDoneEvent,
)
from chatkit.store import Store
from chatkit.attachment_store import AttachmentStore

from rag.chat import ChatHandler
from rag.qdrant_client import QdrantManager
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"


class SimpleMemoryStore(Store):
    """Simple in-memory store for ChatKit"""

    def __init__(self):
        self.threads: Dict[str, ThreadMetadata] = {}
        self.thread_items: Dict[str, List[Dict]] = {}
        self.attachments: Dict[str, Dict] = {}

    def generate_thread_id(self, context: Any) -> str:
        return str(uuid.uuid4())

    def generate_item_id(self, item_type: str, thread: ThreadMetadata, context: Any) -> str:
        return str(uuid.uuid4())

    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata:
        if thread_id not in self.threads:
            # Create new thread if it doesn't exist
            self.threads[thread_id] = ThreadMetadata(
                id=thread_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={}
            )
            self.thread_items[thread_id] = []
        return self.threads[thread_id]

    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        self.threads[thread.id] = thread

    async def load_thread_items(
        self,
        thread_id: str,
        after: Optional[str],
        limit: int,
        order: str,
        context: Any
    ):
        items = self.thread_items.get(thread_id, [])
        # Simple pagination - in production, use proper database queries
        if after:
            # Find item index and get items after it
            for i, item in enumerate(items):
                if item.get("id") == after:
                    items = items[i+1:]
                    break

        # Return page format
        return {
            "items": items[:limit],
            "has_more": len(items) > limit
        }

    async def add_thread_item(self, thread_id: str, item: Dict, context: Any) -> None:
        if thread_id not in self.thread_items:
            self.thread_items[thread_id] = []
        self.thread_items[thread_id].append(item)

        # Update thread timestamp
        if thread_id in self.threads:
            self.threads[thread_id].updated_at = datetime.now()

    async def save_attachment(self, attachment: Dict, context: Any) -> None:
        self.attachments[attachment["id"]] = attachment

    async def load_attachment(self, attachment_id: str, context: Any) -> Dict:
        return self.attachments.get(attachment_id, {})

    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        if attachment_id in self.attachments:
            del self.attachments[attachment_id]

    async def load_threads(self, limit: int, after: Optional[str], order: str, context: Any):
        threads = list(self.threads.values())
        threads.sort(key=lambda t: t.updated_at, reverse=True)

        return {
            "items": threads[:limit],
            "has_more": len(threads) > limit
        }

    async def save_item(self, thread_id: str, item: Dict, context: Any) -> None:
        # Find and update existing item
        if thread_id in self.thread_items:
            for i, existing in enumerate(self.thread_items[thread_id]):
                if existing.get("id") == item.get("id"):
                    self.thread_items[thread_id][i] = item
                    return
        # If not found, add as new
        await self.add_thread_item(thread_id, item, context)

    async def load_item(self, thread_id: str, item_id: str, context: Any) -> Dict:
        if thread_id in self.thread_items:
            for item in self.thread_items[thread_id]:
                if item.get("id") == item_id:
                    return item
        return {}

    async def delete_thread(self, thread_id: str, context: Any) -> None:
        if thread_id in self.threads:
            del self.threads[thread_id]
        if thread_id in self.thread_items:
            del self.thread_items[thread_id]


class RAGChatKitServer(ChatKitServer):
    """Custom ChatKit server that integrates with RAG system"""

    def __init__(self, store: Store, settings: Settings):
        super().__init__(store)
        self.settings = settings
        # Initialize RAG components
        self.qdrant = QdrantManager(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.chat_handler = ChatHandler(
            openai_api_key=settings.openai_api_key,
            qdrant_manager=self.qdrant,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model
        )

    async def respond(
        self,
        thread: ThreadMetadata,
        input: Optional[UserMessageItem],
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Process user message and stream RAG-enhanced response"""

        if not input or not input.content:
            return

        # Extract user message text
        user_message = ""
        for content in input.content:
            if hasattr(content, 'text'):
                user_message += content.text
            elif isinstance(content, str):
                user_message += content

        if not user_message.strip():
            return

        # Save user message to thread
        user_item_id = self.store.generate_item_id("message", thread, context)
        user_item = {
            "id": user_item_id,
            "type": "message",
            "role": "user",
            "content": [{"type": "text", "text": user_message}],
            "created_at": datetime.now(),
        }
        await self.store.add_thread_item(thread.id, user_item, context)

        # Get chat history for context
        history_items = await self.store.load_thread_items(
            thread.id, None, 10, "desc", context
        )
        chat_history = []

        # Convert items to chat history format (excluding current message)
        for item in history_items.get("items", []):
            if item.get("id") != user_item_id:
                role = item.get("role", "user")
                content = ""
                for content_part in item.get("content", []):
                    if isinstance(content_part, dict) and content_part.get("text"):
                        content += content_part["text"]
                    elif isinstance(content_part, str):
                        content += content_part

                if content:
                    chat_history.append({"role": role, "content": content})

        # Reverse to get chronological order and limit to last 6 exchanges
        chat_history = list(reversed(chat_history[-6:]))

        # Generate RAG response
        try:
            # Stream the response
            response_content = ""
            async for chunk in self.chat_handler.stream_chat_response(
                query=user_message,
                history=chat_history,
                thread_id=thread.id
            ):
                if chunk:
                    response_content += chunk
                    # Stream chunk to client
                    yield {
                        "type": "message_chunk",
                        "id": user_item_id + "_response",
                        "content": [{"type": "text", "text": chunk}],
                    }

            # Save complete assistant response
            assistant_item_id = self.store.generate_item_id("message", thread, context)
            assistant_item = {
                "id": assistant_item_id,
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": response_content}],
                "created_at": datetime.now(),
            }
            await self.store.add_thread_item(thread.id, assistant_item, context)

            # Signal completion
            yield ThreadItemDoneEvent(id=assistant_item_id)

        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            # Send error message
            error_item_id = self.store.generate_item_id("message", thread, context)
            error_item = {
                "id": error_item_id,
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "I apologize, but I encountered an error while processing your request. Please try again."}],
                "created_at": datetime.now(),
            }
            await self.store.add_thread_item(thread.id, error_item, context)

            yield {
                "type": "message_chunk",
                "id": error_item_id,
                "content": [{"type": "text", "text": "I apologize, but I encountered an error while processing your request. Please try again."}],
            }
            yield ThreadItemDoneEvent(id=error_item_id)


# Global server instance
chatkit_server = None


def get_chatkit_server() -> RAGChatKitServer:
    """Get or create the ChatKit server instance"""
    global chatkit_server
    if chatkit_server is None:
        settings = Settings()
        store = SimpleMemoryStore()
        chatkit_server = RAGChatKitServer(store, settings)
    return chatkit_server