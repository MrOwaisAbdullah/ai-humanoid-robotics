---
ID: 002
TITLE: RAG Embedding Implementation Plan
STAGE: plan
DATE_ISO: 2025-12-06
SURFACE: agent
MODEL: glm-4.6
FEATURE: 002-rag-embedding-fix
BRANCH: 001-chatkit-integration
USER: User
COMMAND: /sp.plan
LABELS: ["rag", "embeddings", "vector-search", "implementation", "planning"]
LINKS:
  SPEC: "../../specs/002-rag-embedding-fix/spec.md"
  PLAN: "../../specs/002-rag-embedding-fix/plan.md"
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - specs/002-rag-embedding-fix/plan.md
  - specs/002-rag-embedding-fix/research.md
  - specs/002-rag-embedding-fix/data-model.md
  - specs/002-rag-embedding-fix/contracts/api.yaml
  - specs/002-rag-embedding-fix/quickstart.md
TESTS_YAML:
  - All constitution checks passed
  - Research completed for all technical uncertainties
  - Data model designed with validation rules
  - API contracts defined with OpenAPI spec
PROMPT_TEXT: |
  # RAG Implementation Analysis Report

  **Date:** December 06, 2025
  **Status:** Analysis Complete
  **Component:** RAG Pipeline (Ingestion, Chunking, Retrieval)

  ## Executive Summary

  The reported issue where the chatbot responds with *"each source repeats the title 'How to Use This Book' but does not provide further details"* is primarily caused by **content duplication** and **retrieval relevance crowding**. The system is successfully retrieving context, but it is retrieving multiple copies of the same "meta-instruction" section instead of the actual book content (Introduction, Chapters, etc.).

  ## 1. Root Cause Analysis

  ### A. Content Duplication (Primary Issue)
  The project structure contains multiple potential copies of the documentation:
  - `backend/book_content/` (Likely the source of truth)
  - `docs/` (Docusaurus source, potentially identical content)
  - `build/` (Generated artifacts, usually ignored but worth verifying)

  If the ingestion process is targeted at the project root or includes both `backend/` and `docs/`, the Vector Database (Qdrant) receives duplicate chunks. When a user asks "tell me about this book", the embedding model finds the section **"How to Use This Book"** to be the most semantically similar match. Because duplicates exist, the Top-5 retrieved chunks are *all* identical copies of this specific section, pushing out diverse content like "Chapter 1: Introduction".

  ### B. Semantic Similarity Bias
  The query "tell me about this **book**" semantically aligns very strongly with the header "How to Use This **Book**".
  - **Query:** "tell me about this book"
  - **Match:** "How to Use This Book"
  - **Missed:** "Chapter 1: Introduction to Physical AI" (Does not explicitly contain the word "Book" in the header).

  Without a mechanism to diversify results (like Max Marginal Relevance) or filter duplicates, the most "similar" text (the instruction guide) monopolizes the context window.

  ### C. Chunking Granularity
  The `MarkdownChunker` splits strictly by headers. Small sections (like "How to Use This Book") become individual chunks. While this is generally correct for structure, "orphan" headers or very short sections can lack sufficient context to be useful on their own.

  ### D. Metadata Mismatch
  There is a minor code inconsistency identified during analysis:
  - **Chunking:** Saves the header name as `metadata["section_header"]`.
  - **Retrieval:** Tries to read `metadata["section"]` for formatting citations.
  This results in context that lacks clear section labels, making it harder for the LLM to understand the structure of the retrieved text.

  ## 2. Identified Problems & Fixes

  | Severity | Component | Problem | Recommended Solution |
  |----------|-----------|---------|----------------------|
  | **High** | **Ingestion** | **Duplicate Indexing**: The same content exists in `backend/book_content` and `docs/`. | **Restrict Ingestion Path**: Update ingestion scripts to target *only* `backend/book_content` (or the canonical source) and explicitly ignore `docs/` or `build/`. |
  | **High** | **Retrieval** | **Context Crowding**: Top-K results are identical, hiding other relevant info. | **De-duplication**: Implement a filter in `RetrievalEngine` to remove chunks with identical content or hash values before returning results. |
  | **Medium** | **Retrieval** | **Semantic Tunnel Vision**: "Book" keyword biases result to meta-pages. | **Hybrid Search / MMR**: Use Maximal Marginal Relevance (MMR) in the retrieval step to ensure diversity in the selected chunks. |
  | **Low** | **Code** | **Metadata Key Mismatch**: `section_header` vs `section`. | **Update Retrieval.py`: Change `_format_document` to look for `section_header`. |
  | **Low** | **Chunking** | **Small Chunks**: Headers might be chunked with little content. | **Min Chunk Size**: Enforce a minimum token count (e.g., 50 tokens) to merge small headers with subsequent content. |

  ## 3. Next Steps

  1.  **Clean the Vector Database**: Run a "re-index" operation that clears the existing collection.
  2.  **Targeted Ingestion**: Run the ingestion script specifically on `backend/book_content`:
      ```bash
      python -m backend.rag.scripts.ingest --dir backend/book_content
      ```
  3.  **Apply Code Fixes**: (If approved)
      - Update `retrieval.py` to handle duplicates and fix metadata keys.
      - Update `chunking.py` to prevent tiny chunks.

  ## 4. Technical Details (Code References)

  - **`backend/rag/chunking.py`**:
      - `split_by_headers` regex logic is robust but creates a new chunk for every header.
      - `create_chunks_from_section` does not filter small chunks.

  - **`backend/rag/retrieval.py`**:
      - `_format_document`: Uses `metadata.get("section")` (Incorrect) instead of `section_header`.
      - `retrieve`: Does not deduplicate results based on content hash.

  - **`backend/rag/ingestion.py`**:
      - `ingest_directory` recursive search defaults to `*.md*`. If run from root, it catches `docs/*.md`, `backend/*.md`, `README.md`, etc.

  ---
  *Report generated by Gemini CLI Agent*
RESPONSE_TEXT: |
  Created comprehensive implementation plan addressing all identified issues:

  **Phase 0 - Research Completed**:
  - Optimal chunk size: 600 tokens with 100 token overlap
  - De-duplication: SHA256 content hashing
  - MMR implementation with λ=0.5 for result diversity
  - Template filtering with configurable regex patterns
  - Dynamic similarity threshold (starting at 0.7)
  - OpenAI text-embedding-3-small model selected

  **Phase 1 - Design Artifacts Created**:
  - Data model with DocumentChunk, VectorEmbedding, RetrievalResult entities
  - Complete OpenAPI 3.0 specification for all RAG endpoints
  - Quickstart guide with troubleshooting steps

  **Key Solutions**:
  1. Restrict ingestion to backend/book_content only
  2. Implement content de-duplication using SHA256 hashes
  3. Apply MMR to ensure result diversity
  4. Filter template content using regex patterns
  5. Adjust similarity threshold from 0.3 to 0.7
  6. Fix metadata consistency (section_header vs section)

  All constitution checks passed. Ready for task generation with /sp.tasks
OUTCOME: Implementation plan complete with research, data models, API contracts, and quickstart guide
EVALUATION: Plan addresses all root causes from analysis with specific implementation approaches
---

# Prompt History Record: RAG Embedding Implementation Plan

## Context
User provided a detailed RAG analysis report identifying the root cause of generic template responses. The primary issue is content duplication causing the system to retrieve multiple copies of "How to Use This Book" instead of actual book content.

## Analysis Process
1. **Loaded Planning Environment**: Set up spec directory structure and loaded templates
2. **Constitution Review**: Verified SOLID principles compliance for all proposed changes
3. **Research Phase**: Resolved all technical uncertainties:
   - Chunk size optimization (600 tokens with 100 overlap)
   - De-duplication strategy (SHA256 hashing)
   - MMR implementation for result diversity
   - Template filtering approaches
   - Similarity threshold tuning

## Implementation Strategy

### Phase 0: Research Findings
- Documented optimal parameters for OpenAI embeddings
- Selected cost-effective embedding model (text-embedding-3-small)
- Designed adaptive similarity threshold mechanism
- Established error handling patterns

### Phase 1: Design Deliverables
1. **Data Model** (data-model.md):
   - DocumentChunk with content_hash for deduplication
   - RetrievalResult with duplicate detection
   - IngestionJob status tracking
   - RetrievalConfig for flexible parameters

2. **API Contracts** (contracts/api.yaml):
   - Complete OpenAPI 3.0 specification
   - Enhanced /api/v1/ingest with path validation
   - Improved /api/v1/chat with error handling
   - New /api/v1/health with content metrics

3. **Quickstart Guide** (quickstart.md):
   - Step-by-step setup instructions
   - Troubleshooting for template responses
   - Configuration examples
   - Test script for validation

## Key Technical Decisions

1. **Ingestion Restriction**: Target only `backend/book_content` to prevent duplication
2. **De-duplication**: SHA256 hash comparison before returning results
3. **Similarity Threshold**: Adjust from 0.3 to 0.7 with adaptive fallback
4. **Chunking Strategy**: 600 tokens with 100 token overlap using tiktoken
5. **Template Filtering**: Configurable regex patterns for common headers

## Files Generated
- specs/002-rag-embedding-fix/plan.md - Main implementation plan
- specs/002-rag-embedding-fix/research.md - Technical research findings
- specs/002-rag-embedding-fix/data-model.md - Entity definitions and relationships
- specs/002-rag-embedding-fix/contracts/api.yaml - Complete API specification
- specs/002-rag-embedding-fix/quickstart.md - Setup and troubleshooting guide
- history/prompts/002-rag-embedding-fix/002-rag-embedding-fix.plan.prompt.md - This PHR

## Constitution Compliance
- ✅ All SOLID principles maintained
- ✅ No code duplication in proposed solution
- ✅ Proper error handling strategy
- ✅ Configuration management via environment variables
- ✅ Production-first mindset with monitoring considerations

## Next Steps
Plan is complete and ready for task generation with `/sp.tasks`. The implementation will resolve the template response issue by addressing content duplication, improving retrieval relevance, and implementing proper filtering mechanisms.