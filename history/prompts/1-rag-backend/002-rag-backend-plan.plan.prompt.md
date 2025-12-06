---
ID: 002
TITLE: rag-backend-plan
STAGE: plan
DATE_ISO: 2025-01-05
SURFACE: agent
MODEL: claude-sonnet-2024-02-15
FEATURE: 1-rag-backend
BRANCH: 1-rag-backend
USER: unspecified
COMMAND: /sp.plan
LABELS: ["rag", "backend", "plan", "architecture"]
LINKS:
  SPEC: specs/1-rag-backend/spec.md
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - specs/1-rag-backend/plan.md
  - specs/1-rag-backend/plan/research.md
  - specs/1-rag-backend/plan/data-model.md
  - specs/1-rag-backend/plan/contracts/openapi.yaml
  - specs/1-rag-backend/plan/quickstart.md
TESTS_YAML:
  -
PROMPT_TEXT: |
  1.  **Scaffold Backend Structure**:
      *   Create `backend/` directory.
      *   Create `backend/rag/` package for core logic.
      *   Initialize `requirements.txt` with: `fastapi`, `uvicorn`, `openai`, `qdrant-client`, `tiktoken`, `python-multipart`.

  2.  **Implement RAG Core (No LangChain)**:
      *   Create `backend/rag/chunking.py`: Port the `RecursiveTextSplitter` from the skill (pure Python).
      *   Create `backend/rag/embeddings.py`: Implement `EmbeddingGenerator` using `AsyncOpenAI`.
      *   Create `backend/rag/vector_store.py`: Implement `QdrantManager` with `qdrant-client`.

  3.  **Develop API Endpoints**:
      *   Create `backend/main.py`:
          *   Setup FastAPI app with Lifespan events to initialize OpenAI/Qdrant clients.
          *   Add CORS middleware allowing `https://mrowaisabdullah.github.io`.
          *   Implement `POST /chat`: Streaming endpoint using `StreamingResponse` and `async generator` for SSE.
          *   Implement `POST /ingest`: Endpoint to trigger document processing.
          *   Implement `GET /health`.

  4.  **Ingestion Logic**:
      *   Create `backend/scripts/ingest.py`: Script to traverse `docs/`, read Markdown, split chunks, embed, and upsert to Qdrant.
      *   Integrate this logic into the `/ingest` endpoint.

  5.  **Deployment Configuration**:
      *   Create `backend/Dockerfile`:
          *   Base image: `python:3.11-slim`.
          *   User: Create non-root user with ID `1000`.
          *   Port: Expose `7860`.
          *   CMD: `uvicorn main:app --host 0.0.0.0 --port 7860`.
      *   Create `backend/.env.example`.

  6.  **Verification**:
      *   Test `/health` endpoint locally.
      *   Verify `Dockerfile` builds without errors.
RESPONSE_TEXT: |
  Created comprehensive implementation plan including:
  - Main plan.md with technical context and constitution checks
  - research.md resolving all critical architectural decisions
  - data-model.md defining entities and relationships
  - OpenAPI contracts for all endpoints
  - quickstart.md for deployment and testing

  Plan is ready for implementation with clear architecture decisions and no unresolved clarifications.
OUTCOME: Implementation plan created with all research completed and contracts defined
EVALUATION: Plan phase complete - ready for task breakdown and implementation
---

# Prompt History Record

## Prompt
The user provided a detailed 6-point plan for implementing the RAG backend:
1. Scaffold backend structure
2. Implement RAG core (no LangChain)
3. Develop API endpoints
4. Create ingestion logic
5. Configure deployment
6. Verify implementation

## Context
Following the clarification phase where we resolved authentication, citation format, and conversation context decisions, the user provided specific implementation guidance for the RAG backend. This included exact technical requirements, dependencies, and deployment specifications.

## Analysis
I processed the user's implementation guidance and created a comprehensive plan including:

1. **Technical Context Analysis**:
   - Identified system architecture components
   - Recognized key design decisions from clarification phase
   - Noted constitution alignment points

2. **Research Phase**:
   - Resolved rate limiting strategy (token bucket with API key tiers)
   - Determined Qdrant connection pooling approach
   - Established token optimization strategies
   - Defined FastAPI SSE best practices
   - Created Hugging Face Spaces optimization plan

3. **Design Phase**:
   - Created comprehensive data model with entities and relationships
   - Defined API contracts using OpenAPI specification
   - Established state transitions and validation rules
   - Created request/response schemas

## Planning Deliverables

### 1. Implementation Plan (plan.md)
- Complete technical context with architecture decisions
- Constitution check showing security, performance, and maintainability compliance
- Phased implementation approach
- Risk assessment with mitigation strategies
- Success criteria aligned with specification

### 2. Research Document (research.md)
- Resolved all NEEDS CLARIFICATION items from specification
- Detailed implementation decisions with rationales
- Code examples for key patterns
- Performance optimization strategies

### 3. Data Model (data-model.md)
- Entity definitions with attributes and validation
- Relationship mappings
- Qdrant collection schema
- State transition diagrams
- Performance considerations

### 4. API Contracts (contracts/openapi.yaml)
- Complete OpenAPI 3.0 specification
- All endpoints with detailed schemas
- Security definitions for API keys
- Error response models

### 5. Quickstart Guide (quickstart.md)
- Step-by-step setup instructions
- Environment configuration
- Testing examples
- Deployment guide for Hugging Face Spaces
- Troubleshooting section

## Key Architectural Decisions

### Confirmed from Clarification Phase
- Authentication: Public access with optional API key for rate limiting
- Citations: Embedded markdown format [Chapter - Section](source)
- Conversation: Short-term memory (last 3 messages)

### Newly Decided
- Rate Limiting: Token bucket pattern with slowapi library
- Vector Storage: Async Qdrant client with gRPC optimization
- Streaming: Server-Sent Events with async generators
- Deployment: Multi-stage Docker builds for HF Spaces

## Next Steps
The plan is complete and ready for the task breakdown phase (`/sp.tasks`). All technical decisions have been made, contracts defined, and implementation approach established. The backend structure and implementation flow are clearly documented.

## Output Files Created
1. `specs/1-rag-backend/plan.md` - Main implementation plan
2. `specs/1-rag-backend/plan/research.md` - Research findings
3. `specs/1-rag-backend/plan/data-model.md` - Data model definition
4. `specs/1-rag-backend/plan/contracts/openapi.yaml` - API contracts
5. `specs/1-rag-backend/plan/quickstart.md` - Quickstart guide