---

description: "Task list for RAG Backend API implementation"
---

# Tasks: RAG Backend API

**Input**: Design documents from `/specs/1-rag-backend/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL for this feature - only include if explicitly requested in the specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend project**: `backend/` at repository root (per plan.md)
- Paths shown below follow the backend structure from the implementation plan
- Package management: Uses `uv` for fast dependency management and reproducible builds

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend directory structure per implementation plan
- [ ] T002 Initialize Python project with pyproject.toml and uv configuration
- [ ] T003 [P] Create .env.example with environment variables template
- [ ] T004 [P] Set up Python package structure in backend/rag/__init__.py
- [ ] T005 Create Dockerfile for Hugging Face Spaces deployment with uv
- [ ] T006 Create scripts directory for ingestion utilities
- [ ] T007 Generate uv.lock file for reproducible dependency management

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Implement rate limiting middleware with slowapi in backend/main.py
- [ ] T008 Setup Qdrant client initialization with connection pooling in backend/main.py
- [ ] T009 Configure CORS middleware for https://mrowaisabdullah.github.io in backend/main.py
- [ ] T010 [P] Implement error handling and logging infrastructure in backend/main.py
- [ ] T011 Create environment configuration management in backend/main.py
- [ ] T012 [P] Setup lifespan events for OpenAI and Qdrant clients in backend/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Book Content Ingestion (Priority: P1) 🎯 MVP

**Goal**: Ingest entire book Markdown files into the RAG system

**Independent Test**: Call /ingest endpoint and verify chunks are stored in Qdrant with correct metadata

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create Document model classes in backend/rag/models.py
- [ ] T014 [P] [US1] Create TextChunk model classes in backend/rag/models.py
- [ ] T015 [P] [US1] Implement RecursiveTextSplitter in backend/rag/chunking.py (no LangChain)
- [ ] T016 [P] [US1] Create EmbeddingGenerator class in backend/rag/embeddings.py using AsyncOpenAI
- [ ] T017 [P] [US1] Implement QdrantManager in backend/rag/vector_store.py
- [ ] T018 [US1] Create markdown file discovery logic in backend/rag/ingestion.py
- [ ] T019 [US1] Implement batch embedding generation in backend/rag/ingestion.py
- [ ] T020 [US1] Build Qdrant upsert operations with metadata in backend/rag/ingestion.py
- [ ] T021 [US1] Add error handling and progress tracking in backend/rag/ingestion.py
- [ ] T022 [US1] Implement /ingest endpoint in backend/main.py (uses T018-T021)
- [ ] T023 [US1] Create standalone ingestion script in backend/scripts/ingest.py
- [ ] T024 [US1] Add ingestion status tracking in backend/main.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Real-time Chat with Book (Priority: P1)

**Goal**: Enable users to ask questions and receive streaming, context-aware answers

**Independent Test**: Send questions to /chat endpoint and verify responses are relevant with proper streaming

### Implementation for User Story 2

- [ ] T025 [P] [US2] Create ConversationContext model in backend/rag/models.py
- [ ] T026 [P] [US2] Create Message model classes in backend/rag/models.py
- [ ] T027 [P] [US2] Create Citation model classes in backend/rag/models.py
- [ ] T028 [P] [US2] Implement semantic search logic in backend/rag/retrieval.py
- [ ] T029 [P] [US2] Create response generation with citations in backend/rag/generation.py
- [ ] T030 [US2] Implement conversation context management (3 messages) in backend/rag/context.py
- [ ] T031 [US2] Create streaming response generator with SSE in backend/rag/chat.py
- [ ] T032 [US2] Implement /chat endpoint with StreamingResponse in backend/main.py
- [ ] T033 [US2] Add citation formatting (markdown brackets) in backend/rag/generation.py
- [ ] T034 [US2] Implement session-based conversation context in backend/main.py
- [ ] T035 [US2] Add input validation for chat requests in backend/main.py
- [ ] T036 [US2] Implement error handling for chat streaming in backend/main.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Content Management (Priority: P2)

**Goal**: Enable content re-ingestion and system health monitoring

**Independent Test**: Call /ingest with updated content and verify chunks are replaced; check /health endpoint

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement /ingest/status endpoint in backend/main.py
- [ ] T038 [P] [US3] Create ingestion task tracking system in backend/rag/tasks.py
- [ ] T039 [US3] Implement re-ingestion logic to replace outdated chunks in backend/rag/ingestion.py
- [ ] T040 [P] [US3] Add ingestion progress monitoring in backend/main.py
- [ ] T041 [US3] Create system health monitoring in backend/main.py
- [ ] T042 [US3] Implement document hash-based change detection in backend/rag/ingestion.py
- [ ] T043 [US3] Add ingestion statistics tracking in backend/main.py
- [ ] T044 [US3] Implement concurrent ingestion request handling in backend/main.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Production optimizations and final preparations

- [ ] T045 [P] Implement connection pooling for Qdrant in backend/rag/vector_store.py
- [ ] T046 [P] Add comprehensive error handling for external API calls in backend/rag/client.py
- [ ] T047 [P] Implement token usage optimization in backend/rag/generation.py
- [ ] T048 [P] Add request/response logging in backend/main.py
- [ ] T049 Create README.md with setup instructions
- [ ] T050 Create API documentation in backend/docs/api.md
- [ ] T051 Add performance monitoring and metrics
- [ ] T052 Implement graceful degradation when services are unavailable
- [ ] T053 Validate Dockerfile builds correctly for HF Spaces
- [ ] T054 Run quickstart.md validation locally

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create Document model classes in backend/rag/models.py"
Task: "Create TextChunk model classes in backend/rag/models.py"

# Launch all core RAG components together:
Task: "Implement RecursiveTextSplitter in backend/rag/chunking.py"
Task: "Create EmbeddingGenerator class in backend/rag/embeddings.py"
Task: "Implement QdrantManager in backend/rag/vector_store.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion)
4. Complete Phase 4: User Story 2 (Chat)
5. **STOP AND VALIDATE**: Test both stories independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Ingestion)
   - Developer B: User Story 2 (Chat)
   - Developer C: User Story 3 (Content Management)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tasks follow the LangChain-free constraint from technical requirements
- All I/O operations must be async/await
- Port 7860 configured for Hugging Face Spaces
- Docker configured for non-root user (ID: 1000)
- Server-Sent Events implemented for streaming responses