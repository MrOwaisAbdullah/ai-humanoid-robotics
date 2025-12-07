# Implementation Plan: Advanced Chatbot UI with Text Selection Integration

**Feature**: 003-chat-ui
**Created**: 2025-12-06
**Status**: Draft
**Based on**: [spec.md](./spec.md)

## 1. Architecture and Technology Stack

### 1.1 Component Architecture

```
src/components/ChatWidget/
├── ChatWidgetContainer.tsx      # Main container with state management
├── components/
│   ├── ChatInterface.tsx       # Core chat UI (messages, input)
│   ├── MessageRenderer.tsx     # Markdown + syntax highlighting
│   ├── WelcomeScreen.tsx       # Initial screen with suggestions
│   ├── ThinkingIndicator.tsx   # Pulsing animation during processing
│   ├── StreamingCursor.tsx     # Blinking cursor during streaming
│   ├── InputArea.tsx           # Capsule-style input with send button
│   ├── SourceBadge.tsx         # Clickable source citations
│   └── SelectionTooltip.tsx    # "Ask AI" tooltip for text selection
├── hooks/
│   ├── useChatSession.ts       # Chat state management
│   ├── useStreamingResponse.ts # SSE handling for streaming
│   └── useTextSelection.ts     # Global text selection detection
├── utils/
│   ├── animations.ts           # Framer Motion configurations
│   ├── markdown.ts             # Custom markdown renderers
│   └── positioning.ts          # Tooltip positioning logic
└── styles/
    ├── ChatWidget.module.css   # Component-specific styles
    └── animations.css          # Animation keyframes
```

### 1.2 Technology Stack

- **React 18+**: With hooks and concurrent features
- **TypeScript**: For type safety and better development experience
- **Framer Motion**: For smooth animations and transitions
- **react-markdown**: For markdown rendering with custom components
- **react-syntax-highlighter**: For code block syntax highlighting
- **Tailwind CSS**: For styling and responsive design
- **React Portals**: For rendering SelectionTooltip outside component hierarchy

## 2. State Management Strategy

### 2.1 Chat Session State

```typescript
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: SourceCitation[];
  isStreaming?: boolean;
}

interface ChatSession {
  messages: ChatMessage[];
  isOpen: boolean;
  isThinking: boolean;
  currentStreamingId?: string;
}
```

### 2.2 Text Selection State

```typescript
interface TextSelectionState {
  selectedText: string;
  rect: DOMRect;
  isVisible: boolean;
}
```

### 2.3 State Implementation

- Use `useReducer` for complex chat state logic
- Use `useContext` to share chat state across components
- Implement optimistic updates for better UX
- Maintain session state in React memory only (no persistence)

## 3. Component Design Details

### 3.1 ChatWidgetContainer

**Responsibilities**:
- Main state management and orchestration
- Portal creation for SelectionTooltip
- Global text selection listener setup
- API integration for chat messages

**Key Features**:
- Renders ChatInterface and SelectionTooltip
- Manages chat session lifecycle
- Handles SSE connection for streaming
- Coordinates text selection detection

### 3.2 MessageRenderer

**Responsibilities**:
- Render markdown content with custom components
- Display source citations as clickable badges
- Handle code syntax highlighting
- Manage link rendering with external URL handling

**Implementation**:
```typescript
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

const MessageRenderer: React.FC<{ message: ChatMessage }> = ({ message }) => {
  // Custom renderers for different markdown elements
  // Source badge integration
  // Click handlers for URLs
};
```

### 3.3 Text Selection Hook

**Responsibilities**:
- Detect text selections globally
- Calculate optimal tooltip position
- Handle edge cases (screen boundaries, overlapping elements)
- Manage tooltip visibility

**Implementation Strategy**:
- Use `document.addEventListener('selectionchange')`
- Calculate position relative to viewport
- Implement collision detection for screen edges
- Debounce rapid selection changes

## 4. Animation Design

### 4.1 Animation Components

**Widget Open/Close**:
- Scale and fade transition
- Duration: 300ms
- Easing: cubic-bezier(0.4, 0, 0.2, 1)

**Message Entry**:
- Slide up with fade
- Stagger for multiple messages
- Duration: 200ms per message

**Streaming Cursor**:
- Blink animation: 1s cycle
- Smooth character-by-character reveal
- No layout shifts during streaming

**Thinking Indicator**:
- Pulsing dot animation
- 3-dot sequence with stagger
- Smooth fade in/out

### 4.2 Performance Optimizations

- Use `useMemo` for expensive animation calculations
- Implement `will-change` properties for GPU acceleration
- Batch DOM updates during streaming
- Use CSS transforms instead of layout properties

## 5. Integration with Existing System

### 5.1 Docusaurus Integration

**Approach**:
- Create a custom theme component in `src/theme/Root.tsx`
- Use Docusaurus's `useThemeConfig` to access site configuration
- Integrate with existing color scheme (dark mode)
- Respect user's font size preferences

**Root Component Update**:
```typescript
// src/theme/Root.tsx
import React from 'react';
import Root from '@theme-original/Root';
import ChatWidgetContainer from '../components/ChatWidget/ChatWidgetContainer';

export default function RootWithChat(props: any): JSX.Element {
  return (
    <>
      <ChatWidgetContainer />
      <Root {...props} />
    </>
  );
}
```

### 5.2 Backend API Integration

**Streaming Endpoint**:
- Use existing SSE endpoint at `/api/chat/stream`
- Send selected text as context when available
- Handle connection errors and retries
- Implement proper cleanup on component unmount

**Request Format**:
```typescript
interface ChatRequest {
  message: string;
  context?: {
    selectedText: string;
    source: string; // Chapter/section info
  };
  stream: boolean;
}
```

## 6. Implementation Phases

### Phase 1: Foundation (P1 Features)
1. **ChatWidgetContainer** - Basic structure and state management
2. **ChatInterface** - Message display and input
3. **API Integration** - Basic streaming functionality
4. **Root Integration** - Connect to Docusaurus theme

### Phase 2: Enhanced Rendering (P1 Features)
1. **MessageRenderer** - Markdown support
2. **Syntax Highlighting** - Code block rendering
3. **Source Badges** - Citation display
4. **Basic Animations** - Widget open/close

### Phase 3: Text Selection (P1 Features)
1. **useTextSelection** - Selection detection hook
2. **SelectionTooltip** - "Ask AI" tooltip
3. **Context Injection** - Pre-fill with selected text
4. **Positioning Logic** - Smart tooltip placement

### Phase 4: Polish (P2 Features)
1. **Advanced Animations** - Message entry, streaming cursor
2. **Thinking Indicator** - Processing state animation
3. **Welcome Screen** - Suggestion chips
4. **Performance Optimization** - Memory and CPU optimization

## 7. Risk Analysis and Mitigation

### 7.1 Technical Risks

**Risk**: Text selection conflicts with existing browser behavior
**Mitigation**: Implement proper event handling and fallback positioning

**Risk**: Performance impact of global selection listener
**Mitigation**: Use passive event listeners and efficient debouncing

**Risk**: Animation performance on low-end devices
**Mitigation**: Implement `prefers-reduced-motion` support and GPU acceleration

**Risk**: Markdown rendering security (XSS)
**Mitigation**: Use react-markdown's built-in sanitization and custom sanitizers

### 7.2 Integration Risks

**Risk**: Conflicts with existing Docusaurus theme
**Mitigation**: Proper namespacing and minimal global styles

**Risk**: SSE connection issues in production
**Mitigation**: Robust error handling and reconnection logic

## 8. Testing Strategy

### 8.1 Unit Tests
- Custom hooks (useChatSession, useTextSelection)
- Utility functions (positioning, markdown processing)
- Component rendering with different props

### 8.2 Integration Tests
- End-to-end chat flow
- Text selection to chat context injection
- API integration with mock streaming
- Responsive behavior across screen sizes

### 8.3 Performance Tests
- Animation frame rate monitoring
- Memory usage during long conversations
- Text selection performance on large pages

## 9. Success Metrics

### 9.1 Performance Targets
- Initial render: < 200ms
- Animation frame rate: 60fps
- Memory usage: < 50MB for chat components
- Text selection response: < 100ms

### 9.2 User Experience Targets
- Chatbot open time: < 500ms
- Message streaming: smooth without lag
- Text selection accuracy: 95%
- Mobile responsiveness: 100% feature parity

## 10. Dependencies and Prerequisites

### 10.1 Required Dependencies
```json
{
  "framer-motion": "^10.16.4",
  "react-markdown": "^9.0.1",
  "react-syntax-highlighter": "^15.5.0",
  "@types/react-syntax-highlighter": "^15.5.7"
}
```

### 10.2 External Dependencies
- Existing backend SSE API
- Tailwind CSS configuration
- Docusaurus theme customization

## 11. Architectural Decision Records (ADRs)

### ADR-001: State Management Approach
**Decision**: Use React hooks (useReducer + useContext) instead of external state management
**Rationale**:
- Keeps chatbot self-contained
- No additional dependencies
- Easier integration with Docusaurus
- Sufficient for current complexity

### ADR-002: Animation Library Choice
**Decision**: Use Framer Motion instead of CSS-only animations
**Rationale**:
- Better performance with GPU acceleration
- Easier to orchestrate complex animations
- Better accessibility support
- Maintains animation state automatically

### ADR-003: Text Selection Detection Strategy
**Decision**: Use global document listener instead of individual component listeners
**Rationale**:
- Works across all content without modifying each component
- Single source of truth for selection state
- Easier to manage lifecycle and cleanup
- Better performance with delegation

## 12. Implementation Checklist

- [ ] Set up project structure and TypeScript configuration
- [ ] Install required dependencies (framer-motion, react-markdown, etc.)
- [ ] Create ChatWidgetContainer with basic state management
- [ ] Implement ChatInterface component
- [ ] Add streaming API integration
- [ ] Create MessageRenderer with markdown support
- [ ] Implement syntax highlighting for code blocks
- [ ] Add source badge components
- [ ] Create useTextSelection hook
- [ ] Implement SelectionTooltip with portal
- [ ] Add basic animations (open/close, message entry)
- [ ] Implement thinking indicator
- [ ] Add streaming cursor effect
- [ ] Create welcome screen with suggestions
- [ ] Integrate with Docusaurus theme
- [ ] Add responsive design support
- [ ] Implement error boundaries and fallbacks
- [ ] Add accessibility features (ARIA labels, keyboard navigation)
- [ ] Performance optimization and testing
- [ ] Documentation and code comments