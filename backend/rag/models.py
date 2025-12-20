"""
Data models for the RAG system.

Defines entities for documents, chunks, conversations, and citations.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class DocumentStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChunkType(str, Enum):
    """Type of text chunk."""
    CHAPTER = "chapter"
    SECTION = "section"
    SUBSECTION = "subsection"
    PARAGRAPH = "paragraph"
    CODE = "code"
    TABLE = "table"
    OTHER = "other"


# User Story 1: Document Ingestion Models

class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    file_path: str = Field(..., description="Relative path to the file")
    file_name: str = Field(..., description="Name of the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    file_hash: str = Field(..., description="SHA256 hash of the file content")
    mime_type: str = Field(..., description="MIME type of the file")
    title: Optional[str] = Field(None, description="Document title if extractable")
    author: Optional[str] = Field(None, description="Document author if available")
    created_at: Optional[datetime] = Field(None, description="File creation time")
    modified_at: Optional[datetime] = Field(None, description="File modification time")
    chapters: List[str] = Field(default_factory=list, description="List of chapter titles")
    sections: List[str] = Field(default_factory=list, description="List of section titles")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class Document(BaseModel):
    """Represents a document in the system."""
    id: str = Field(..., description="Unique document identifier")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    status: DocumentStatus = Field(DocumentStatus.PENDING, description="Processing status")
    chunk_count: int = Field(0, description="Number of chunks created from this document")
    total_chunks: int = Field(0, description="Total number of chunks for this document")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Document creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    processed_at: Optional[datetime] = Field(None, description="Processing completion time")


class TextChunkMetadata(BaseModel):
    """Metadata for a text chunk."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    chunk_type: ChunkType = Field(..., description="Type of content in the chunk")
    chapter: Optional[str] = Field(None, description="Chapter title if applicable")
    section: Optional[str] = Field(None, description="Section title if applicable")
    subsection: Optional[str] = Field(None, description="Subsection title if applicable")
    page_number: Optional[int] = Field(None, description="Page number if available")
    line_start: Optional[int] = Field(None, description="Starting line number in source")
    line_end: Optional[int] = Field(None, description="Ending line number in source")
    word_count: int = Field(0, description="Number of words in the chunk")
    token_count: int = Field(0, description="Estimated token count for the chunk")
    level: int = Field(1, description="Hierarchical level (1=chapter, 2=section, etc.)")
    hierarchy_path: List[str] = Field(default_factory=list, description="Path in document hierarchy")
    tags: List[str] = Field(default_factory=list, description="Chunk-specific tags")
    language: str = Field("en", description="Language code of the content")


class TextChunk(BaseModel):
    """Represents a chunk of text from a document."""
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="The text content of the chunk")
    metadata: TextChunkMetadata = Field(..., description="Chunk metadata")
    content_hash: str = Field(..., description="SHA256 hash of the content")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the content")
    embedding_model: Optional[str] = Field(None, description="Model used for embedding")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Chunk creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


# User Story 2: Chat Models

class MessageRole(str, Enum):
    """Role of a message in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """A message in a conversation."""
    id: str = Field(..., description="Unique message identifier")
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    token_count: int = Field(0, description="Token count of the message")
    citations: List[str] = Field(default_factory=list, description="Citation IDs referenced")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")


class ConversationContext(BaseModel):
    """Context for a conversation session."""
    session_id: str = Field(..., description="Unique session identifier")
    messages: List[Message] = Field(default_factory=list, description="Conversation history")
    max_messages: int = Field(3, description="Maximum number of messages to keep in context")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity time")
    total_tokens: int = Field(0, description="Total tokens used in conversation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")

    def add_message(self, message: Message):
        """Add a message to the conversation context."""
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
        self.total_tokens += message.token_count

        # Keep only the last max_messages exchanges (user + assistant pairs)
        if len(self.messages) > self.max_messages * 2 + 1:  # +1 for system message
            # Remove the oldest message (keeping system message if present)
            if self.messages and self.messages[0].role != MessageRole.SYSTEM:
                self.messages.pop(0)
            elif len(self.messages) > 1:
                self.messages.pop(1)

    def get_context_messages(self) -> List[Message]:
        """Get messages for context window."""
        return self.messages[-self.max_messages * 2:] if self.messages else []


class Citation(BaseModel):
    """A citation referencing source content."""
    id: str = Field(..., description="Unique citation identifier")
    chunk_id: str = Field(..., description="Referenced chunk ID")
    document_id: str = Field(..., description="Source document ID")
    text_snippet: str = Field(..., description="Snippet of the cited text")
    relevance_score: float = Field(..., description="Relevance score of the citation")
    chapter: Optional[str] = Field(None, description="Chapter title")
    section: Optional[str] = Field(None, description="Section title")
    page_number: Optional[int] = Field(None, description="Page number if available")
    url: Optional[str] = Field(None, description="URL to the source content")
    confidence: float = Field(1.0, description="Confidence in the citation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Citation creation time")

    def to_markdown(self) -> str:
        """Convert citation to markdown format."""
        parts = []
        if self.chapter:
            # Format chapter name nicely
            chapter_name = self.chapter
            if not chapter_name.lower().startswith('chapter'):
                # Add "Chapter" prefix if not present
                chapter_name = f"Chapter {chapter_name}" if chapter_name.isdigit() else chapter_name
            parts.append(chapter_name)
        if self.section:
            # Clean up section name
            section_name = self.section
            # Remove excessive '#' and clean up
            section_name = re.sub(r'^#+\s*', '', section_name).strip()
            if section_name:
                parts.append(section_name)

        location = " - ".join(parts) if parts else "Source"
        link_target = self.url if self.url else f"{self.document_id}#{self.chunk_id}"
        return f"[{location}]({link_target})"


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., description="User question")
    session_id: Optional[str] = Field(None, description="Optional session ID for context")
    context_window: int = Field(4000, description="Context window size in tokens")
    k: int = Field(5, description="Number of documents to retrieve")
    stream: bool = Field(True, description="Whether to stream the response")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional search filters")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., description="Generated answer")
    sources: List[Citation] = Field(..., description="Source citations")
    session_id: str = Field(..., description="Session ID")
    query: str = Field(..., description="Original query")
    response_time: float = Field(..., description="Response time in seconds")
    tokens_used: int = Field(0, description="Tokens used for generation")
    model: str = Field(..., description="Model used for generation")


# User Story 3: Management Models

class IngestionTaskStatus(str, Enum):
    """Status of an ingestion task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IngestionTask(BaseModel):
    """Represents an ingestion task."""
    task_id: str = Field(..., description="Unique task identifier")
    content_path: str = Field(..., description="Path to content directory")
    status: IngestionTaskStatus = Field(IngestionTaskStatus.PENDING, description="Task status")
    progress: float = Field(0.0, description="Progress percentage (0-100)")
    documents_found: int = Field(0, description="Number of documents found")
    documents_processed: int = Field(0, description="Number of documents processed")
    chunks_created: int = Field(0, description="Number of chunks created")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")


class HealthStatus(BaseModel):
    """Health status of the system."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    qdrant_connected: bool = Field(..., description="Qdrant connection status")
    openai_api_key_configured: bool = Field(..., description="OpenAI API key status")
    collections: List[str] = Field(..., description="Available Qdrant collections")
    documents_count: int = Field(0, description="Total number of documents")
    chunks_count: int = Field(0, description="Total number of chunks")
    active_tasks: int = Field(0, description="Number of active ingestion tasks")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")