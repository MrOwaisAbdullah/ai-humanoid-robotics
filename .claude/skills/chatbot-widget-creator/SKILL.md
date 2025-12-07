---
name: chatbot-widget-creator
description: Creates a battle-tested ChatGPT-style chatbot widget that solves real-world production issues. Features infinite re-render protection, text selection "Ask AI", RAG backend integration, streaming SSE, and comprehensive performance monitoring.
category: frontend
version: 3.1.0
date_updated: 2025-12-07
---

# Chatbot Widget Creator Skill

## Purpose

Creates a **production-ready ChatGPT-style chatbot widget** with advanced features:
- **Infinite re-render protection** using useReducer and split context pattern
- **Text selection "Ask AI"** functionality with smart tooltips
- **Streaming responses** with Server-Sent Events (SSE)
- **RAG backend integration** ready for FastAPI/Qdrant setup
- **Performance monitoring** and debugging utilities
- **Modern glassmorphic UI** with ChatGPT-style interface

## Key Improvements Based on Real Implementation

### 1. **State Management Architecture**
- **useReducer pattern** instead of multiple useState hooks
- **Split context** (StateContext + ActionsContext) to prevent unnecessary re-renders
- **Stable callbacks** with proper dependencies to avoid circular references
- **AbortController** for proper cleanup of streaming connections

### 2. **Performance Optimizations**
- **React.memo** wrapping for expensive components
- **useMemo** for computed values and complex operations
- **useCallback** with stable dependencies
- **Render counter utilities** for debugging
- **Virtualization** support for long conversations (50+ messages)

### 3. **Text Selection Feature**
- **useTextSelection** hook for detecting text selections
- **Smart positioning tooltip** with edge detection
- **Context-aware prompts** when asking about selected text
- **Length validation** with truncation warnings

## Prerequisites

1. **Backend Requirements**:
   - FastAPI or similar with SSE support
   - Endpoint: `POST /api/chat` returning Server-Sent Events
   - Request format: `{ "question": string, "stream": boolean }`
   - Response format: SSE with `{ "type": "chunk", "content": string }`

2. **Frontend Dependencies**:
   ```bash
   npm install react framer-motion
   # Note: No ChatKit dependency - this is a custom implementation
   ```

## Quick Start

### 1. Create the Widget Structure

```bash
# Create main directory structure
mkdir -p src/components/ChatWidget/{components,hooks,contexts,utils,styles}

# Copy all template files
cp .claude/skills/chatbot-widget-creator/templates/* src/components/ChatWidget/
```

### 2. Backend API Requirements

Your backend must implement:

```python
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint with Server-Sent Events streaming."""

    # Request format
    {
        "question": "What is physical AI?",
        "stream": true,
        "context": {  # Optional
            "selectedText": "...",
            "source": "User selection"
        }
    }

    # Response format (SSE)
    data: {"type": "start", "session_id": "..."}
    data: {"type": "chunk", "content": "Physical AI refers to..."}
    data: {"type": "chunk", "content": "embodied AI systems..."}
    data: {"type": "done", "session_id": "..."}
```

### 3. Integration

Add to your site root (e.g., `src/theme/Root.tsx`):

```tsx
import React from 'react';
import ChatWidgetContainer from '../components/ChatWidget/ChatWidgetContainer';

export default function Root({ children }) {
  const getChatEndpoint = () => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost') {
      return 'http://localhost:7860/api/chat';
    }
    return 'https://your-domain.com/api/chat';
  };

  return (
    <>
      {children}
      <ChatWidgetContainer
        apiUrl={getChatEndpoint()}
        maxTextSelectionLength={2000}
        fallbackTextLength={5000}
      />
    </>
  );
}
```

## Architecture Details

### State Management (Critical for Performance)

```typescript
// Consolidated state to prevent fragmentation
interface ChatState {
  messages: ChatMessage[];
  isOpen: boolean;
  isThinking: boolean;
  currentStreamingId?: string;
  error: Error | null;
  renderCount: number;
}

// Split context pattern
const ChatStateContext = createContext<{ state: ChatState }>();
const ChatActionsContext = createContext<{ actions: ChatActions }>();

// Components only subscribe to what they need
const messages = useChatSelector(s => s.messages);  // Re-renders on messages change
const actions = useChatActions();                   // Never re-renders
```

### Key Anti-Patterns Avoided

1. **❌ Multiple useState hooks**:
   ```typescript
   // Bad - causes context fragmentation
   const [messages, setMessages] = useState([]);
   const [isOpen, setIsOpen] = useState(false);
   ```

2. **✅ Consolidated useReducer**:
   ```typescript
   // Good - single state source
   const [state, dispatch] = useReducer(chatReducer, initialState);
   ```

3. **❌ Circular dependencies**:
   ```typescript
   // Bad - callback depends on state that changes
   const handleChunk = useCallback((chunk) => {
     if (session.currentStreamingId) {  // Dependency on state
       updateMessage(session.currentStreamingId, chunk);
     }
   }, [session.currentStreamingId]); // Infinite re-render!
   ```

4. **✅ Stable references**:
   ```typescript
   // Good - no circular dependencies
   const streamingIdRef = useRef<string>();
   const handleChunk = useCallback((chunk) => {
     if (streamingIdRef.current) {
       dispatch(updateStreamingAction(streamingIdRef.current, chunk));
     }
   }, [dispatch]); // Stable dependency array
   ```

### Streaming Response Handling

```typescript
// Proper SSE parsing
const lines = chunk.split('\n');
for (const line of lines) {
  if (line.startsWith('data: ')) {
    const data = line.slice(6);
    if (data !== '[DONE]') {
      const parsed = JSON.parse(data);

      if (parsed.type === 'chunk' && parsed.content) {
        handleChunk(parsed.content);
      } else if (parsed.type === 'done') {
        handleComplete();
      }
    }
  }
}
```

## Customization Guide

### Theming

Edit `src/components/ChatWidget/styles/ChatWidget.module.css`:

```css
/* Primary colors */
.widget {
  background: var(--ifm-color-emphasis-300);
  border: 1px solid var(--ifm-color-emphasis-600);
}

/* Message bubbles */
.userMessage {
  background: var(--ifm-color-primary);
}

.assistantMessage {
  background: var(--ifm-color-emphasis-200);
}
```

### Adding New Message Types

```typescript
// Extend ChatMessage interface
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  timestamp: Date;
  sources?: SourceCitation[];
  code?: boolean;
  metadata?: Record<string, any>;
}
```

### Performance Monitoring

Enable in development:

```typescript
import { usePerformanceMonitor } from '../utils/performanceMonitor';

function MyComponent() {
  const { renderCount } = usePerformanceMonitor('MyComponent');

  useEffect(() => {
    if (renderCount > 50) {
      console.warn(`Component re-rendered ${renderCount} times`);
    }
  });
}
```

## Production Deployment Checklist

### Frontend
- [ ] Remove performance monitoring in production build
- [ ] Enable React.memo for expensive components
- [ ] Implement virtualization for long conversations
- [ ] Add error boundaries for graceful failures
- [ ] Configure proper CSP headers for streaming

### Backend
- [ ] Implement rate limiting
- [ ] Add CORS configuration for your domain
- [ ] Set up monitoring for SSE connections
- [ ] Configure proper timeout handling
- [ ] Add health check endpoints

## Troubleshooting

### Common Issues and Solutions

1. **Infinite Re-renders**
   - Check for circular dependencies in useCallback
   - Ensure split context pattern is properly implemented
   - Use React DevTools Profiler to identify causes

2. **Memory Leaks**
   - Ensure AbortController cleanup on unmount
   - Check for unclosed SSE connections
   - Monitor with `window.performance.memory`

3. **SSE Not Working**
   - Verify CORS headers include `text/event-stream`
   - Check that responses use correct `data: {}` format
   - Ensure `Cache-Control: no-cache` is set

4. **Text Selection Issues**
   - Verify `useTextSelection` is enabled
   - Check for CSS `user-select: none` conflicts
   - Ensure z-index is high enough for tooltip

## Advanced Features

### Message Persistence

```typescript
// Add to ChatState
interface ChatState {
  // ...existing fields
  sessionId: string;
  persistedAt?: Date;
}

// In reducer
case 'PERSIST_CHAT':
  localStorage.setItem(`chat_${action.payload.sessionId}`, JSON.stringify(state.messages));
```

### File Attachments

```typescript
// Extend ChatRequest
interface ChatRequest {
  question: string;
  stream: boolean;
  attachments?: File[];
}

// Handle in UI
const handleFileUpload = (files: File[]) => {
  // Validate and prepare for upload
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
};
```

## Component Reference

### Core Components

1. **ChatWidgetContainer**: Main wrapper with provider
2. **ChatInterface**: ChatGPT-style UI
3. **ChatButton**: Floating action button
4. **SelectionTooltip**: Text selection "Ask AI" tooltip
5. **MessageBubble**: Individual message display
6. **InputArea**: Message input with file support

### Hooks

1. **useChatState**: Access chat state
2. **useChatActions**: Access chat actions
3. **useChatSelector**: Select specific state slices
4. **useTextSelection**: Text selection detection
5. **usePerformanceMonitor**: Development debugging

### Utilities

1. **chatReducer**: State transitions
2. **formatChatRequest**: API formatting
3. **renderCounter**: Debugging utility
4. **performanceMonitor**: Performance tracking

## Best Practices

1. **Always use the split context pattern** for complex state
2. **Stabilize callbacks** with useRef for frequently changing values
3. **Implement proper cleanup** for all async operations
4. **Monitor performance** in development
5. **Test edge cases** (empty state, errors, long messages)
6. **Use TypeScript strictly** for type safety
7. **Implement error boundaries** for graceful failures