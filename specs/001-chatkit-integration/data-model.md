# Data Model: ChatKit Integration

## Core Entities

### ChatSession
```typescript
interface ChatSession {
  threadId?: string;        // ChatKit thread identifier
  isOpen: boolean;          // Widget visibility state
  createdAt: Date;          // Session creation timestamp
  lastActivity: Date;       // Last interaction timestamp
  messageCount: number;     // Total messages in session
}
```

### ChatMessage
```typescript
interface ChatMessage {
  id: string;              // Unique message identifier
  role: 'user' | 'assistant';  // Message sender
  content: string;          // Message content
  timestamp: Date;         // When message was sent/received
  citations?: Citation[];   // Optional citations from RAG
  metadata?: {            // Additional metadata
    selectedText?: string;  // If triggered by text selection
    sourceUrl?: string;    // Page URL where message originated
  };
}
```

### Citation
```typescript
interface Citation {
  id: string;              // Unique citation ID
  chunkId: string;         // Document chunk identifier
  documentId: string;      // Source document ID
  chapter?: string;        // Chapter name
  section?: string;        // Section name
  textSnippet: string;     // Preview of cited content
  relevanceScore: number;  // RAG retrieval score (0-1)
  url?: string;           // Link to cited content
}
```

### TextSelection
```typescript
interface TextSelection {
  id: string;              // Unique selection ID
  text: string;            // Selected content
  startOffset: number;     // Start position in document
  endOffset: number;       // End position in document
  contextUrl: string;      // URL of page with selection
  timestamp: Date;         // When selection was made
}
```

## LocalStorage Schema

### Chat Session Storage
```typescript
// Key: 'chat-session'
interface StoredChatSession {
  threadId?: string;
  isOpen: boolean;
  lastActivity: string;    // ISO timestamp
  messageCount: number;
}
```

### User Preferences
```typescript
// Key: 'chat-preferences'
interface ChatPreferences {
  theme: 'light' | 'dark' | 'auto';
  autoOpen: boolean;       // Auto-open on text selection
  notifications: boolean;  // Enable desktop notifications
  fontSize: 'small' | 'medium' | 'large';
}
```

## API Contracts

### Chat Endpoint (Server-Sent Events)
```typescript
// POST /chat
interface ChatRequest {
  message: string;         // User's message
  sessionId?: string;      // Optional session ID
  context?: {             // Optional context
    selectedText?: string;
    sourceUrl?: string;
  };
  k?: number;             // Number of documents to retrieve (default: 5)
}

// SSE Response Format
interface SSEChunk {
  type: 'start' | 'chunk' | 'done' | 'error' | 'citation';
  content?: string;       // For 'chunk' type
  sessionId?: string;     // For 'start' type
  sources?: Citation[];    // For 'citation' type
  error?: string;         // For 'error' type
  responseTime?: number;  // For 'done' type
}
```

### Session Management
```typescript
// POST /chatkit/session
interface SessionResponse {
  client_secret: string;   // ChatKit client token
  expires_in: number;      // Token lifetime in seconds
  thread_id?: string;      // Existing thread ID
}

// POST /chatkit/refresh
interface RefreshRequest {
  token: string;           // Current client token
}
```

## State Management

### React Component State
```typescript
interface ChatWidgetState {
  isOpen: boolean;
  isLoading: boolean;
  isStreaming: boolean;
  selectedText: string;
  messages: ChatMessage[];
  error: string | null;
  threadId: string | null;
}
```

### ChatKit Control State
```typescript
// Internal ChatKit state (managed by useChatKit hook)
interface ChatKitControl {
  threadId: string | null;
  isLoading: boolean;
  error: Error | null;
  // Additional ChatKit-specific state
}
```

## Validation Rules

### Chat Message Validation
- Content length: 1 - 4000 characters
- Must contain at least one non-whitespace character
- No HTML tags (sanitized on backend)
- Citation links must be valid URLs

### Session Validation
- Session ID: UUID v4 format
- Thread ID: ChatKit thread ID format
- Timestamps: ISO 8601 format

### Text Selection Validation
- Minimum length: 3 characters
- Maximum length: 1000 characters
- Must not be entirely whitespace
- Cannot be within chat widget element

## Error Types

```typescript
enum ChatError {
  NETWORK_ERROR = 'NETWORK_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  SESSION_EXPIRED = 'SESSION_EXPIRED',
  RATE_LIMITED = 'RATE_LIMITED',
  INVALID_REQUEST = 'INVALID_REQUEST',
  BACKEND_ERROR = 'BACKEND_ERROR',
  STREAM_INTERRUPTED = 'STREAM_INTERRUPTED'
}

interface ChatErrorDetail {
  type: ChatError;
  message: string;
  code?: string;
  retryable: boolean;
}
```

## Event Types

### Widget Events
```typescript
interface WidgetEventMap {
  'widget:open': void;
  'widget:close': void;
  'message:sent': { content: string };
  'message:received': { content: string; citations: Citation[] };
  'error': { error: ChatErrorDetail };
  'text:selected': { text: string; url: string };
}
```

### ChatKit Events
```typescript
// Events emitted by ChatKit (handled internally)
interface ChatKitEventMap {
  'thread-created': { threadId: string };
  'message-created': { messageId: string };
  'message-updated': { messageId: string };
  'run-created': { runId: string };
  'run-completed': { runId: string };
  'error': { error: Error };
}
```