# Feature Specification: RAG Embedding System Fix

**Feature Branch**: `002-rag-embedding-fix`
**Created**: 2025-12-06
**Status**: Draft
**Input**: User description: "Our rag embedding is not working correctly we have to implement is correctly using the latest docs, using context 7 mcp and web search, currently this is what its saying, hi, can you tell me about this book Based on the context provided from [Source 1] to [Source 5], it appears that each source repeats the title "How to Use This Book" but does not provide further details or content about the book itself. Unfortunately, without additional information on the book's topics, themes, authors, or specific content beyond the repeated title section, I am unable to provide a detailed description or insights about the book in question. If you have specific questions or topics from the book you're interested in, please provide more details so I can assist you better. we have to make the plan to solve this problems"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate Book Content Retrieval (Priority: P1)

As a user chatting with the AI assistant about the book, I want to receive specific, relevant answers about the book's content instead of generic "How to Use This Book" responses, so that I can get valuable information about the book's topics.

**Why this priority**: This is the core functionality issue - users cannot get any value from the RAG system when it returns generic template responses instead of actual content.

**Independent Test**: Can be fully tested by asking a specific question about book content and verifying the response contains actual book information rather than template text.

**Acceptance Scenarios**:

1. **Given** the book content has been ingested into the vector store, **When** a user asks "What topics does this book cover?", **Then** the system returns specific topics from the book content
2. **Given** the RAG system is queried, **When** retrieving context, **Then** it should not return "How to Use This Book" template text
3. **Given** a user asks about a specific concept in the book, **When** processing the query, **Then** the response includes relevant passages from the actual book content

---

### User Story 2 - Proper Document Ingestion (Priority: P1)

As a system administrator, I want to successfully ingest book documents into the vector database with proper chunking, so that the RAG system can retrieve relevant content.

**Why this priority**: Without proper ingestion, the vector store is empty or contains only template text, making the entire RAG system non-functional.

**Independent Test**: Can be fully tested by running the ingestion process and verifying that chunks are created and stored in the vector database.

**Acceptance Scenarios**:

1. **Given** book content files exist in the content directory, **When** the ingestion endpoint is called, **Then** documents are successfully chunked and stored
2. **Given** the ingestion process completes, **When** checking the health endpoint, **Then** chunks_count reflects the actual number of content chunks
3. **Given** documents are ingested, **When** querying the vector store, **Then** it returns relevant content chunks, not template text

---

### User Story 3 - Optimal Similarity Scoring (Priority: P2)

As a user, I want the RAG system to retrieve context using appropriate similarity thresholds, so that I get relevant responses that match my questions.

**Why this priority**: The current low threshold (0.3) allows irrelevant content to be retrieved, contributing to poor response quality.

**Independent Test**: Can be tested by querying with questions that should have no good matches and verifying the system handles this appropriately.

**Acceptance Scenarios**:

1. **Given** a user query, **When** searching for similar content, **Then** only content with similarity score above 0.7 is retrieved
2. **Given** no content meets the similarity threshold, **When** processing a query, **Then** the system responds appropriately rather than returning low-quality matches
3. **Given** multiple content chunks exceed the threshold, **When** retrieving context, **Then** the most relevant chunks are selected based on similarity scores

---

### Edge Cases

- What happens when the book content directory is empty or missing?
- How does the system handle queries about topics not covered in the book?
- What occurs when embedding generation fails due to API issues?
- How does the system handle malformed markdown files during ingestion?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest book content from markdown files into the vector database with proper chunking
- **FR-002**: System MUST use token-based chunking with 600 tokens per chunk and 100 token overlap for better semantic representation (based on research.md findings)
- **FR-003**: System MUST implement a similarity score threshold of 0.7 for content retrieval
- **FR-004**: System MUST exclude template/generic content (like "How to Use This Book") from being ingested
- **FR-005**: System MUST validate that content exists in the vector store before processing queries
- **FR-006**: System MUST provide clear error messages when no relevant content is found
- **FR-007**: System MUST support re-ingestion with force_reindex option to update content
- **FR-008**: System MUST use the latest OpenAI embedding model (text-embedding-3-small or text-embedding-3-large)
- **FR-009**: System MUST use SHA256 content hashing to detect and filter duplicate chunks during retrieval

### Key Entities *(include if feature involves data)*

- **DocumentChunk**: A segment of book content (600 tokens) with metadata including source file, position, and SHA256 content hash for de-duplication
- **VectorEmbedding**: High-dimensional vector representation of a document chunk used for similarity search
- **SimilarityScore**: Numerical value (0-1) indicating how closely a chunk matches a query embedding
- **IngestionJob**: A process that converts raw documents into chunked embeddings in the vector store

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive specific, relevant book content answers in 90% of queries about book topics
- **SC-002**: Document ingestion processes 1000+ chunks within 30 seconds
- **SC-003**: Similarity search retrieves relevant content with precision > 0.85 on test queries
- **SC-004**: Zero template responses ("How to Use This Book") in production queries
- **SC-005**: System handles empty result sets gracefully with appropriate user feedback
- **SC-006**: Vector store health check accurately reflects ingested content count