# Implementation Plan: RAG Backend API

**Feature Branch**: `1-rag-backend`
**Created**: 2025-01-05
**Status**: Draft
**Spec**: [spec.md](spec.md)

## Technical Context

### System Architecture
- **Backend Framework**: FastAPI with async/await patterns
- **Vector Database**: Qdrant for semantic search and storage
- **Embedding Model**: OpenAI text-embedding-3-small
- **Chat Model**: OpenAI GPT-4 for response generation
- **Deployment Target**: Hugging Face Spaces (Docker)

### Key Design Decisions
- **Authentication**: Public access with optional API key for rate limiting
- **Conversation State**: Short-term memory (last 3 messages) for context
- **Response Format**: Server-Sent Events (SSE) for streaming
- **Citations**: Embedded markdown format [Chapter - Section](source)
- **Dependencies**: Pure Python implementation (no LangChain)

### Data Flow
1. **Ingestion**: Markdown → Text chunks → Embeddings → Qdrant
2. **Query**: User question → Semantic search → Context retrieval → GPT-4 response → Streamed output with citations

## Constitution Check

### Security & Privacy
- ✅ No user data persistence beyond short-term memory
- ✅ API key validation for external services
- ✅ CORS properly configured for frontend domain
- ⚠️ **NEEDS CLARIFICATION**: Rate limiting strategy for public access

### Performance & Scalability
- ✅ Async architecture for concurrent requests
- ✅ Vector indexing for efficient semantic search
- ⚠️ **NEEDS CLARIFICATION**: Connection pooling for Qdrant

### Maintainability
- ✅ Modular architecture with separate concerns
- ✅ Pure Python implementation (no heavy dependencies)
- ✅ Clear separation of ingestion and serving logic

### Cost Management
- ✅ Efficient chunking to minimize API calls
- ⚠️ **NEEDS CLARIFICATION**: Token usage optimization strategies

## Phase 0: Research & Architecture Decisions

### Research Tasks

1. **FastAPI SSE Best Practices**
   - How to implement efficient Server-Sent Events
   - Memory management for streaming responses
   - Connection timeout handling

2. **Qdrant Integration Patterns**
   - Optimal collection schema for book chunks
   - Batch operations for ingestion
   - Filter strategies for metadata

3. **OpenAI API Optimization**
   - Batch embedding strategies
   - Token counting and rate limit handling
   - Error retry patterns

4. **Hugging Face Spaces Deployment**
   - Docker configuration best practices
   - Resource limits and optimizations
   - CI/CD integration patterns

## Phase 1: Design & Implementation

### Directory Structure
```
backend/
├── main.py              # FastAPI application entry point
├── pyproject.toml       # Python project config with uv
├── uv.lock             # Dependency lock file for reproducible builds
├── requirements.txt     # Legacy requirements file (backward compatibility)
├── Dockerfile          # HF Spaces deployment config (uses uv)
├── .env.example        # Environment variables template
├── rag/                # RAG package
│   ├── __init__.py
│   ├── chunking.py     # Text splitting logic
│   ├── embeddings.py   # OpenAI embedding generation
│   ├── vector_store.py # Qdrant operations
│   ├── retrieval.py    # Semantic search
│   └── generation.py   # Response generation
├── scripts/
│   └── ingest.py       # Document ingestion script
└── tests/              # Unit tests (optional)
```

### Implementation Tasks

#### 1. Project Setup
- [ ] Create backend directory structure
- [ ] Initialize pyproject.toml with uv configuration
- [ ] Generate uv.lock for reproducible builds
- [ ] Create .env.example with configuration variables
- [ ] Set up Python package structure
- [ ] Configure Dockerfile for uv installation

#### 2. RAG Core Implementation
- [ ] Implement RecursiveTextSplitter in chunking.py
- [ ] Create EmbeddingGenerator class in embeddings.py
- [ ] Implement QdrantManager in vector_store.py
- [ ] Build retrieval logic in retrieval.py
- [ ] Create response generation in generation.py

#### 3. FastAPI Application
- [ ] Set up FastAPI app with lifespan events
- [ ] Configure CORS middleware
- [ ] Implement /health endpoint
- [ ] Create /chat endpoint with SSE streaming
- [ ] Add /ingest endpoint for document processing

#### 4. Ingestion Pipeline
- [ ] Create markdown file discovery logic
- [ ] Implement batch embedding generation
- [ ] Build Qdrant upsert operations
- [ ] Add error handling and progress tracking

#### 5. Deployment Configuration
- [ ] Create Dockerfile for HF Spaces
- [ ] Configure non-root user (ID: 1000)
- [ ] Set port 7860 exposure
- [ ] Optimize for production deployment

## Phase 2: Integration & Testing

### Integration Tasks
- [ ] Test end-to-end ingestion pipeline
- [ ] Verify chat streaming functionality
- [ ] Test citation generation and formatting
- [ ] Validate conversation context management
- [ ] Test Docker build and deployment

### Performance Optimization
- [ ] Implement connection pooling
- [ ] Add caching for frequent queries
- [ ] Optimize chunk sizes for context limits
- [ ] Monitor and log performance metrics

## Risk Assessment

### Technical Risks
1. **OpenAI Rate Limits**: Implement exponential backoff and queueing
2. **Qdrant Connection Issues**: Add retry logic and health checks
3. **Memory Leaks**: Monitor streaming connections and cleanup
4. **Token Cost Overruns**: Implement usage tracking and limits

### Mitigation Strategies
- Comprehensive error handling with user-friendly messages
- Graceful degradation when services are unavailable
- Detailed logging for debugging and monitoring
- Rate limiting at the API level

## Success Criteria

### Functional Requirements
- ✅ All specified endpoints implemented
- ✅ Streaming responses work correctly
- ✅ Citations included in proper format
- ✅ Ingestion handles book content efficiently

### Performance Requirements
- ✅ Chat responses within 3 seconds
- ✅ Support 100 concurrent users
- ✅ 100ms vector search for 90% queries
- ✅ 99.5% uptime with zero data loss

### Deployment Requirements
- ✅ Successfully builds on HF Spaces
- ✅ Runs as non-root user (ID: 1000)
- ✅ Exposes port 7860 correctly
- ✅ Handles environment configuration

## Next Steps

1. Execute Phase 0 research tasks
2. Implement Phase 1 core functionality
3. Complete Phase 2 integration and testing
4. Deploy to Hugging Face Spaces
5. Monitor and optimize performance

## Dependencies

### External Services
- OpenAI API (embeddings and chat)
- Qdrant instance (vector storage)

### Python Packages
- fastapi >= 0.104.0
- uvicorn >= 0.24.0
- openai >= 1.3.0
- qdrant-client >= 1.6.0
- tiktoken >= 0.5.0
- python-multipart >= 0.0.6
- aiofiles >= 23.0.0

### Development Tools
- Docker Desktop
- Python 3.11+
- Git for version control