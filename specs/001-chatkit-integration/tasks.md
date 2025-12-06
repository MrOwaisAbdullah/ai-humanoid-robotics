# Implementation Tasks: ChatKit Integration

**Branch**: `001-chatkit-integration` | **Date**: 2025-01-05 | **Spec**: [specs/001-chatkit-integration/spec.md](spec.md)
**Plan**: [specs/001-chatkit-integration/plan.md](plan.md) | **Total Tasks**: 27

## Phase 1: Setup

**Goal**: Initialize the project and install required dependencies for ChatKit integration

**Note**:
- The RAG backend (branch: `1-rag-backend`) is already implemented with book content ingested (25 chunks from 2 documents)
- The backend provides the `/chat` endpoint with SSE streaming at port 7860
- We need to add a new `/api/chatkit/session` endpoint for ChatKit client_secret generation
- ChatKit will handle streaming internally using OpenAI's managed service

### Tasks

- [ ] T001 Install @openai/chatkit-react and dependencies in package.json
- [ ] T002 [P] Create ChatWidget component directory structure in src/components/ChatWidget/
- [ ] T003 Create types directory for TypeScript interfaces based on data model
- [ ] T004 [P] Create hooks directory for custom React hooks
- [ ] T005 [P] Create styles directory for glassmorphism CSS utilities

## Phase 2: Foundational

**Goal**: Implement core infrastructure and shared functionality

### Tasks

- [ ] T006 Create TypeScript interfaces for ChatSession, ChatMessage, Citation, and TextSelection in src/components/ChatWidget/types/
- [ ] T007 [P] Implement useSessionPersistence hook in src/components/ChatWidget/hooks/useSessionPersistence.ts
- [ ] T008 [P] Implement useChatKitSession hook for fetching client_secret from backend in src/components/ChatWidget/hooks/useChatKitSession.ts
- [ ] T009 [P] Create glassmorphism CSS utilities with backdrop-filter: blur(20px), background: rgba(255, 255, 255, 0.08), border: 1px solid rgba(255, 255, 255, 0.2) in src/styles/glassmorphism.css
- [ ] T010 Add environment variable configuration:
  - OPENAI_API_KEY for ChatKit sessions
  - CHATKIT_SESSION_ENDPOINT for client_secret fetching
  - CHAT_API_ENDPOINT for RAG backend (http://localhost:7860)

## Phase 3: User Story 1 - Basic Chat Widget (P1)

**Goal**: Provide a floating chat button and window with basic chat functionality

**Independent Test**: Open chat widget, ask a question about the book, verify response includes citations

### Tasks

- [ ] T011 [US1] Create ChatFloatingButton component in src/components/ChatWidget/ChatFloatingButton.tsx
- [ ] T012 [US1] Create ChatPanel component with glassmorphism styling in src/components/ChatWidget/ChatPanel.tsx
- [ ] T013 [US1] Implement main ChatWidget component with ChatKit integration in src/components/ChatWidget/index.tsx
- [ ] T014 [US1] Configure ChatKit with dark theme and custom placeholder text
- [ ] T015 [US1] Implement client_secret fetching from backend `/api/chatkit/session` endpoint
- [ ] T016 [US1] Configure ChatKit with OpenAI API key for managed streaming
- [ ] T017 [US1] Implement citation rendering as clickable links (format: [source] as provided by RAG backend)
- [ ] T018 [US1] Add error handling for backend unavailability
- [ ] T019 [US1] Add `/api/chatkit/session` endpoint to backend for client_secret generation
- [ ] T020 [US1] Integrate ChatWidget into Docusaurus theme in src/theme/Root.tsx

## Phase 4: User Story 2 - Text Selection & Context (P2)

**Goal**: Enable users to highlight text and ask questions about selected content

**Independent Test**: Highlight text, verify "Ask AI about this" button appears and pre-fills chat

### Tasks

- [ ] T021 [US2] Implement useTextSelection hook in src/components/ChatWidget/hooks/useTextSelection.ts
- [ ] T022 [US2] Add text selection event listeners with 300ms debounce
- [ ] T023 [US2] Create SelectionPopover component for "Ask AI about this" button
- [ ] T024 [US2] Position popover near text selection dynamically
- [ ] T025 [US2] Pre-fill chat message with selected text when popover is clicked
- [ ] T026 [US2] Filter selections to exclude those within chat widget

## Phase 5: User Story 3 - Glassmorphism Styling (P3)

**Goal**: Apply modern glassmorphism effects to all chat components

**Independent Test**: Visual inspection of chat widget for frosted glass appearance and theme adaptation

### Tasks

- [ ] T026 [US3] Apply backdrop-blur and rgba backgrounds to ChatPanel
- [ ] T028 [US3] Add glassmorphism effects to floating button and popover
- [ ] T029 [US3] Implement theme-aware glassmorphism (light/dark mode support)
- [ ] T030 [US3] Add subtle animations and transitions for smooth interactions

## Phase 6: Mobile Responsiveness

**Goal**: Ensure chat widget works properly on mobile devices with overlay presentation

### Tasks

- [ ] T030 Add mobile-specific CSS with media queries for screens < 768px
- [ ] T031 Implement full-screen overlay presentation on mobile with slide-up animation (300ms ease-out)
- [ ] T032 Add draggable handle at top of mobile chat panel with smooth closing animation
- [ ] T033 Ensure touch-friendly target sizes (minimum 44px)
- [ ] T034 Prevent zoom on iOS with font-size: 16px for input fields

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Finalize implementation with performance optimizations and accessibility

### Tasks

- [ ] T035 Implement LocalStorage history pruning (keep last 50 messages)
- [ ] T036 Add loading states and connection status indicators
- [ ] T037 Implement automatic reconnection logic for ChatKit session drops
- [ ] T038 Add keyboard navigation support
- [ ] T039 Ensure WCAG AA compliance with proper ARIA labels
- [ ] T040 Add performance monitoring and error logging
- [ ] T041 Create documentation in README.md with setup instructions

## Dependencies

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
```

**Critical Path**: Phase 3 (US1) must be completed before Phase 4 (US2) and Phase 5 (US3)
- Phase 4 and Phase 5 can be developed in parallel after Phase 3
- Phase 6 (Mobile) depends on Phase 3, 4, and 5 for complete functionality
- Phase 7 (Polish) runs after all user stories are implemented

## Parallel Execution Opportunities

### Within User Story 1 (Phase 3)
- T011, T012, T013: Component creation (can be done in parallel)
- T016, T017: Streaming and citations (can be done in parallel)

### Within User Story 2 (Phase 4)
- T020, T021, T022: Hook and popover (sequential dependency)
- T023, T024, T025: Positioning and integration (can be done in parallel)

### Cross-Story Parallelism
- Phase 4 (US2) and Phase 5 (US3) can be developed in parallel after Phase 3
- Mobile responsiveness (Phase 6) can start once basic components exist

## Implementation Strategy

### MVP Scope (First Release)
Complete Phase 1, 2, and 3 to deliver basic chat functionality:
- Floating chat button
- Basic chat window
- Streaming responses
- Citation display
- Session persistence

### Incremental Delivery
1. **Week 1**: Phase 1-3 (Basic chat)
2. **Week 2**: Phase 4 (Text selection)
3. **Week 3**: Phase 5-7 (Styling, mobile, polish)

### Testing Strategy
- Unit tests for hooks (T007, T008, T020)
- Component tests for UI components
- Integration tests for end-to-end flows
- Visual regression tests for glassmorphism effects

## Success Criteria

Each phase is complete when:
- All tasks in the phase are checked off
- Independent test criteria for the user story are met
- Code passes linting and type checking
- Documentation is updated
- Performance targets are met (2s load, <100ms streaming)