# Data Model: RAG Backend API

**Date**: 2025-01-05
**Feature**: 1-rag-backend

## Core Entities

### 1. Document
Represents a source Markdown file containing book content.

**Attributes:**
- `id`: string (unique identifier)
- `file_path`: string (relative path from content root)
- `title`: string (document title, from filename or first H1)
- `chapter`: string (chapter name/number)
- `section`: string (section within chapter)
- `file_hash`: string (SHA256 for change detection)
- `word_count`: integer (total words in document)
- `chunk_count`: integer (number of chunks created)
- `last_modified`: datetime (file modification time)
- `ingested_at`: datetime (when document was processed)
- `status`: enum (pending, processing, completed, failed)

**Validation Rules:**
- `file_path` must be a valid relative path
- `title` cannot be empty
- `file_hash` is automatically calculated
- `word_count` >= 0

### 2. TextChunk
Represents a semantically meaningful piece of text from a document.

**Attributes:**
- `id`: string (unique identifier)
- `document_id`: string (foreign key to Document)
- `chunk_index`: integer (position within document)
- `text`: string (actual text content, ~500 tokens)
- `metadata`: object (additional information)
  - `chapter`: string
  - `section`: string
  - `start_char`: integer (character position in document)
  - `end_char`: integer (end position in document)
  - `heading_level`: integer (H1, H2, H3, etc.)
  - `heading_text`: string (heading text)
- `embedding`: list[float] (OpenAI embedding vector)
- `token_count`: integer (approximate token count)
- `created_at`: datetime (when chunk was created)

**Validation Rules:**
- `text` cannot be empty
- `embedding` must be 1536 dimensions (OpenAI text-embedding-3-small)
- `token_count` >= 0
- `chunk_index` >= 0

### 3. VectorCollection
Represents a collection in Qdrant for storing chunks.

**Attributes:**
- `name`: string (collection name)
- `vector_size`: integer (1536 for OpenAI embeddings)
- `distance_metric`: string (cosine, dotproduct, euclidean)
- `created_at`: datetime
- `chunk_count`: integer (total chunks stored)
- `last_updated`: datetime

**Default Values:**
- `vector_size`: 1536
- `distance_metric`: "cosine"

### 4. ConversationContext
Temporary storage for maintaining conversation context (last 3 messages).

**Attributes:**
- `session_id`: string (generated UUID)
- `messages`: array[Message] (up to 3 messages)
- `created_at`: datetime
- `last_accessed`: datetime
- `expires_at`: datetime (30 minutes from creation)

**Validation Rules:**
- `messages` length <= 3
- `expires_at` > `created_at`

### 5. Message
Represents a user query or system response.

**Attributes:**
- `id`: string (unique identifier)
- `role`: enum (user, assistant)
- `content`: string (message content)
- `citations`: array[Citation] (for assistant messages)
- `token_count`: integer (approximate tokens)
- `timestamp`: datetime (when message was created)

### 6. Citation
Reference to source material used in a response.

**Attributes:**
- `chunk_id`: string (reference to TextChunk)
- `text_snippet`: string (relevant excerpt)
- `relevance_score`: float (0.0 to 1.0)
- `source_location`: object
  - `file_path`: string
  - `chapter`: string
  - `section`: string
  - `heading`: string

**Validation Rules:**
- `relevance_score` between 0.0 and 1.0
- `text_snippet` cannot be empty

## Data Relationships

```
Document (1) -----> (N) TextChunk
    |                     |
    |                 (1) Citation
    |                     |
    |                (N) Message
    |
(N) VectorCollection
```

- One Document contains many TextChunks
- One TextChunk can have many Citations (in different responses)
- One Message can have many Citations
- Chunks are stored in one VectorCollection

## State Transitions

### Document Processing States
```
pending → processing → completed
    ↓
  failed
```

### Chunk Lifecycle
```
Created → Embedded → Stored → Retrieved
```

### Conversation Context Lifecycle
```
Created → Accessed → Updated → Expired
```

## Qdrant Collection Schema

### Payload Structure
```json
{
  "document_id": "doc_123",
  "chunk_index": 0,
  "metadata": {
    "chapter": "Chapter 1",
    "section": "1.1 Introduction",
    "heading_level": 2,
    "heading_text": "Introduction to Robotics",
    "file_path": "book/chapter1.md",
    "start_char": 0,
    "end_char": 1500
  },
  "text": "The actual chunk content...",
  "token_count": 420,
  "created_at": "2025-01-05T10:00:00Z"
}
```

### Index Configuration
```json
{
  "vector_size": 1536,
  "distance": "Cosine",
  "payload_schema": {
    "document_id": "keyword",
    "metadata.chapter": "keyword",
    "metadata.section": "text",
    "token_count": "integer"
  }
}
```

## API Request/Response Models

### ChatRequest
```json
{
  "question": "string (required)",
  "session_id": "string (optional)",
  "api_key": "string (optional)",
  "context_window": "integer (default: 3000)"
}
```

### ChatResponse (SSE)
```json
{
  "type": "chunk" | "citation" | "done" | "error",
  "content": "string (for type: chunk)",
  "citation": {
    "text": "relevant excerpt",
    "source": {
      "chapter": "Chapter X",
      "section": "X.Y",
      "heading": "Section Title"
    }
  }
}
```

### IngestRequest
```json
{
  "content_path": "string (default: ./book_content)",
  "force_reindex": "boolean (default: false)",
  "batch_size": "integer (default: 100)"
}
```

### HealthResponse
```json
{
  "status": "healthy" | "degraded",
  "version": "string",
  "uptime": "float (seconds)",
  "qdrant_connected": "boolean",
  "openai_connected": "boolean",
  "documents_count": "integer",
  "chunks_count": "integer"
}
```

## Performance Considerations

### Chunk Optimization
- Target 500 tokens per chunk with 50-token overlap
- Preserve paragraph boundaries when possible
- Include metadata for precise citations

### Vector Storage
- Use cosine similarity for semantic search
- Implement batch upserts for efficiency
- Store additional metadata for filtering

### Memory Management
- Limit conversation context to 3 messages
- Implement TTL for conversation contexts
- Use streaming for responses to minimize memory usage

### Scaling
- Implement connection pooling for Qdrant
- Use async operations throughout
- Monitor and optimize search result sizes