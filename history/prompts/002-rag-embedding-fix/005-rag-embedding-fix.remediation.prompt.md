---
ID: 005
TITLE: RAG Embedding Remediation
STAGE: misc
DATE_ISO: 2025-12-06
SURFACE: agent
MODEL: glm-4.6
FEATURE: 002-rag-embedding-fix
BRANCH: 001-chatkit-integration
USER: User
COMMAND: remediation edits
LABELS: ["rag", "embeddings", "remediation", "spec-update", "task-update"]
LINKS:
  SPEC: "../../specs/002-rag-embedding-fix/spec.md"
  PLAN: "../../specs/002-rag-embedding-fix/plan.md"
  TASKS: "../../specs/002-rag-embedding-fix/tasks.md"
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - specs/002-rag-embedding-fix/spec.md
  - specs/002-rag-embedding-fix/tasks.md
TESTS_YAML:
  - Updated FR-002 with specific token count (600)
  - Added FR-009 for SHA256 de-duplication
  - Added T009 to invoke rag-pipeline-builder skill
  - Added T050 for rate limiting
  - Renumbered all tasks (now 51 total)
PROMPT_TEXT: |
  yes apply this in our plan and tasks
RESPONSE_TEXT: |
  Applied all remediation edits:

  1. Updated spec.md:
     - FR-002: Fixed token count to 600 tokens with 100 overlap
     - FR-009: Added SHA256 de-duplication requirement
     - DocumentChunk: Updated to include SHA256 hash

  2. Updated tasks.md:
     - Added T009 to invoke rag-pipeline-builder skill in Phase 2
     - Added T050 for rate limiting in Phase 6
     - Renumbered all subsequent tasks (now 51 total)
     - Updated notes to mention skill usage

  All critical and high issues from analysis have been resolved.
OUTCOME: Successfully applied remediation edits
EVALUATION: Ready for implementation with skill integration
---

# Prompt History Record: RAG Embedding Remediation

## Context
User approved the remediation edits for the top 3 issues identified in the analysis. The edits were applied to both spec.md and tasks.md files.

## Changes Applied

### 1. Specification Updates (spec.md)

**FR-002 - Token-based chunking**:
- Changed from: "optimal chunk sizes (500-800 tokens)"
- Changed to: "600 tokens per chunk and 100 token overlap"
- Added reference: "(based on research.md findings)"

**FR-009 - De-duplication** (NEW):
- Added: "System MUST use SHA256 content hashing to detect and filter duplicate chunks during retrieval"

**DocumentChunk Entity**:
- Updated to include "SHA256 content hash for de-duplication"
- Changed token count from "500-800 tokens" to "600 tokens"

### 2. Task List Updates (tasks.md)

**Added Critical Task**:
```
- [ ] T009 [P] [US1] Generate RAG pipeline components using rag-pipeline-builder skill
  - Invoke skill: `/skill rag-pipeline-builder`
  - Generate chunking implementation (600 tokens, 100 overlap)
  - Create OpenAI embedding client (text-embedding-3-small)
  - Implement Qdrant manager with de-duplication support
  - Output to backend/rag/generated/ for review
```

**Added Rate Limiting Task**:
```
- [ ] T050 [P] Add rate limiting for external APIs in backend/rag/rate_limits.py
  - Implement OpenAI API rate limiting (3000 RPM)
  - Add Qdrant connection pooling
  - Include backoff strategy for retries
```

**Task Renumbering**:
- All tasks after T009 renumbered sequentially
- Total task count: 49 → 51
- Phase 2 now has 7 tasks (includes skill generation)
- Phase 6 now has 11 tasks (includes rate limiting)

### 3. Updated Notes Section
Added reference to T009 using rag-pipeline-builder skill for accelerated implementation.

## Impact

### Critical Issue Resolved
- **C1: Missing Skill Integration** - Now explicitly tasked in Phase 2
- Will accelerate implementation by ~45 minutes
- Provides proven LangChain-free architecture

### High Issues Resolved
- **H1: Token Count Consistency** - Now consistently 600 tokens across all documents
- **H2: SHA256 Documentation** - Now explicitly required in FR-009

### Medium Issues Addressed
- **M3: Rate Limiting** - Added as T050 in Phase 6

## Files Modified
- specs/002-rag-embedding-fix/spec.md - Updated requirements and entities
- specs/002-rag-embedding-fix/tasks.md - Added skill task and rate limiting
- history/prompts/002-rag-embedding-fix/005-rag-embedding-fix.remediation.prompt.md - This PHR

## Next Steps
The artifacts are now ready for implementation with:
1. Clear specification of token counts and de-duplication method
2. Explicit use of rag-pipeline-builder skill for faster development
3. Production-ready considerations (rate limiting)
4. All tasks properly numbered and organized

User can now proceed with `/sp.implement` confident that all critical issues have been resolved.