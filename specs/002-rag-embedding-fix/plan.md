# Implementation Plan: RAG Embedding System Fix

**Branch**: `002-rag-embedding-fix` | **Date**: 2025-12-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-rag-embedding-fix/spec.md`

## Summary

Fix RAG system returning generic template responses by addressing content duplication, improving retrieval relevance, and implementing proper chunking strategies. The solution involves: (1) restricting ingestion to canonical content source, (2) implementing de-duplication in retrieval, (3) adjusting similarity thresholds, (4) fixing metadata inconsistencies, and (5) optimizing chunk sizes for better semantic representation.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, OpenAI SDK, Qdrant, tiktoken
**Storage**: Qdrant vector database
**Testing**: pytest
**Target Platform**: Linux server (backend API)
**Project Type**: Web application (RAG backend)
**Performance Goals**: <3s first response, >90% query relevance
**Constraints**: OpenAI API rate limits, Qdrant free tier (1GB)
**Scale/Scope**: Single book (~1000 chunks), concurrent users <100

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### SOLID Principles Compliance
✅ **SRP**: Each RAG component (chunking, embedding, retrieval) has single responsibility
✅ **OCP**: Retrieval strategies designed for extension without modification
✅ **LSP**: Different vector stores can be substituted via interface
✅ **ISP**: Separate interfaces for ingestion vs retrieval
✅ **DIP**: Depend on VectorStore interface, not Qdrant specifically
✅ **DRY**: No code duplication identified in solution

### Other Constitution Principles
✅ **Error Handling**: All external calls will have proper error handling
✅ **Config Management**: Using environment variables (no hardcoding)
✅ **API Design**: RESTful endpoints with consistent naming
✅ **Performance**: Chunking and caching strategies included
✅ **Documentation Research**: Using latest OpenAI docs via Context7

## Project Structure

### Documentation (this feature)

```text
specs/002-rag-embedding-fix/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── api.yaml         # OpenAPI spec for RAG endpoints
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── rag/
│   ├── __init__.py
│   ├── chat.py          # Modify: similarity threshold
│   ├── chunking.py      # Modify: min chunk size, template filtering
│   ├── embedding.py     # Verify: latest model usage
│   ├── ingestion.py     # Modify: restrict path, template filtering
│   ├── retrieval.py     # Modify: deduplication, metadata fix
│   └── storage/
│       ├── __init__.py
│       └── qdrant_store.py
├── api/
│   ├── routes/
│   │   ├── chat.py      # Modify: error handling
│   │   └── ingest.py    # Modify: validation
│   └── models/
│       ├── chat.py      # Add: response models
│       └── ingest.py    # Add: request models
└── tests/
    ├── unit/
    │   ├── test_chunking.py
    │   ├── test_retrieval.py
    │   └── test_ingestion.py
    └── integration/
        └── test_rag_pipeline.py

frontend/src/
└── components/
    └── ChatWidget/      # Existing - verify error handling
```

**Structure Decision**: Using existing backend structure with focused modifications to RAG components. No new major directories needed.

## Complexity Tracking

No violations requiring justification. All changes are within existing architecture and follow SOLID principles.

## Phase 0: Research & Clarifications

### Research Tasks

1. **Optimal Chunk Size for OpenAI Embeddings**
   - Research latest recommendations for text-embedding-3-small/large
   - Verify token counting with tiktoken
   - Document overlap strategy for context preservation

2. **De-duplication Strategies**
   - Research content hash algorithms (MD5, SHA256)
   - Evaluate duplicate detection performance impact
   - Document implementation approach for Qdrant

3. **Maximal Marginal Relevance (MMR)**
   - Research MMR implementation in RAG systems
   - Evaluate lambda parameter tuning
   - Document hybrid search approach (semantic + keyword)

4. **Template Content Filtering**
   - Research markdown header patterns
   - Evaluate regex approaches for template detection
   - Document configurable exclusion rules

## Phase 1: Design & Contracts

### Data Model Updates

Key entities to modify:
- DocumentChunk: Add content_hash, template_flag fields
- RetrievalResult: Add deduplication metadata
- IngestionConfig: Add path restrictions, template filters

### API Contract Updates

Endpoints to modify:
- POST /api/v1/ingest: Add path validation, force_reindex
- GET /api/v1/health: Add content metrics
- POST /api/v1/chat: Enhanced error responses

### Implementation Strategy

1. **Ingestion Path Restriction**
   - Default to backend/book_content only
   - Add configurable allowed_paths
   - Exclude docs/, build/, and other non-content dirs

2. **Content De-duplication**
   - Generate SHA256 hash for each chunk
   - Store hash in metadata
   - Filter duplicates before return

3. **Similarity Threshold Adjustment**
   - Change from 0.3 to 0.7 in retrieval
   - Add config override for testing
   - Document rationale in code

4. **Metadata Consistency**
   - Fix section_header vs section mismatch
   - Update all references consistently
   - Add validation in chunking

5. **Template Filtering**
   - Identify common template headers
   - Add regex patterns for exclusion
   - Make patterns configurable

## Phase 2: Testing & Validation

### Test Coverage

1. **Unit Tests**
   - Chunk size validation
   - De-duplication logic
   - Similarity threshold enforcement
   - Template filtering rules

2. **Integration Tests**
   - End-to-end ingestion pipeline
   - Retrieval with real queries
   - Error handling scenarios

3. **Performance Tests**
   - Ingestion speed with 1000+ chunks
   - Query latency with de-duplication
   - Memory usage with large documents

### Success Metrics

- Zero template responses in test queries
- >90% query relevance score
- <30s ingestion time for full book
- <3s query response time