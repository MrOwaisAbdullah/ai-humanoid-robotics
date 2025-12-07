# Implementation Plan: Fix Infinite Re-render Bug in Chat Widget

**Branch**: `001-fix-rerender` | **Date**: 2025-12-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-fix-rerender/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The infinite re-render bug in the chat widget is caused by three main issues:
1. Circular callback dependencies where `handleChunk` depends on `session.currentStreamingId`
2. Overlapping streaming systems (`useChatSession` and `useStreamingResponse`)
3. Unstable context references causing the entire context to re-create on each render

**Technical Approach**: Consolidate state management using `useReducer`, split context for performance, and stabilize all callback references using updater functions and refs.

## Technical Context

**Language/Version**: TypeScript 5.0+
**Primary Dependencies**: React 18+, Framer Motion, react-markdown, react-syntax-highlighter
**Storage**: In-memory only (no persistence)
**Testing**: Jest + React Testing Library + React DevTools Profiler
**Target Platform**: Web (Chrome, Firefox, Safari, Edge - last 2 major versions)
**Project Type**: Web application (React component optimization)
**Performance Goals**: <20ms render time, 60fps animations, zero re-render loops
**Constraints**: <50MB memory usage, 10,000 character message limit, 100% crash-free rate
**Scale/Scope**: Single chat widget instance per page, supporting concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### SOLID Principles Compliance

1. **Single Responsibility Principle (SRP)** ✅
   - Each hook will have a single responsibility
   - Separating streaming logic from state management
   - Context split into state vs actions

2. **Open/Closed Principle (OCP)** ✅
   - Reducer pattern allows easy extension of chat actions
   - Components remain closed for modification but open for extension through props

3. **Dependency Inversion Principle (DIP)** ✅
   - Components depend on abstractions (context), not concrete implementations
   - Streaming implementation can be swapped without changing components

4. **Don't Repeat Yourself (DRY)** ✅
   - Consolidated state management eliminates duplicate logic
   - Single source of truth for all chat state

### Production-First Mindset ✅
- Error handling included in all async operations
- Performance metrics defined in success criteria
- Proper cleanup patterns for streams and event listeners

### Specification-First Development ✅
- Clear spec with measurable success criteria
- All requirements have acceptance criteria
- Scope clearly bounded to prevent scope creep

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-rerender/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output - React optimization patterns
├── data-model.md        # Phase 1 output - State management design
├── quickstart.md        # Phase 1 output - Implementation guide
├── contracts/           # Phase 1 output - API contracts
│   └── chat-api.md      # Streaming API specification
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created yet)
```

### Source Code (affected directories)

```text
src/components/ChatWidget/
├── ChatWidgetContainer.tsx      # Main container (requires refactoring)
├── hooks/
│   ├── useChatSession.tsx       # State management (consolidate)
│   ├── useStreamingResponse.ts  # Streaming logic (consolidate)
│   └── useErrorHandler.ts       # Error handling (existing)
├── components/
│   ├── ChatInterface.tsx        # UI component (optimize)
│   └── MessageRenderer.tsx      # Message display (optimize)
└── types/
    └── index.ts                 # Type definitions (update)

src/theme/Root.tsx              # Docusaurus integration (unchanged)
```

**Structure Decision**: Using existing ChatWidget directory structure with minimal changes to preserve Docusaurus integration. Focus is on internal refactoring rather than structural changes.

## Complexity Tracking

No constitution violations - all optimizations align with SOLID principles and project guidelines.

## Phase 0: Research Complete ✅

### Research Findings
- React 18+ automatic batching helps prevent multiple re-renders
- useTransition is ideal for streaming updates
- Splitting context significantly improves performance
- useReducer pattern consolidates complex state logic
- Updater functions eliminate dependency issues in useCallback

### Key Decisions from Research
1. Use `useReducer` instead of multiple `useState` hooks
2. Split context into separate state and actions contexts
3. Use `useRef` for frequently changing values needed in callbacks
4. Implement proper cleanup with AbortController for streams
5. Apply `useTransition` for non-blocking streaming updates

## Phase 1: Design Complete ✅

### Data Model Design
- Consolidated ChatState with all related properties
- Type-safe reducer actions for state updates
- Split context pattern for optimized re-renders
- Clear separation of concerns between state and actions

### API Contracts
- Server-Sent Events for streaming protocol
- Error handling with retry logic
- Rate limiting and validation rules
- Browser compatibility considerations

### Implementation Strategy
1. Refactor ChatWidgetContainer to use useReducer
2. Update ChatProvider with split context
3. Consolidate streaming logic into single hook
4. Stabilize all callback dependencies
5. Add performance monitoring

## Next Steps

The plan is complete with research and design phases finished. Ready to proceed with:
1. `/sp.tasks` to generate detailed implementation tasks
2. `/sp.implement` to execute the fix

All artifacts created:
- `research.md` - React optimization patterns and best practices
- `data-model.md` - State management design and interfaces
- `quickstart.md` - Step-by-step implementation guide
- `contracts/chat-api.md` - Streaming API specification