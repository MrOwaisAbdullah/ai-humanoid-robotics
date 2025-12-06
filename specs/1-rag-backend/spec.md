# Feature Specification: RAG Backend API

**Feature Branch**: `1-rag-backend`
**Created**: 2025-01-05
**Status**: Draft
**Input**: Use the `rag-pipeline-builder` skill to generate a production-ready RAG Backend API for our book.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Book Content Ingestion (Priority: P1)

As a system administrator, I need to ingest the entire "Physical AI & Humanoid Robotics" book content (Markdown files) into the RAG system so that users can ask questions about the book content.

**Why this priority**: This is foundational - without ingested content, the chatbot cannot answer any questions about the book.

**Independent Test**: Can be tested by running the ingestion endpoint and verifying that chunks are stored in the vector database with correct metadata.

**Acceptance Scenarios**:

1. **Given** a directory containing book Markdown files, **When** the ingestion endpoint is called, **Then** all files are processed and stored as vector embeddings
2. **Given** previously ingested content, **When** ingestion runs again, **Then** duplicate chunks are identified and skipped
3. **Given** an ingestion failure, **When** an error occurs, **Then** a detailed error message is returned with the file that failed

---

### User Story 2 - Real-time Chat with Book (Priority: P1)

As a reader, I need to ask questions about the book content through a chat interface and receive relevant, context-aware answers streamed in real-time so that I can get immediate help understanding complex topics.

**Why this priority**: This is the core value proposition - users want instant answers about the book content.

**Independent Test**: Can be tested by sending questions to the chat endpoint and verifying responses are relevant to the book content and streamed properly.

**Acceptance Scenarios**:

1. **Given** ingested book content, **When** a user asks a question, **Then** the system streams relevant answer chunks in real-time
2. **Given** an ambiguous question, **When** processed, **Then** the system asks for clarification or provides the most likely interpretation
3. **Given** multiple relevant passages, **When** generating an answer, **Then** the response synthesizes information from multiple sources

---

### User Story 3 - Content Management (Priority: P2)

As a system administrator, I need to trigger content re-ingestion and monitor the system health so that the knowledge base stays up-to-date with any book updates.

**Why this priority**: Important for maintaining content accuracy but doesn't block initial deployment.

**Independent Test**: Can be tested by calling the ingest endpoint with updated content and verifying new chunks replace old ones.

**Acceptance Scenarios**:

1. **Given** updated book content, **When** re-ingestion is triggered, **Then** outdated chunks are replaced with new ones
2. **Given** system health monitoring, **When** checking status, **Then** ingestion statistics and vector database health are returned

---

### Edge Cases

- What happens when the vector database connection is lost?
- How does system handle very long documents (>10,000 words)?
- How are concurrent ingestion requests handled?
- What happens when OpenAI API rate limits are hit?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest Markdown files from a specified directory structure
- **FR-002**: System MUST split text into semantically meaningful chunks using LangChain-free approach
- **FR-003**: System MUST generate vector embeddings using OpenAI's text-embedding-3-small model
- **FR-004**: System MUST store vectors in Qdrant with metadata including source file and chunk position
- **FR-005**: System MUST provide a `/chat` endpoint supporting Server-Sent Events (SSE)
- **FR-006**: System MUST retrieve relevant chunks based on semantic similarity
- **FR-007**: System MUST generate contextual answers using OpenAI GPT-4 with retrieved context
- **FR-008**: System MUST stream responses character-by-character via SSE
- **FR-009**: System MUST include source citations in responses
- **FR-010**: System MUST support re-ingestion to update content
- **FR-011**: System MUST configure CORS to allow https://mrowaisabdullah.github.io
- **FR-012**: System MUST handle ingestion errors gracefully with detailed error messages
- **FR-013**: System MUST validate API keys before making external API calls
- **FR-014**: System MUST implement proper async/await patterns for all I/O operations

### Key Entities

- **Document**: Represents a source Markdown file with metadata (path, title, last modified)
- **Chunk**: A semantic piece of text with embedding vector, source reference, and position
- **Conversation Context**: Temporary storage of last 3 messages for follow-up context
- **Message**: Individual user query or system response with citations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive chat responses within 3 seconds of sending a query
- **SC-002**: System processes a 100-page book in under 2 minutes during ingestion
- **SC-003**: 95% of responses include relevant citations from the source material
- **SC-004**: Chat responses are rated as helpful by 85% of users in feedback surveys
- **SC-005**: System maintains 99.5% uptime with zero data loss during re-ingestion
- **SC-006**: API supports 100 concurrent chat users without response degradation
- **SC-007**: Vector search returns relevant results within 100ms for 90% of queries

## Technical Constraints

- **TC-001**: Must deploy to Hugging Face Spaces using Docker
- **TC-002**: Must expose port 7860 (not 8000)
- **TC-003**: Must run as non-root user with ID 1000
- **TC-004**: Must use FastAPI with async/await throughout
- **TC-005**: Must NOT use LangChain - implement pure Python chunking
- **TC-006**: Must use OpenAI embeddings and chat models
- **TC-007**: Must use Qdrant as vector database
- **TC-008**: Must implement streaming via Server-Sent Events

## Dependencies

- **D-001**: OpenAI API key for embeddings and chat
- **D-002**: Qdrant instance (URL and API key)
- **D-003**: Book content in Markdown format
- **D-004**: Docker runtime environment
- **D-005**: Hugging Face Spaces platform

## Clarifications

### Session 2025-01-05
- Q: Authentication & Access Control → A: Public access with optional API key for higher rate limits
- Q: Citation Display Format in SSE Stream → A: Embedded citations in markdown format with brackets [source]
- Q: Conversation State Management → A: Short-term memory (keep last 3 messages for context)

## Assumptions

- Book content is available in Markdown format with clear section headings
- OpenAI API has sufficient rate limits for expected usage
- Qdrant instance is properly configured and accessible
- Frontend will handle SSE response parsing
- Users have basic familiarity with chat interfaces