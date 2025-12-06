# Research Findings: ChatKit Integration

## Key Decisions

### 1. ChatKit SDK Selection
**Decision**: Use `@openai/chatkit-react` v4.0+ with TypeScript support
**Rationale**:
- Official React SDK from OpenAI with built-in SSE support
- Full TypeScript definitions available
- Optimized for streaming responses
- Includes pre-built UI components that can be customized

### 2. Streaming Architecture
**Decision**: Server-Sent Events (SSE) for streaming responses
**Rationale**:
- Backend already implements SSE in `/chat` endpoint
- ChatKit has native SSE support
- Simpler than WebSockets for one-way streaming
- Better for mobile battery life

### 3. Session Persistence
**Decision**: LocalStorage for chat history and session state
**Rationale**:
- No authentication required (as clarified in spec)
- Survives browser reloads
- Simple client-side implementation
- Aligns with FR-014 requirement

### 4. Styling Approach
**Decision**: Tailwind CSS utility classes with custom glassmorphism effects
**Rationale**:
- Docusaurus already uses Tailwind CSS
- Glassmorphism achieved via backdrop-blur and rgba colors
- Responsive design built-in
- Matches modern design requirements

## Dependencies

### Frontend
```bash
npm install @openai/chatkit-react@latest
npm install framer-motion@latest
npm install lucide-react@latest
```

### Backend (Already installed)
- FastAPI with SSE support
- OpenAI SDK for embeddings
- Qdrant client for vector search

## Integration Patterns

### Text Selection Detection
- Use native `window.getSelection()` API
- Debounce selection events (300ms)
- Minimum selection length: 3 characters
- Works on all text content including code blocks

### Glassmorphism Implementation
- CSS backdrop-filter: blur(12px)
- Semi-transparent backgrounds (rgba values)
- Border with rgba(255,255,255,0.1-0.2)
- Multiple box-shadows for depth

### Mobile Responsiveness
- Overlay presentation with draggable handle
- Full-screen chat on mobile (< 768px)
- Touch-friendly targets (44px minimum)
- Prevent zoom on iOS with font-size: 16px

### Component Architecture
```
ChatWidget/
├── index.tsx          # Main widget with ChatKit integration
├── ChatFloatingButton.tsx  # Floating action button
├── ChatPanel.tsx      # Glassmorphism-styled panel
└── hooks/
    ├── useTextSelection.ts
    ├── useSessionPersistence.ts
    └── useSSEStream.ts
```

## Alternatives Considered

1. **WebSocket vs SSE**: Chose SSE for simplicity and better mobile performance
2. **Custom Chat UI vs ChatKit**: Chose ChatKit for proven streaming patterns
3. **Redux vs Local State**: Chose LocalStorage for persistence without complexity
4. **CSS Modules vs Tailwind**: Chose Tailwind for consistency with Docusaurus

## Implementation Notes

1. ChatKit requires a client secret from backend endpoint
2. SSE events must be formatted as JSON chunks
3. Glassmorphism effects may need WebKit prefixes for some browsers
4. Text selection must be filtered to exclude selections within the chat widget itself