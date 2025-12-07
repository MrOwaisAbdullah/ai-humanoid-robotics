# Quickstart Guide: Chat Widget Re-render Fix

**Purpose**: Quick implementation reference for fixing infinite re-renders in the chat widget
**Date**: 2025-12-07

## Core Fix Strategy

The infinite re-render issue stems from three main problems:
1. Circular callback dependencies
2. Multiple overlapping state management systems
3. Unstable context references

## Step 1: Consolidate State Management

### Before (Problematic)
```typescript
// Multiple separate state hooks causing cascade re-renders
const [messages, setMessages] = useState([]);
const [isThinking, setIsThinking] = useState(false);
const [currentStreamingId, setCurrentStreamingId] = useState();
```

### After (Solution)
```typescript
// Single consolidated state with useReducer
const [state, dispatch] = useReducer(chatReducer, initialChatState);
```

## Step 2: Stabilize Callback Dependencies

### Before (Problematic)
```typescript
// Changes on every render due to session dependency
const handleChunk = useCallback((chunk: string) => {
  if (session.currentStreamingId) {
    updateMessage(session.currentStreamingId, chunk);
  }
}, [session.currentStreamingId, updateMessage]);
```

### After (Solution)
```typescript
// Use ref for streaming ID - no dependency needed
const streamingIdRef = useRef<string>();

const handleChunk = useCallback((chunk: string) => {
  const streamingId = streamingIdRef.current;
  if (streamingId) {
    updateMessage(streamingId, chunk);
  }
}, [updateMessage]); // Stable reference!
```

## Step 3: Split Context for Performance

### Before (Problematic)
```typescript
// Single context causes all consumers to re-render
const contextValue = useMemo(() => ({
  session,
  sendMessage,
  updateMessage,
  setStreaming
}), [session, sendMessage, updateMessage, setStreaming]);
```

### After (Solution)
```typescript
// Separate state from actions
const StateContext = createContext<ChatState>();
const ActionsContext = createContext<ChatActions>();

// Actions context has stable reference
const actions = useMemo(() => ({
  sendMessage,
  updateMessage,
  setStreaming
}), []); // Empty deps - stable functions
```

## Step 4: Use Updater Functions

### Before (Problematic)
```typescript
// Requires dependency on messages
const addMessage = useCallback((message) => {
  setMessages(prev => [...prev, message]);
}, [setMessages]);
```

### After (Solution)
```typescript
// No dependencies needed with reducer
const sendMessage = useCallback(async (content) => {
  dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
  dispatch({ type: 'SET_THINKING', payload: true });
}, []); // Empty deps!
```

## Implementation Checklist

### 1. Refactor ChatWidgetContainer

- [ ] Replace multiple useState with single useReducer
- [ ] Use useRef for values that change frequently but needed in callbacks
- [ ] Stabilize all useCallback dependencies
- [ ] Remove duplicate streaming state management

### 2. Update ChatProvider

- [ ] Split into StateContext and ActionsContext
- [ ] Memoize actions with empty dependency array
- [ ] Use functional updates to avoid dependencies
- [ ] Ensure context value stability

### 3. Fix Streaming Logic

- [ ] Consolidate useChatSession and useStreamingResponse
- [ ] Use useTransition for non-blocking updates
- [ ] Implement proper cleanup with AbortController
- [ ] Batch stream updates to prevent render thrashing

### 4. Optimize Components

- [ ] Use React.memo for expensive components
- [ ] Implement useMemo for computed values
- [ ] Add proper dependency arrays to all hooks
- [ ] Remove functions from useEffect dependencies

## Code Templates

### Reducer Implementation

```typescript
// chatReducer.ts
export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        isThinking: false,
        currentStreamingId: action.payload.isStreaming ? action.payload.id : undefined
      };

    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id
            ? { ...msg, content: action.payload.content }
            : msg
        )
      };

    case 'SET_STREAMING':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id
            ? { ...msg, isStreaming: action.payload.isStreaming }
            : msg
        ),
        currentStreamingId: action.payload.isStreaming ? action.payload.id : undefined
      };

    default:
      return state;
  }
}
```

### Provider Implementation

```typescript
// ChatProvider.tsx
export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);

  const actions = useMemo(() => ({
    sendMessage: useCallback(async (content: string) => {
      // Implementation using dispatch
      const userMessage: ChatMessage = {
        id: `msg_${Date.now()}_user`,
        content,
        role: 'user',
        timestamp: new Date()
      };

      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SET_THINKING', payload: true });

      // ... rest of implementation
    }, []),

    updateMessage: useCallback((id: string, content: string) => {
      dispatch({ type: 'UPDATE_MESSAGE', payload: { id, content } });
    }, []),

    setStreaming: useCallback((id: string, isStreaming: boolean) => {
      dispatch({ type: 'SET_STREAMING', payload: { id, isStreaming } });
    }, [])

    // ... other actions
  }), []);

  return (
    <ChatStateContext.Provider value={state}>
      <ChatActionsContext.Provider value={actions}>
        {children}
      </ChatActionsContext.Provider>
    </ChatStateContext.Provider>
  );
}
```

### Streaming Implementation

```typescript
// useStreamingResponse.ts
export function useStreamingResponse({ url, onChunk, onComplete, onError }) {
  const [isActive, setIsActive] = useState(false);
  const [isPending, startTransition] = useTransition();
  const controllerRef = useRef<AbortController>();

  const startStreaming = useCallback(async (request) => {
    if (controllerRef.current) {
      controllerRef.current.abort();
    }

    const controller = new AbortController();
    controllerRef.current = controller;

    setIsActive(true);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(request),
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' }
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);

        // Non-blocking update
        startTransition(() => {
          onChunk(chunk);
        });
      }

      onComplete();
    } catch (error) {
      if (error.name !== 'AbortError') {
        onError(error);
      }
    } finally {
      setIsActive(false);
    }
  }, [url, onChunk, onComplete, onError]); // Stable deps

  const stopStreaming = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  return { startStreaming, stopStreaming, isActive, isPending };
}
```

## Testing the Fix

### 1. Render Count Testing

```typescript
// Add render counter for debugging
let renderCount = 0;

function ChatWidgetContainer() {
  renderCount++;
  console.log(`Render count: ${renderCount}`);

  // ... component implementation
}
```

### 2. Performance Profiling

```typescript
// Use React DevTools Profiler
<Profiler id="ChatWidget" onRender={(id, phase, actualDuration) => {
  console.log(`${id} ${phase}:`, actualDuration);
}}>
  <ChatWidgetContainer />
</Profiler>
```

### 3. Memory Leak Detection

```typescript
// Check for memory leaks
useEffect(() => {
  const interval = setInterval(() => {
    const nodes = document.querySelectorAll('*');
    console.log('DOM nodes:', nodes.length);
  }, 5000);

  return () => clearInterval(interval);
}, []);
```

## Common Pitfalls to Avoid

1. **Don't pass objects directly to context**
   ```typescript
   // Bad
   <Context.Provider value={{ messages, actions }}>

   // Good
   <Context.Provider value={memoizedValue}>
   ```

2. **Don't ignore ESLint react-hooks exhaustive-deps warnings**
   ```typescript
   // Bad
   useEffect(() => {
     doSomething(value);
   }); // Missing dependency

   // Good
   useEffect(() => {
     doSomething(value);
   }, [value]); // Include dependency
   ```

3. **Don't create new functions in render**
   ```typescript
   // Bad
   <button onClick={() => handleClick(id)}>

   // Good
   const handleClick = useCallback((id) => {
     // implementation
   }, []);
   <button onClick={() => handleClick(id)}>
   ```

## Validation Steps

1. **Open chat widget** - Should render once
2. **Send a message** - Should trigger minimal re-renders
3. **Receive streaming response** - Should not cause render loop
4. **Check console** - No infinite re-render warnings
5. **Monitor memory** - Should stay stable over time

Remember: The key is stabilizing references and consolidating state updates!