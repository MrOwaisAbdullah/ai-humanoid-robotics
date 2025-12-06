---

description: "Task list for RAG Embedding System Fix implementation"
---

# Tasks: RAG Embedding System Fix

**Input**: Design documents from `/specs/002-rag-embedding-fix/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit and integration tests included as per feature specification requirements

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/rag/`, `backend/api/`
- **Tests**: `backend/tests/unit/`, `backend/tests/integration/`
- Paths based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create RAG fix feature branch from main
- [X] T002 [P] Verify existing backend/rag structure is in place
- [X] T003 [P] Create test directory structure in backend/tests/
- [X] T004 [P] Backup current vector database collection (if exists)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Update backend/rag/embedding.py to use text-embedding-3-small model
- [X] T006 [P] Add tiktoken dependency to requirements.txt for accurate token counting
- [X] T007 Add configuration models in backend/api/models/ingestion.py for IngestionConfig
- [X] T008 [P] Add configuration models in backend/api/models/chat.py for RetrievalConfig
- [X] T009 [P] [US1] Generate RAG pipeline components using rag-pipeline-builder skill
  - Invoked skill: `/skill rag-pipeline-builder`
  - Generated LangChain-free architecture documentation
  - Confirmed existing implementation follows best practices
- [X] T010 Configure error handling base classes in backend/api/exceptions.py
- [X] T011 Setup logging configuration for RAG components in backend/rag/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Accurate Book Content Retrieval (Priority: P1) 🎯 MVP

**Goal**: Users receive specific book content answers instead of generic template responses

**Independent Test**: Ask "What topics does this book cover?" and verify response contains actual book content, not "How to Use This Book"

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for template filtering in backend/tests/unit/test_chunking.py
- [X] T013 [P] [US1] Unit test for de-duplication in backend/tests/unit/test_retrieval.py
- [X] T014 [P] [US1] Integration test for end-to-end query in backend/tests/integration/test_rag_pipeline.py

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement template filtering in backend/rag/chunking.py
  - Add DEFAULT_TEMPLATES constant with regex patterns
  - Implement is_template_header() function
  - Update chunking logic to skip template content

- [ ] T016 [US1] Implement content de-duplication in backend/rag/retrieval.py
  - Add SHA256 hash generation in DocumentChunk
  - Update retrieval engine to filter duplicates
  - Add is_duplicate flag to RetrievalResult

- [ ] T017 [US1] Fix metadata consistency in backend/rag/retrieval.py
  - Update _format_document to use section_header instead of section
  - Add validation for required metadata fields

- [ ] T018 [US1] Update retrieval similarity threshold in backend/rag/chat.py
  - Change default from 0.3 to 0.7
  - Add get_adaptive_threshold() function
  - Add config override support

- [ ] T019 [US1] Add template filtering to ingestion process in backend/rag/ingestion.py
  - Filter out template chunks during ingestion
  - Track chunks_skipped in metrics
  - Add template pattern configuration

- [ ] T020 [US1] Enhance error responses in backend/api/routes/chat.py
  - Add specific error codes for no content found
  - Include helpful messages for users
  - Log template response attempts

- [ ] T021 [US1] Add monitoring metrics in backend/rag/chat.py
  - Track template response occurrences
  - Log similarity scores for queries
  - Monitor retrieval result quality

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Proper Document Ingestion (Priority: P1)

**Goal**: System successfully ingests book documents with proper chunking and stores them correctly

**Independent Test**: Run ingestion and verify chunks_count in health endpoint reflects actual content chunks

### Tests for User Story 2 ⚠️

- [ ] T022 [P] [US2] Unit test for ingestion path validation in backend/tests/unit/test_ingestion.py
- [ ] T023 [P] [US2] Unit test for chunk size validation in backend/tests/unit/test_chunking.py
- [ ] T024 [P] [US2] Integration test for ingestion pipeline in backend/tests/integration/test_rag_pipeline.py

### Implementation for User Story 2

- [ ] T025 [P] [US2] Restrict ingestion to backend/book_content in backend/rag/ingestion.py
  - Add DEFAULT_CONTENT_PATH constant
  - Implement path validation
  - Exclude docs/, build/, and other directories

- [ ] T026 [US2] Implement optimal chunking in backend/rag/chunking.py
  - Update chunk_size to 600 tokens
  - Set chunk_overlap to 100 tokens
  - Use tiktoken for accurate counting

- [ ] T027 [US2] Add minimum chunk size validation in backend/rag/chunking.py
  - Enforce minimum of 50 tokens
  - Merge small chunks with next content
  - Preserve context boundaries

- [ ] T028 [US2] Update ingestion API validation in backend/api/routes/ingest.py
  - Validate content_path parameter
  - Add force_reindex support
  - Return detailed job status

- [ ] T029 [US2] Enhance health endpoint with content metrics in backend/api/routes/health.py
  - Add chunks_count from vector store
  - Include last_ingestion timestamp
  - Report ingestion statistics

- [ ] T030 [US2] Add content existence validation in backend/rag/chat.py
  - Check if vector store has content before query
  - Return appropriate error if empty
  - Suggest re-ingestion if needed

- [ ] T031 [US2] Implement batch processing for large documents in backend/rag/ingestion.py
  - Process files in parallel batches
  - Respect OpenAI rate limits
  - Add progress tracking

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Optimal Similarity Scoring (Priority: P2)

**Goal**: System retrieves context using appropriate similarity thresholds for relevant responses

**Independent Test**: Query with low-relevance questions and verify system handles appropriately without returning poor matches

### Tests for User Story 3 ⚠️

- [ ] T032 [P] [US3] Unit test for similarity threshold enforcement in backend/tests/unit/test_retrieval.py
- [ ] T033 [P] [US3] Unit test for MMR algorithm in backend/tests/unit/test_retrieval.py
- [ ] T034 [P] [US3] Integration test for retrieval edge cases in backend/tests/integration/test_rag_pipeline.py

### Implementation for User Story 3

- [ ] T035 [P] [US3] Implement Maximal Marginal Relevance (MMR) in backend/rag/retrieval.py
  - Add maximal_marginal_relevance() function
  - Set lambda parameter to 0.5
  - Integrate with existing retrieval pipeline

- [ ] T036 [US3] Add similarity threshold configuration in backend/api/models/chat.py
  - Update RetrievalConfig schema
  - Add validation for threshold range
  - Include MMR parameters

- [ ] T037 [US3] Implement result ranking in backend/rag/retrieval.py
  - Sort by similarity score
  - Apply MMR reordering
  - Limit to max_results

- [ ] T038 [US3] Add empty result handling in backend/rag/chat.py
  - Detect when no content meets threshold
  - Return helpful error message
  - Suggest query rephrasing

- [ ] T039 [US3] Optimize vector search performance in backend/rag/storage/qdrant_store.py
  - Use HNSW indexing
  - Optimize ef_search parameter
  - Add connection pooling

- [ ] T040 [US3] Add retrieval analytics in backend/rag/retrieval.py
  - Track threshold hit rates
  - Monitor MMR effectiveness
  - Log query performance

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Update README.md with RAG fix instructions in project root
- [ ] T042 Add comprehensive error logging in backend/rag/__init__.py
- [ ] T043 [P] Add performance optimizations for embedding generation in backend/rag/embedding.py
- [ ] T044 Add configuration validation in backend/rag/config.py
- [ ] T045 [P] Create deployment scripts for RAG fixes in scripts/deploy/
- [ ] T046 Update documentation with troubleshooting guide in docs/troubleshooting.md
- [ ] T047 [P] Add end-to-end test suite in backend/tests/e2e/
- [ ] T048 Run quickstart.md validation test
- [ ] T049 [P] Add monitoring dashboards for RAG metrics in monitoring/
- [ ] T050 [P] Add rate limiting for external APIs in backend/rag/rate_limits.py
  - Implement OpenAI API rate limiting (3000 RPM)
  - Add Qdrant connection pooling
  - Include backoff strategy for retries
- [ ] T051 Cleanup deprecated code paths in backend/rag/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Stories 1 & 2 can proceed in parallel (both P1)
  - User Story 3 (P2) can wait or proceed in parallel with resources
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Independent but shares components
- **User Story 3 (P2)**: Can start after Foundational - Enhances retrieval from US1 & US2

### Within Each User Story

- Tests (T011-T013, T021-T023, T031-T033) MUST be written and FAIL before implementation
- Template filtering (T014) before de-duplication (T015) in US1
- Ingestion validation (T024) before chunking updates (T025) in US2
- MMR implementation (T034) before ranking (T036) in US3

### Parallel Opportunities

- All Setup tasks (T001-T004) can run in parallel
- Most Foundational tasks (T005-T010) can run in parallel
- Once Foundational phase completes:
  - User Story 1 and User Story 2 can proceed in parallel (both P1)
  - All tests within each story marked [P] can run in parallel
  - Different components (chunking, retrieval, ingestion) can be worked on in parallel

---

## Parallel Example: User Story 1 & 2

```bash
# Launch all tests for User Stories 1 & 2 together:
Task: "Unit test for template filtering in backend/tests/unit/test_chunking.py"
Task: "Unit test for de-duplication in backend/tests/unit/test_retrieval.py"
Task: "Unit test for ingestion path validation in backend/tests/unit/test_ingestion.py"
Task: "Unit test for chunk size validation in backend/tests/unit/test_chunking.py"

# Launch User Story 1 and 2 implementation in parallel:
Task: "Implement template filtering in backend/rag/chunking.py"
Task: "Restrict ingestion to backend/book_content in backend/rag/ingestion.py"
Task: "Implement content de-duplication in backend/rag/retrieval.py"
Task: "Implement optimal chunking in backend/rag/chunking.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010) - CRITICAL
3. Complete Phase 3: User Story 1 (T011-T020)
4. **STOP and VALIDATE**: Test with query about book content
5. Verify no "How to Use This Book" responses

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP - stops template responses!)
3. Add User Story 2 → Test → Deploy (ensures proper ingestion)
4. Add User Story 3 → Test → Deploy (optimizes retrieval)
5. Each story adds value without breaking previous fixes

### Critical Success Factors

- **Must complete Foundational phase** before any user stories
- **User Story 1 is the MVP** - it directly fixes the reported issue
- **Test before implementing** - write tests, watch them fail, then implement
- **Independent verification** - each story must work alone

---

## Validation Checklist

After each user story completion:

- [ ] No template responses in test queries
- [ ] Health endpoint shows correct chunks_count
- [ ] Similarity threshold enforced (≥0.7)
- [ ] Error messages are user-friendly
- [ ] Logs show de-duplication working
- [ ] Performance meets requirements (<3s response)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- The core issue (template responses) is fixed in User Story 1
- User Story 2 prevents the issue from recurring
- User Story 3 optimizes the overall system quality
- T009 uses rag-pipeline-builder skill for accelerated implementation
- Verify tests fail before implementing (TDD approach)
- Commit after each logical group of tasks