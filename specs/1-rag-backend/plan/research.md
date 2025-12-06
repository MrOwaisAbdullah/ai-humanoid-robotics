# Research Findings: RAG Backend API

**Date**: 2025-01-05
**Feature**: 1-rag-backend

## 1. Rate Limiting Strategy for Public Access

### Decision
**Chosen**: Implement token bucket rate limiting at FastAPI middleware level
- **Default**: 10 requests per minute per IP
- **With API Key**: 100 requests per minute
- **Burst capacity**: 20 requests for default, 200 for API key

### Rationale
- Prevents abuse while allowing reasonable usage
- API key users get higher limits (premium features)
- Simple to implement with `slowapi` library
- Compatible with HF Spaces deployment

### Implementation
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request):
    pass

@app.post("/chat")
@limiter.limit("100/minute", key_func=lambda: request.headers.get("x-api-key"))
async def chat_endpoint_premium(request: Request):
    pass
```

## 2. Qdrant Connection Pooling

### Decision
**Chosen**: Use async Qdrant client with connection pooling
- Configure max connections per host
- Implement connection health checks
- Use Qdrant Async client for better performance

### Rationale
- Reduces connection overhead
- Handles concurrent requests efficiently
- Built-in retry mechanisms
- Better resource management

### Implementation
```python
from qdrant_client import AsyncQdrantClient

# Initialize with connection pooling
qdrant_client = AsyncQdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    https=True,
    timeout=30,
    # Connection pooling parameters
    prefer_grpc=True,  # Use gRPC for better performance
    grpc_options={
        "grpc.keepalive_time_ms": 30000,
        "grpc.keepalive_timeout_ms": 5000,
        "grpc.http2.max_pings_without_data": 0,
        "grpc.http2.min_time_between_pings_ms": 10000,
        "grpc.http2.min_ping_interval_without_data_ms": 300000
    }
)
```

## 3. Token Usage Optimization

### Decision
**Chosen**: Implement intelligent token management
- Track token usage per request
- Implement context window optimization
- Use caching for repeated embeddings
- Batch process embeddings during ingestion

### Rationale
- Reduces OpenAI API costs
- Improves response speed
- Allows for usage monitoring
- Prevents token limit errors

### Implementation Strategies

#### Context Optimization
```python
def optimize_context(chunks, question, max_tokens=3000):
    """Optimize context to fit within token limits"""
    # Calculate approximate tokens
    question_tokens = len(question.split()) * 1.3  # Rough estimate

    # Select most relevant chunks first
    sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)

    selected_chunks = []
    used_tokens = question_tokens

    for chunk in sorted_chunks:
        chunk_tokens = len(chunk.text.split()) * 1.3
        if used_tokens + chunk_tokens < max_tokens:
            selected_chunks.append(chunk)
            used_tokens += chunk_tokens
        else:
            break

    return selected_chunks
```

#### Embedding Caching
```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding_cache_key(text):
    """Generate cache key for embeddings"""
    return hashlib.md5(text.encode()).hexdigest()

async def get_cached_embedding(text):
    """Get embedding with caching"""
    cache_key = get_embedding_cache_key(text)

    # Check Redis cache first
    cached = await redis.get(f"embedding:{cache_key}")
    if cached:
        return json.loads(cached)

    # Generate new embedding
    embedding = await openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    # Cache for 24 hours
    await redis.setex(
        f"embedding:{cache_key}",
        86400,
        json.dumps(embedding.data[0].embedding)
    )

    return embedding.data[0].embedding
```

## 4. FastAPI SSE Best Practices

### Decision
**Chosen**: Use Server-Sent Events with proper memory management
- Implement backpressure handling
- Use async generators for streaming
- Add connection timeout handling
- Implement proper cleanup on disconnect

### Rationale
- Provides real-time streaming experience
- Efficient memory usage
- Handles concurrent connections
- Graceful error handling

### Implementation
```python
from fastapi.responses import StreamingResponse
import asyncio

async def generate_chat_stream(question: str, context: list):
    """Generate streaming chat response"""
    try:
        # Generate response with citations
        async for chunk in generate_response_with_citations(question, context):
            # Format as SSE
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.01)  # Prevent overwhelming client

        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        # Send error message
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint with SSE streaming"""
    # Validate request
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")

    # Get relevant context
    context = await get_relevant_context(request.question)

    # Return streaming response
    return StreamingResponse(
        generate_chat_stream(request.question, context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

## 5. Hugging Face Spaces Optimization

### Decision
**Chosen**: Optimize Docker image for HF Spaces
- Use multi-stage builds
- Minimize image size
- Implement proper health checks
- Configure resource limits

### Rationale
- Faster deployment times
- Lower resource usage
- Better performance
- Reliable health monitoring

### Implementation
```dockerfile
# Multi-stage Dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Change ownership
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Expose port 7860 (HF Spaces)
EXPOSE 7860

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

## 6. Monitoring and Observability

### Decision
**Chosen**: Implement comprehensive monitoring
- Structured logging
- Performance metrics
- Error tracking
- Usage analytics

### Implementation
```python
import structlog
from prometheus_client import Counter, Histogram, Gauge

# Configure structured logging
logger = structlog.get_logger()

# Metrics
chat_requests = Counter('chat_requests_total', description='Total chat requests')
chat_duration = Histogram('chat_duration_seconds', description='Chat response duration')
active_connections = Gauge('active_connections', description='Active SSE connections')

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info("Request started",
                method=request.method,
                url=str(request.url),
                client_ip=request.client.host)

    try:
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info("Request completed",
                    status_code=response.status_code,
                    duration=duration)

        return response

    except Exception as e:
        logger.error("Request failed",
                    error=str(e),
                    duration=time.time() - start_time)
        raise
```

## Summary

All research tasks completed with clear decisions:
1. ✅ Rate limiting strategy defined (token bucket with API key tiers)
2. ✅ Qdrant connection pooling specified (async client with gRPC)
3. ✅ Token optimization strategy implemented (caching, batching, context optimization)
4. ✅ FastAPI SSE patterns documented (async generators, backpressure handling)
5. ✅ HF Spaces Docker optimization defined (multi-stage builds, resource limits)
6. ✅ Monitoring and observability plan created (structured logging, metrics)

The implementation can proceed with these architectural decisions in place.