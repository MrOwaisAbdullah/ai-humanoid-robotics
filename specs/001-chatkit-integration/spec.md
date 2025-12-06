# Feature Specification: ChatKit Integration

**Feature Branch**: `001-chatkit-integration`
**Created**: 2025-01-05
**Status**: Draft
**Input**: User description: "create spec for chatbot integrating our previously created backend to the chatbot using, subagents and skills, Use the `chatbot-widget-creator` skill to integrate the OpenAI ChatKit widget into our Docusaurus frontend"

## Clarifications

### Session 2025-01-05
- Q: Authentication model for chat access? → A: Optional authentication - users can optionally create accounts for session persistence
- Q: Backend connection protocol for streaming? → A: Server-Sent Events (SSE) - server pushes updates to client
- Q: Chat session persistence method? → A: LocalStorage persistence (survives browser reload)
- Q: Text selection scope for "Ask AI"? → A: All text content on book pages (including code, captions)
- Q: Mobile chat presentation style? → A: Overlay with draggable handle

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Chat Widget (Priority: P1)

User visits the Physical AI & Humanoid Robotics book website and sees a floating chat button in the bottom-right corner. When clicked, a chat window opens with a pre-configured greeting message. The user can type questions about the book content and receive AI-powered responses with citations to relevant sections.

**Why this priority**: This is the core functionality that provides immediate value to users seeking answers about the book content.

**Independent Test**: Can be fully tested by opening the chat widget, asking a question about the book, and verifying that the response includes relevant citations from the book content.

**Acceptance Scenarios**:

1. **Given** the book website is loaded, **When** the user clicks the floating chat button, **Then** a chat window opens with a greeting message "Hello! I'm your AI assistant for the Physical AI & Humanoid Robotics book. How can I help you today?"
2. **Given** the chat window is open, **When** the user asks "What is forward kinematics?", **Then** the system responds with an answer about forward kinematics and includes citations like [Chapter 3 - Kinematics](source)
3. **Given** no messages have been sent, **When** the user types their first message, **Then** a new session is created and the session ID is maintained for the conversation

---

### User Story 2 - Text Selection & Context (Priority: P2)

User is reading a specific section of the book and highlights a text snippet (e.g., a paragraph about Jacobian matrices). A small "Ask AI about this" button appears near the selection. When clicked, it opens the chat widget with the selected text pre-populated as context, allowing the user to ask specific questions about the highlighted content.

**Why this priority**: This enhances the learning experience by allowing users to get immediate explanations for specific content they're reading.

**Independent Test**: Can be tested by highlighting any text on the page and verifying the "Ask AI about this" button appears and properly pre-fills the chat context.

**Acceptance Scenarios**:

1. **Given** the user is viewing any book page, **When** they select/highlight text, **Then** an "Ask AI about this" button appears near the selection
2. **Given** text is selected, **When** the user clicks "Ask AI about this", **Then** the chat opens with a prompt like "Can you explain more about this highlighted text: [selected text]?"
3. **Given** the chat is opened with selected text, **When** the user sends the message, **Then** the AI response specifically references the highlighted content and provides additional context

---

### User Story 3 - Glassmorphism Styling (Priority: P3)

The chat widget matches the modern design of the Docusaurus site with glassmorphism effects - frosted glass appearance with subtle blur, transparency, and a modern color palette that complements the site theme.

**Why this priority**: Visual consistency and modern aesthetics enhance user experience and professional appearance.

**Independent Test**: Can be verified by visual inspection of the chat widget to ensure it matches the glassmorphism design requirements.

**Acceptance Scenarios**:

1. **Given** the chat widget is displayed, **When** viewed on any page, **Then** it has a frosted glass appearance with backdrop blur effect
2. **Given** the chat window is open, **When** content scrolls behind it, **Then** the background content is visible through the glassmorphism effect
3. **Given** the widget is displayed, **When** viewed in light and dark modes, **Then** the styling adapts appropriately to both themes

---

### Edge Cases

- What happens when the backend API is unavailable or returns an error?
- How does system handle very long text selections (over 1000 characters)?
- How does the chat widget behave on mobile devices with limited screen space?
- What happens when a user's session expires during an active conversation?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a floating chat button on all book pages
- **FR-002**: System MUST open a chat window when the chat button is clicked
- **FR-003**: System MUST integrate with OpenAI ChatKit using @openai/chatkit-react library
- **FR-004**: System MUST fetch ChatKit client_secret from backend `/api/chatkit/session` endpoint
- **FR-005**: System MUST configure ChatKit with OpenAI API for streaming responses
- **FR-006**: System MUST render citations as clickable links using the format provided by the RAG backend
- **FR-007**: System MUST detect text selection on all book content (including code blocks, captions, and side notes) and display "Ask AI about this" button
- **FR-008**: System MUST pre-fill chat context with selected text when using "Ask AI about this"
- **FR-009**: System MUST maintain conversation session ID across multiple messages
- **FR-010**: System MUST apply glassmorphism styling with CSS properties: backdrop-filter: blur(20px), background: rgba(255, 255, 255, 0.08), and border: 1px solid rgba(255, 255, 255, 0.2) to all chat components
- **FR-011**: System MUST be responsive on mobile devices (< 768px) with full-screen overlay presentation, smooth slide-up animation (300ms ease-out), and a draggable handle at the top for closing the chat panel
- **FR-012**: System MUST display appropriate error messages when the backend is unavailable
- **FR-013**: System MAY provide optional user identification for enhanced LocalStorage session management (no backend authentication required)
- **FR-014**: System MUST persist chat session in LocalStorage to survive browser reloads within the same browser (persistence is per-browser, not cross-browser)

### Key Entities

- **ChatSession**: Represents a conversation between user and AI, includes session_id and message history
- **Message**: Individual chat message with content, role (user/assistant), timestamp, and optional citations
- **Citation**: Reference to book content with chapter, section, and link information
- **TextSelection**: Highlighted text content with position information for "Ask AI about this" feature

## Dependencies

### System Dependencies
- **D-001**: OpenAI API key for ChatKit sessions and chat completions
- **D-002**: Existing FastAPI backend for ChatKit session management
  - New endpoint: `/api/chatkit/session` (returns client_secret)
  - Existing endpoint: `http://localhost:7860/chat` (for RAG functionality)
- **D-003**: Qdrant cloud instance (configured in backend)
- **D-004**: Book content already ingested into vector database (25 chunks from 2 documents)
- **D-005**: Node.js 18+ and npm/yarn package manager
- **D-006**: @openai/chatkit-react library for UI components

### External Services
- **S-001**: OpenAI ChatKit API for managed chat sessions and streaming
- **S-002**: Backend API for ChatKit session endpoint (/api/chatkit/session)
- **S-003**: RAG Backend API for book content queries (port 7860)
- **S-004**: OpenAI API for embeddings and chat completions (handled by backend)
- **S-005**: Qdrant vector database for semantic search (handled by backend)

### Related Specifications
- **RAG Backend**: [specs/1-rag-backend/spec.md](../1-rag-backend/spec.md) - Contains detailed API contract for `/chat` endpoint, SSE streaming format, and citation handling

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Chat widget loads in under 2 seconds on standard broadband connection
- **SC-002**: AI responses begin streaming within 3 seconds of message submission
- **SC-003**: 95% of user questions receive relevant responses with proper citations
- **SC-004**: Text selection feature works on 100% of book content pages
- **SC-005**: Chat widget maintains full functionality on mobile devices with screen sizes as small as 320px wide
- **SC-006**: User satisfaction score of 4.5/5 or higher in post-interaction surveys
- **SC-007**: Average session duration of 3+ minutes indicates engaging interactions
- **SC-008**: Glassmorphism styling scores 8/10 or higher in visual design evaluations
