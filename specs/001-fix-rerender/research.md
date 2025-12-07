# Research: React Re-render Optimization Patterns

**Date**: 2025-12-07
**Feature**: 001-fix-rerender
**Focus**: Infinite re-render loop fixes for React chat widget

## 1. Callback Dependency Patterns in useCallback

### **Primary Pattern: Use Updater Functions**
The most effective way to avoid dependency issues with `useCallback` is to use updater functions:

```javascript
// ❌ Bad - requires count dependency
const increment = useCallback(() => {
  setCount(count + 1);
}, [count]);

// ✅ Good - no dependencies needed
const increment = useCallback(() => {
  setCount(prevCount => prevCount + 1);
}, []); // Empty dependency array!
```

### **Complex State Updates**
Use `useReducer` for complex state logic:

```javascript
const [state, dispatch] = useReducer(reducer, initialState);

const actions = useMemo(() => ({
  update: (data) => dispatch({ type: 'UPDATE', payload: data }),
  reset: () => dispatch({ type: 'RESET' })
}), []); // Stable actions object

// No need for useCallback - dispatch is stable
```

## 2. Context Value Memoization Strategies

### **Always Memoize Context Values**
Never pass non-memoized values to context providers:

```javascript
// ✅ Good - memoized context value
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  const login = useCallback((userData) => {
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  const contextValue = useMemo(() => ({
    user,
    login,
    logout
  }), [user, login, logout]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
```

### **Split Contexts for Better Performance**
Separate frequently changing from rarely changing values:

```javascript
// Separate contexts
const UserContext = createContext();
const AuthActionsContext = createContext();

// Components that only need actions won't re-render on user changes
const ComponentNeedingActions = () => {
  const { login, logout } = useContext(AuthActionsContext);
  // ...
};
```

## 3. State Management Patterns to Prevent Render Loops

### **Consolidate Related State**
Avoid multiple state updates that cause multiple re-renders:

```javascript
// ✅ Good - consolidated state with useReducer
const [state, setState] = useReducer((state, action) => {
  switch (action.type) {
    case 'fetch':
      return { ...state, loading: true, error: null };
    case 'success':
      return { ...state, loading: false, data: action.payload };
    case 'error':
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
}, { loading: false, error: null, data: null });
```

### **Derived State Pattern**
Use useMemo for computed values instead of storing them:

```javascript
// ✅ Good - compute on demand
const [items, setItems] = useState([]);

const filteredItems = useMemo(() => {
  return items.filter(item => item.active);
}, [items]);
```

## 4. Streaming Data Handling Best Practices

### **Use useTransition for Non-blocking Updates**

```javascript
function StreamProcessor() {
  const [data, setData] = useState([]);
  const [isPending, startTransition] = useTransition();

  const processData = useCallback((chunk) => {
    // Mark update as transition for smoother UI
    startTransition(() => {
      setData(prev => [...prev, ...chunk]);
    });
  }, []); // No dependencies!

  useEffect(() => {
    const stream = new EventSource('/api/stream');

    stream.onmessage = (event) => {
      const chunk = JSON.parse(event.data);
      processData(chunk);
    };

    return () => stream.close();
  }, [processData]); // Stable reference

  return (
    <div>
      {isPending && <div>Processing...</div>}
      <DataList data={data} />
    </div>
  );
}
```

### **Abort Stream Cleanup**
Always clean up streams to prevent memory leaks:

```javascript
const useStreamingData = (url) => {
  const [data, setData] = useState([]);
  const controllerRef = useRef();

  useEffect(() => {
    const controller = new AbortController();
    controllerRef.current = controller;

    fetch(url, { signal: controller.signal })
      .then(response => {
        const reader = response.body.getReader();
        // ... stream processing
      });

    return () => {
      controller.abort();
    };
  }, [url]);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  return { data, cancel };
};
```

## 5. React 18+ Specific Optimizations

### **Automatic Batching**
React 18 automatically batches state updates, even in promises and timeouts:

```javascript
// All these updates are automatically batched in React 18+
const handleClick = () => {
  setCount(c => c + 1);
  setFlag(f => !f);
  setData(d => [...d, 'new']);
  // Only one re-render happens
};
```

### **useDeferredValue for Expensive Rendering**
Defer expensive UI updates:

```javascript
function SearchResults({ query }) {
  const [results, setResults] = useState([]);
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    search(deferredQuery).then(setResults);
  }, [deferredQuery]); // Debounced updates

  return (
    <div>
      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
      />
      {results.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}
```

## Decisions Made

### Decision 1: Use useReducer for Chat State Management
**Rationale**: The chat widget has complex state with multiple interrelated properties (messages, streaming status, thinking state). Using useReducer will consolidate this into a single state update, preventing multiple re-renders.

**Alternatives considered**:
- Multiple useState hooks: Causes cascade of re-renders
- External state library (Redux/Zustand): Overkill for this scope

### Decision 2: Split Chat Context into State and Actions
**Rationale**: Components that only need to trigger actions (like input components) shouldn't re-render when messages change.

**Alternatives considered**:
- Single context with all values: Causes unnecessary re-renders
- Prop drilling: Complex for deeply nested components

### Decision 3: Use useTransition for Streaming Updates
**Rationale**: Streaming responses can arrive rapidly. useTransition will batch updates and prevent UI blocking.

**Alternatives considered**:
- Direct state updates: Can cause UI jank
- Manual debouncing: More complex implementation

### Decision 4: Stabilize Callbacks with Updater Functions
**Rationale**: Many callbacks in the chat widget can use functional updates to avoid dependency arrays entirely.

**Alternatives considered**:
- useCallback with dependencies: Still causes re-creation
- Inline functions: Always re-renders

### Decision 5: Use useRef for Streaming ID
**Rationale**: The current streaming message ID changes frequently but callbacks need stable access to it.

**Alternatives considered**:
- Include in state: Causes re-renders
- Pass as prop: Complex prop drilling

## Technology Choices

**Language/Version**: TypeScript 5.0+ (matches existing codebase)
**Primary Dependencies**: React 18+, Framer Motion, React Markdown
**Testing**: Jest + React Testing Library
**Target Platform**: Web (Chrome, Firefox, Safari, Edge - last 2 versions)
**Performance Goals**: <20ms render time, 60fps animations
**Constraints**: <50MB memory usage, zero browser crashes
**Scale/Scope**: Single chat widget instance per page