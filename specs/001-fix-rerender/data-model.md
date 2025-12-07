# Data Model: Chat Widget State Management

**Date**: 2025-12-07
**Feature**: 001-fix-rerender
**Purpose**: Define optimized state structure to prevent infinite re-renders

## Core Entities

### ChatMessage

Represents a single message in the chat conversation.

```typescript
interface ChatMessage {
  id: string;                    // Unique identifier (e.g., `msg_${timestamp}_${type}`)
  content: string;               // Message text content
  role: 'user' | 'assistant';    // Who sent the message
  timestamp: Date;              // When the message was created
  sources?: SourceCitation[];    // Optional source references for AI responses
  isStreaming?: boolean;         // Is this message currently streaming?
}
```

### SourceCitation

Reference to source material mentioned in AI responses.

```typescript
interface SourceCitation {
  chapter: string;              // Chapter title
  section: string;              // Section name
  direct_link: string;          // URL to navigate to source
  page_number?: number;         // Optional page number
}
```

### ChatState

Consolidated chat state using useReducer pattern.

```typescript
interface ChatState {
  messages: ChatMessage[];      // Array of all messages
  isOpen: boolean;              // Is the chat widget open?
  isThinking: boolean;          // Is AI processing a request?
  currentStreamingId?: string;   // ID of message currently streaming
  error: string | null;         // Current error message
  inputText: string;            // Current text in input field
}
```

### ChatActions

Actions available for chat interactions (separate from state to prevent re-renders).

```typescript
interface ChatActions {
  sendMessage: (content: string) => Promise<void>;
  toggleWidget: () => void;
  closeWidget: () => void;
  clearMessages: () => void;
  updateMessage: (id: string, content: string) => void;
  setStreaming: (id: string, isStreaming: boolean) => void;
  setError: (error: string | null) => void;
  retryLastMessage: () => void;
}
```

## State Management Pattern

### Reducer Actions

Type-safe actions for state updates:

```typescript
type ChatAction =
  | { type: 'TOGGLE_WIDGET' }
  | { type: 'OPEN_WIDGET' }
  | { type: 'CLOSE_WIDGET' }
  | { type: 'SET_THINKING'; payload: boolean }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_MESSAGE'; payload: { id: string; content: string } }
  | { type: 'SET_STREAMING'; payload: { id: string; isStreaming: boolean } }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_INPUT_TEXT'; payload: string };
```

### Initial State

```typescript
export const initialChatState: ChatState = {
  messages: [],
  isOpen: false,
  isThinking: false,
  currentStreamingId: undefined,
  error: null,
  inputText: ''
};
```

## Context Structure

### Split Context Pattern

Separate contexts for state and actions to optimize re-renders:

```typescript
// Context for state values
const ChatStateContext = createContext<ChatState | undefined>(undefined);

// Context for actions (stable reference)
const ChatActionsContext = createContext<ChatActions | undefined>(undefined);
```

### Custom Hooks

```typescript
// Hook for accessing state
export const useChatState = () => {
  const context = useContext(ChatStateContext);
  if (!context) {
    throw new Error('useChatState must be used within ChatProvider');
  }
  return context;
};

// Hook for accessing actions
export const useChatActions = () => {
  const context = useContext(ChatActionsContext);
  if (!context) {
    throw new Error('useChatActions must be used within ChatProvider');
  }
  return context;
};

// Combined hook for convenience
export const useChat = () => {
  const state = useChatState();
  const actions = useChatActions();
  return { ...state, ...actions };
};
```

## Streaming Data Model

### Streaming State

```typescript
interface StreamingState {
  isActive: boolean;            // Is streaming active?
  currentMessageId?: string;    // ID of message being streamed
  buffer: string;               // Accumulated content buffer
  error: Error | null;          // Streaming error
}
```

### Streaming Chunk Processing

```typescript
interface StreamChunk {
  type: 'content' | 'error' | 'complete' | 'source';
  data: string | SourceCitation | Error;
}
```

## Input Validation Rules

### Message Content

```typescript
const MESSAGE_LIMITS = {
  MIN_LENGTH: 1,
  MAX_LENGTH: 10000,
  TRUNCATION_MESSAGE: ' (message truncated)'
};

export const validateMessage = (content: string): string => {
  if (content.length === 0) {
    throw new Error('Message cannot be empty');
  }

  if (content.length > MESSAGE_LIMITS.MAX_LENGTH) {
    return content.substring(0, MESSAGE_LIMITS.MAX_LENGTH) + MESSAGE_LIMITS.TRUNCATION_MESSAGE;
  }

  return content;
};
```

### Source Citations

```typescript
export const validateSource = (source: SourceCitation): void => {
  if (!source.chapter || !source.section || !source.direct_link) {
    throw new Error('Source must have chapter, section, and direct_link');
  }

  if (!source.direct_link.startsWith('http')) {
    throw new Error('Direct link must be a valid URL');
  }
};
```

## Performance Optimizations

### Message List Virtualization (Future)

For long conversations (50+ messages):

```typescript
interface VirtualizedListConfig {
  itemHeight: number;          // Height of each message
  bufferSize: number;          // Number of items to render outside viewport
  overscan: number;            // Extra items to render for smooth scrolling
}
```

### Message Caching

```typescript
interface MessageCache {
  get: (id: string) => ChatMessage | undefined;
  set: (id: string, message: ChatMessage) => void;
  clear: () => void;
}
```

## Error Model

### Error Types

```typescript
type ChatErrorType =
  | 'NETWORK_ERROR'
  | 'STREAMING_ERROR'
  | 'VALIDATION_ERROR'
  | 'TIMEOUT_ERROR'
  | 'UNKNOWN_ERROR';

interface ChatError {
  type: ChatErrorType;
  message: string;
  retryable: boolean;
  timestamp: Date;
}
```

### Error Handling Pattern

```typescript
export const createChatError = (
  type: ChatErrorType,
  message: string,
  retryable: boolean = false
): ChatError => ({
  type,
  message,
  retryable,
  timestamp: new Date()
});
```

## State Transitions

### Valid State Machine

```
[CLOSED] --> [OPENING] --> [OPEN] --> [CLOSING] --> [CLOSED]
    |              |          |           |
    v              v          v           v
  (none)       (none)    [THINKING]  (none)
                        |
                        v
                    [STREAMING] --> [COMPLETE]
                        |
                        v
                     [ERROR]
```

### Transition Rules

```typescript
const canTransition = (
  from: ChatState['status'],
  to: ChatState['status']
): boolean => {
  const validTransitions = {
    closed: ['opening'],
    opening: ['open', 'closed'],
    open: ['thinking', 'closing'],
    thinking: ['streaming', 'open', 'error'],
    streaming: ['complete', 'error', 'thinking'],
    complete: ['open'],
    error: ['thinking', 'open'],
    closing: ['closed']
  };

  return validTransitions[from]?.includes(to) ?? false;
};
```

## Memory Management

### Cleanup Requirements

1. **Event Listeners**: Remove on unmount
2. **Timers**: Clear all intervals/timeouts
3. **Streams**: Abort ongoing fetches
4. **Observers**: Disconnect ResizeObserver/IntersectionObserver

### Memory Limits

```typescript
const MEMORY_LIMITS = {
  MAX_MESSAGES: 100,           // Maximum messages to keep in memory
  MAX_MESSAGE_LENGTH: 50000,   // Maximum single message length
  CLEANUP_THRESHOLD: 0.8       // Trigger cleanup at 80% capacity
};
```

## Integration Points

### API Integration

```typescript
interface ChatAPI {
  sendMessage: (message: string) => Promise<AsyncIterable<StreamChunk>>;
  retryMessage: (messageId: string) => Promise<AsyncIterable<StreamChunk>>;
}
```

### Docusaurus Integration

```typescript
interface DocusaurusContext {
  siteConfig: {
    baseUrl: string;
    title: string;
  };
  location: {
    pathname: string;
  };
}
```

This data model provides a solid foundation for implementing the chat widget with optimized state management that prevents infinite re-renders.