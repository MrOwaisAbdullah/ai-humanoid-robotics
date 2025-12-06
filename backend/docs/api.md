# RAG Backend API Documentation

## Overview

The RAG Backend API provides endpoints for ingesting Markdown documents and querying them using natural language with Retrieval-Augmented Generation (RAG).

## Base URL

```
http://localhost:7860
```

## Authentication

The API is publicly accessible with rate limiting. Optional API key authentication is supported for higher rate limits.

Include the API key in the `X-API-Key` header:
```http
X-API-Key: your-api-key-here
```

## Rate Limiting

- Default: 60 requests per minute
- With API key: Higher limits (configurable)
- Endpoints have specific limits

## Response Format

All responses follow this structure:

```json
{
  "data": {...},
  "error": "Error message if any",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Endpoints

### Health Check

Check system health and status.

**Endpoint**: `GET /health`

**Rate Limit**: 100/minute

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "qdrant": {
      "status": "healthy",
      "details": {
        "collections": ["robotics_book"],
        "collection_stats": {
          "name": "robotics_book",
          "vector_count": 1250,
          "vector_size": 1536,
          "distance": "Cosine"
        }
      }
    },
    "openai": {
      "status": "configured",
      "details": {
        "api_key_configured": true,
        "model": "gpt-4-turbo-preview",
        "embedding_model": "text-embedding-3-small"
      }
    },
    "task_manager": {
      "status": "healthy",
      "details": {
        "total_tasks": 5,
        "running_tasks": 1,
        "status_counts": {
          "completed": 4,
          "running": 1
        }
      }
    }
  },
  "metrics": {
    "documents_count": 15,
    "chunks_count": 1250,
    "active_tasks": 1
  }
}
```

### Chat

Ask questions about the ingested book content.

**Endpoint**: `POST /chat`

**Rate Limit**: 60/minute (default)

**Request Body**:
```json
{
  "question": "What is humanoid robotics?",
  "session_id": "optional-session-uuid",
  "context_window": 4000,
  "k": 5,
  "stream": true,
  "filters": {
    "chapter": "Introduction"
  }
}
```

**Parameters**:
- `question` (required): User's question
- `session_id` (optional): Session ID for conversation context
- `context_window` (optional): Context window size in tokens (default: 4000)
- `k` (optional): Number of documents to retrieve (default: 5)
- `stream` (optional): Enable streaming response (default: true)
- `filters` (optional): Metadata filters for retrieval

#### Streaming Response

When `stream: true`, responses use Server-Sent Events:

```
data: {"type": "start", "session_id": "...", "sources": ["[Chapter 1 - Introduction](source)"]}

data: {"type": "chunk", "content": "Humanoid robotics"}

data: {"type": "chunk", "content": " is a field of robotics"}

...

data: {"type": "done", "session_id": "...", "response_time": 2.5, "tokens_used": 150}
```

#### Non-Streaming Response

When `stream: false`, returns a complete response:

```json
{
  "answer": "Humanoid robotics is a field of robotics...",
  "sources": [
    {
      "id": "cite-123",
      "chunk_id": "chunk-456",
      "document_id": "doc-789",
      "text_snippet": "Humanoid robotics refers to robots...",
      "relevance_score": 0.95,
      "chapter": "Chapter 1",
      "section": "Introduction"
    }
  ],
  "session_id": "session-uuid",
  "query": "What is humanoid robotics?",
  "response_time": 2.5,
  "tokens_used": 150,
  "model": "gpt-4-turbo-preview"
}
```

### Ingestion

Trigger document ingestion from Markdown files.

**Endpoint**: `POST /ingest`

**Rate Limit**: 10/minute

**Request Body**:
```json
{
  "content_path": "./book_content",
  "force_reindex": false,
  "batch_size": 100
}
```

**Parameters**:
- `content_path` (optional): Path to content directory (default: from config)
- `force_reindex` (optional): Clear existing collection (default: false)
- `batch_size` (optional): Processing batch size (default: 100)

**Response**:
```json
{
  "message": "Document ingestion started",
  "task_id": "ingest_1640995200_abc12345",
  "content_path": "./book_content",
  "force_reindex": false,
  "batch_size": 100,
  "status": "processing"
}
```

### Ingestion Status

Check status of ingestion tasks.

**Endpoint**: `GET /ingest/status`

**Rate Limit**: 30/minute

**Query Parameters**:
- `task_id` (optional): Specific task ID to check
- `limit` (optional): Number of tasks to return (default: 20)

**Response for Single Task**:
```json
{
  "task_id": "ingest_1640995200_abc12345",
  "content_path": "./book_content",
  "status": "completed",
  "progress": 100.0,
  "documents_found": 15,
  "documents_processed": 15,
  "chunks_created": 1250,
  "errors": [],
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:02:30Z",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:02:30Z"
}
```

**Response for All Tasks**:
```json
{
  "tasks": [
    {
      "task_id": "ingest_1640995200_abc12345",
      "status": "completed",
      "progress": 100.0,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1
}
```

### Cancel Ingestion Task

Cancel a running or pending ingestion task.

**Endpoint**: `POST /ingest/{task_id}/cancel`

**Rate Limit**: 10/minute

**Response**:
```json
{
  "message": "Task ingest_1640995200_abc12345 cancelled successfully"
}
```

### Ingestion Statistics

Get ingestion task statistics.

**Endpoint**: `GET /ingest/stats`

**Rate Limit**: 30/minute

**Response**:
```json
{
  "total_tasks": 25,
  "running_tasks": 1,
  "status_counts": {
    "completed": 20,
    "running": 1,
    "pending": 2,
    "failed": 2
  },
  "max_concurrent": 5
}
```

### Collections

Manage Qdrant collections.

#### List Collections

**Endpoint**: `GET /collections`

**Rate Limit**: 30/minute

**Response**:
```json
{
  "collections": ["robotics_book"]
}
```

#### Delete Collection

**Endpoint**: `DELETE /collections/{collection_name}`

**Rate Limit**: 10/minute

**Response**:
```json
{
  "message": "Collection 'robotics_book' deleted successfully"
}
```

## Error Handling

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized (if API key required)
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error
- `503`: Service Unavailable

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "request_id": "req-123",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Errors

#### Rate Limit Exceeded
```json
{
  "error": "Rate limit exceeded",
  "detail": "Maximum of 60 requests per minute allowed",
  "retry_after": 30
}
```

#### Invalid Request
```json
{
  "error": "Invalid request",
  "detail": "Field 'question' is required",
  "field": "question"
}
```

#### Service Unavailable
```json
{
  "error": "Service unavailable",
  "detail": "Qdrant connection failed"
}
```

## Best Practices

### 1. Session Management

Use consistent `session_id` for conversation continuity:

```javascript
const sessionId = localStorage.getItem('chat_session_id') ||
                  crypto.randomUUID();

localStorage.setItem('chat_session_id', sessionId);
```

### 2. Streaming Responses

Handle streaming responses properly:

```javascript
const response = await fetch('/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    question: "What is robotics?",
    session_id: sessionId,
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log(data);
    }
  }
}
```

### 3. Error Handling

Implement proper error handling:

```javascript
try {
  const response = await fetch('/chat', {...});

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Request failed');
  }

  // Handle response...
} catch (error) {
  console.error('Chat error:', error);
  // Show error to user
}
```

### 4. Rate Limiting

Respect rate limits and implement backoff:

```javascript
async function makeRequest(url, data, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
      });

      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || 60;
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
      }

      return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

## SDK Examples

### Python

```python
import requests

# Chat with streaming
response = requests.post(
    "http://localhost:7860/chat",
    json={
        "question": "What is humanoid robotics?",
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(data)
```

### JavaScript/Node.js

```javascript
// Using fetch for streaming
async function chat(question, sessionId) {
  const response = await fetch('http://localhost:7860/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      question,
      session_id: sessionId,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const {done, value} = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    console.log(text);
  }
}
```

### cURL

```bash
# Non-streaming chat
curl -X POST "http://localhost:7860/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is humanoid robotics?",
    "stream": false
  }'

# Ingest documents
curl -X POST "http://localhost:7860/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "content_path": "./book_content",
    "force_reindex": false
  }'

# Check health
curl "http://localhost:7860/health"
```