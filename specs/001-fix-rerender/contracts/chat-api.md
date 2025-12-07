# Chat API Contracts

**Date**: 2025-12-07
**Version**: 1.0.0

## Overview

Internal API contracts for the chat widget streaming functionality. This is primarily for frontend-backend communication within the application.

## Streaming Endpoint

### POST /api/chat/stream

Initiates a streaming chat response from the AI.

#### Request

```typescript
interface ChatRequest {
  message: string;              // User message content (max 10,000 chars)
  context?: {
    selectedText?: string;       // Text selected by user (max 2,000 chars)
    source?: string;             // Source chapter/section info
  };
  stream: boolean;              // Always true for streaming
  sessionId?: string;            // Optional session identifier
}
```

#### Response (Server-Sent Events)

The response streams text chunks and metadata as separate events:

```typescript
// Content chunk event
event: chunk
data: {
  type: "content",
  content: string,              // Text chunk
  messageId: string             // Message identifier
}

// Source citation event
event: chunk
data: {
  type: "source",
  source: {
    chapter: string,
    section: string,
    direct_link: string,
    page_number?: number
  },
  messageId: string
}

// Completion event
event: chunk
data: {
  type: "complete",
  messageId: string
}

// Error event
event: error
data: {
  type: "error",
  error: {
    code: string,
    message: string,
    retryable: boolean
  }
}
```

### Error Response Format

```typescript
interface ChatError {
  code: "NETWORK_ERROR" | "VALIDATION_ERROR" | "TIMEOUT_ERROR" | "RATE_LIMIT" | "UNKNOWN_ERROR";
  message: string;
  details?: any;
  retryable: boolean;
  retryAfter?: number;           // Seconds to wait before retry (for rate limiting)
}
```

## Internal Contracts

### Chat State Events

These are internal events used by the chat widget state management:

```typescript
// State update actions
interface ChatAction {
  type: 'ADD_MESSAGE' | 'UPDATE_MESSAGE' | 'SET_STREAMING' | 'SET_THINKING' | 'SET_ERROR';
  payload: any;
}

// Message structure
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: SourceCitation[];
  isStreaming?: boolean;
}
```

### Streaming Protocol

```typescript
// Chunk types from backend
type StreamChunk = ContentChunk | SourceChunk | CompleteChunk | ErrorChunk;

interface ContentChunk {
  type: "content";
  content: string;
  messageId: string;
}

interface SourceChunk {
  type: "source";
  source: SourceCitation;
  messageId: string;
}

interface CompleteChunk {
  type: "complete";
  messageId: string;
}

interface ErrorChunk {
  type: "error";
  error: {
    code: string;
    message: string;
  };
}
```

## Validation Rules

### Request Validation

```typescript
const validateChatRequest = (request: ChatRequest): void => {
  // Message validation
  if (!request.message || request.message.trim().length === 0) {
    throw new Error('Message cannot be empty');
  }

  if (request.message.length > 10000) {
    throw new Error('Message too long (max 10,000 characters)');
  }

  // Context validation
  if (request.context?.selectedText) {
    if (request.context.selectedText.length > 2000) {
      throw new Error('Selected text too long (max 2,000 characters)');
    }
  }

  // Stream must be true for this endpoint
  if (!request.stream) {
    throw new Error('Streaming must be enabled');
  }
};
```

### Response Validation

```typescript
const validateStreamChunk = (chunk: StreamChunk): void => {
  if (!chunk.type) {
    throw new Error('Chunk must have type');
  }

  switch (chunk.type) {
    case 'content':
      if (!chunk.messageId) {
        throw new Error('Content chunk must have messageId');
      }
      break;

    case 'source':
      if (!chunk.source || !chunk.messageId) {
        throw new Error('Source chunk must have source and messageId');
      }
      break;

    case 'complete':
      if (!chunk.messageId) {
        throw new Error('Complete chunk must have messageId');
      }
      break;

    case 'error':
      if (!chunk.error) {
        throw new Error('Error chunk must have error details');
      }
      break;
  }
};
```

## Error Codes

| Code | Description | Retryable |
|------|-------------|-----------|
| NETWORK_ERROR | Failed to connect to backend | Yes |
| VALIDATION_ERROR | Invalid request format | No |
| TIMEOUT_ERROR | Request timed out | Yes |
| RATE_LIMIT | Too many requests | Yes (after delay) |
| CONTEXT_TOO_LARGE | Selected text exceeds limit | No |
| SESSION_EXPIRED | Chat session expired | Yes |
| MODEL_ERROR | AI model error | Yes |
| UNKNOWN_ERROR | Unexpected error | Yes |

## Rate Limits

```typescript
const RATE_LIMITS = {
  MESSAGES_PER_MINUTE: 30,
  MESSAGES_PER_HOUR: 200,
  MAX_CONCURRENT_STREAMS: 1,
  RETRY_AFTER_LIMIT: 60        // Seconds
};
```

## Connection Management

### Connection Lifecycle

1. **Initiate**: POST request with streaming flag
2. **Receive**: Process chunks as they arrive
3. **Complete**: Final chunk with type "complete"
4. **Error**: Error chunk with error details
5. **Abort**: Client can abort connection anytime

### Cleanup Requirements

- Abort controller on unmount
- Close event listeners
- Clear timeouts/intervals
- Reset streaming state

### Retry Logic

```typescript
const shouldRetry = (error: ChatError, attempt: number): boolean => {
  if (!error.retryable || attempt >= 3) {
    return false;
  }

  switch (error.code) {
    case 'NETWORK_ERROR':
    case 'TIMEOUT_ERROR':
    case 'MODEL_ERROR':
      return true;
    case 'RATE_LIMIT':
      return attempt < 5; // More retries for rate limits
    default:
      return false;
  }
};
```

## Browser Compatibility

### EventSource Support

For browsers that don't support EventSource natively (IE/Edge Legacy):

```typescript
// Polyfill check
if (!window.EventSource) {
  // Use fetch with stream reader as fallback
  const eventSourcePolyfill = {
    addEventListener: (event, handler) => {
      // Implementation using fetch API
    },
    close: () => {
      // Cleanup implementation
    }
  };
}
```

### WebSocket Alternative

For real-time bidirectional communication (future enhancement):

```typescript
interface WebSocketMessage {
  type: 'chat' | 'ping' | 'pong';
  payload: any;
}

// Protocol: ws(s)://domain/ws/chat
// Authentication: Via query parameter or header
```

## Monitoring Metrics

### Client-Side Metrics

```typescript
interface StreamingMetrics {
  startTime: number;
  firstChunkTime?: number;
  lastChunkTime?: number;
  totalChunks: number;
  totalBytes: number;
  errors: number;
  retries: number;
}
```

### Server-Side Metrics

- Response time percentiles (p50, p95, p99)
- Error rates by type
- Concurrent connections
- Tokens processed per request
- Model inference time

## Security Considerations

### Input Sanitization

- Escape HTML in message content
- Sanitize selected text context
- Validate URLs in source citations
- Limit message length

### CORS Headers

```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': window.location.origin,
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400'
};
```

### Authentication

If authentication is added:

```typescript
interface AuthenticatedRequest extends ChatRequest {
  sessionId?: string;
  userId?: string;
  token?: string;               // JWT or similar
}
```