# Research Findings: OpenAI Translation System

**Date**: 2025-12-12
**Feature**: 002-openai-translation

## 1. OpenAI Agents SDK + Gemini Integration

### Decision: Use Gemini 2.0 Flash via OpenAI-compatible endpoint

**Rationale**:

- Gemini 2.0 Flash offers fastest response times (critical for 3-second requirement)
- Native OpenAI-compatible endpoint simplifies integration
- Cost-effective for high-volume translation
- Good quality for Urdu translation tasks

**Configuration**:

```python
from agents import OpenAIChatCompletionsModel, AsyncOpenAI

provider = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_API_KEY"),
    timeout=60.0,
    max_retries=3,
)

model = OpenAIChatCompletionsModel(
    openai_client=provider,
    model="gemini-2.0-flash-lite",
    temperature=0.3,  # Lower for more consistent translations
)
```

**Alternatives considered**:

- Gemini 2.0 Pro: Higher quality but slower response times
- OpenAI GPT-4: Excellent quality but higher cost
- Custom fine-tuned model: Too complex for current scope

## 2. Translation Workflow Architecture

### Decision: Agent-based architecture with specialized tools

**Rationale**:

- Separates concerns (translation, formatting, caching)
- Extensible for future language support
- Better error handling and observability
- Aligns with OpenAI Agents SDK patterns

**Workflow**:

1. Content extraction from page
2. Structure analysis (headings, lists, code blocks)
3. Content chunking (2000 tokens with overlap)
4. Parallel translation using agents
5. Structure reconstruction
6. Caching of results

## 3. Content Chunking Strategy

### Decision: Urdu-aware recursive chunking

**Rationale**:

- Preserves Urdu script integrity
- Maintains context across chunks
- Handles mixed content (text + code)
- Optimized for Gemini's token limits

**Implementation**:

```python
def chunk_content_for_translation(content: str) -> List[ContentChunk]:
    """Split content into chunks optimized for Urdu translation"""
    # 1. Extract and preserve code blocks
    # 2. Split text content at semantic boundaries
    # 3. Ensure each chunk ≤ 2000 tokens
    # 4. Add 200 token overlap between chunks
```

## 4. Error Handling Patterns

### Decision: Circuit breaker with exponential backoff

**Rationale**:

- Prevents cascade failures
- Handles rate limits gracefully
- Provides good user experience
- Maintains system stability

**Implementation**:

```python
class TranslationCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.last_failure_time = None
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

## 5. Caching Strategy

### Decision: Multi-level caching with content hash keys

**Rationale**:

- Reduces API costs significantly
- Improves response time for repeated requests
- Detects content changes automatically
- Scales with user growth

**Implementation**:

- **L1**: In-memory cache (Redis) - 1 hour TTL
- **L2**: Persistent cache (SQLite) - 24 hours TTL
- **Key**: `hash(page_url + content_hash + target_language)`

## 6. Urdu-Specific Considerations

### Decision: Normalize script and handle technical terms

**Rationale**:

- Urdu has multiple valid forms for some characters
- Technical terms may not have direct translations
- Cultural context matters for formal content

**Implementation**:

```python
def normalize_urdu_script(text: str) -> str:
    """Normalize Urdu script for consistent translation"""
    # Handle hamza variants: ۔, ئ, ء
    # Handle yeh variants: ی, ے
    # Handle heh variants: ہ, ۃ
```

## 7. Performance Optimization

### Decision: Streaming with parallel processing

**Rationale**:

- Meets 3-second response requirement
- Provides real-time feedback
- Optimizes resource utilization
- Scales to multiple users

**Implementation**:

- Process chunks in parallel (max 3 concurrent)
- Stream results as they complete
- Maintain order in final output
- Show progress indicator to user

## 8. Security Considerations

### Decision: Validate all inputs and sanitize outputs

**Rationale**:

- Prevent injection attacks
- Ensure content integrity
- Comply with data privacy
- Handle malicious input gracefully

**Implementation**:

- Input validation for content size
- Sanitization of HTML/CSS
- Rate limiting per user/IP
- Logging of all translation requests

## 9. Testing Strategy

### Decision: Multi-tier testing with real content

**Rationale**:

- Ensure translation quality
- Verify performance requirements
- Test edge cases thoroughly
- Monitor production health

**Implementation**:

- Unit tests for each component
- Integration tests for workflow
- E2E tests with sample pages
- Performance tests with load simulation

## 10. Monitoring and Observability

### Decision: Comprehensive logging with metrics

**Rationale**:

- Track system health
- Identify bottlenecks
- Measure translation quality
- Optimize based on usage patterns

**Implementation**:

- Request/response logging
- Performance metrics (latency, throughput)
- Error tracking and alerting
- Usage analytics and reporting

## Summary

The research phase has identified all key decisions needed for implementation. The chosen approach balances:

- Performance (3-second response times)
- Quality (accurate Urdu translations)
- Scalability (handles growing user base)
- Maintainability (clean, modular code)
- Cost-effectiveness (optimized API usage)

Next phase will involve creating detailed data models and API contracts based on these decisions.
