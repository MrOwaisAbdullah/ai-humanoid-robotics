# Research Findings: RAG Embedding System Fix

**Generated**: 2025-12-06
**Purpose**: Resolve technical uncertainties for Phase 1 design

## 1. Optimal Chunk Size for OpenAI Embeddings

### Decision: 600 tokens with 100 token overlap

**Rationale**:
- OpenAI's text-embedding-3-small has an 8191 token context window
- Research shows 400-800 tokens provides optimal semantic coherence
- 600 tokens balances context preservation and retrieval precision
- 100 token overlap (16.7%) ensures no information loss at boundaries

**Implementation Details**:
```python
import tiktoken

def count_tokens(text: str) -> int:
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    return len(encoding.encode(text))

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    # Implement with tiktoken for accurate token counting
```

**Alternatives Considered**:
- 400 tokens: More granular but increases retrieval noise
- 800 tokens: Better context but reduces precision for specific queries
- Fixed character count: Inaccurate due to variable token length

## 2. Content De-duplication Strategy

### Decision: SHA256 content hashing with metadata storage

**Rationale**:
- SHA256 provides collision-resistant hashing
- Fast computation (O(n) where n is chunk length)
- Small storage overhead (64 characters per chunk)
- Enables O(1) duplicate detection

**Implementation Approach**:
```python
import hashlib

def generate_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

# Store in Qdrant metadata
metadata = {
    "content_hash": hash_value,
    "source_file": file_path,
    "section_header": header
}
```

**Performance Impact**:
- Negligible overhead during ingestion (~1ms per chunk)
- No impact on retrieval speed
- Memory increase: ~64 bytes per chunk

## 3. Maximal Marginal Relevance (MMR)

### Decision: Implement basic MMR with lambda=0.5

**Rationale**:
- MMR reduces redundancy in retrieved results
- Lambda=0.5 balances relevance and diversity
- Simple implementation improves results without complex dependencies

**Algorithm**:
```python
def maximal_marginal_relevance(query_embedding, doc_embeddings, lambda_param=0.5, k=5):
    selected = []
    remaining = list(range(len(doc_embeddings)))

    while len(selected) < k and remaining:
        # Select document maximizing: λ * similarity - (1-λ) * max_sim_to_selected
        best_score = -float('inf')
        best_idx = None

        for idx in remaining:
            relevance = cosine_similarity(query_embedding, doc_embeddings[idx])
            max_similarity = max([
                cosine_similarity(doc_embeddings[idx], doc_embeddings[s])
                for s in selected
            ], default=0)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(best_idx)
        remaining.remove(best_idx)

    return selected
```

**Alternatives Considered**:
- Full semantic search with reranking: More complex, higher latency
- Keyword hybrid search: Better for exact matches, less semantic
- No diversification: Current issue (all results identical)

## 4. Template Content Filtering

### Decision: Configurable regex patterns for header exclusion

**Rationale**:
- Templates follow predictable patterns
- Regex provides flexible matching
- Configurable allows adaptation to different books

**Implementation**:
```python
import re

DEFAULT_TEMPLATES = [
    r'^how to use this book$',
    r'^table of contents$',
    r'^foreword$',
    r'^preface$',
    r'^about the author$',
    r'^copyright$',
    r'^acknowledgments$'
]

def is_template_header(header: str, patterns: List[str] = None) -> bool:
    if patterns is None:
        patterns = DEFAULT_TEMPLATES

    header_lower = header.lower().strip()
    return any(re.match(pattern, header_lower, re.IGNORECASE) for pattern in patterns)
```

**Configuration**:
```python
# In settings.py
TEMPLATE_EXCLUSION_PATTERNS = [
    r'^how to use this book$',
    r'^table of contents$',
    # Add custom patterns per book
]
```

## 5. Similarity Threshold Optimization

### Decision: Dynamic threshold starting at 0.7

**Rationale**:
- 0.7 eliminates low-quality matches
- Dynamic adjustment based on result count
- Prevents empty results for edge cases

**Implementation**:
```python
def get_adaptive_threshold(initial_threshold: float = 0.7,
                          min_results: int = 3,
                          max_results: int = 5) -> float:
    """
    Dynamically adjust threshold to ensure sufficient results
    """
    threshold = initial_threshold

    while threshold > 0.3:  # Minimum threshold
        results = search_with_threshold(threshold)
        if len(results) >= min_results:
            break
        threshold -= 0.1

    return threshold
```

## 6. OpenAI Embedding Model Selection

### Decision: text-embedding-3-small

**Rationale**:
- 5x cheaper than text-embedding-ada-002
- Better multilingual capabilities
- Dimension: 1536 (manageable for Qdrant free tier)
- Performance: Comparable to ada-002 for most use cases

**Cost Analysis**:
- text-embedding-3-small: $0.02 per 1M tokens
- text-embedding-3-large: $0.13 per 1M tokens
- For 1000 chunks ~600K tokens: ~$0.012 vs $0.078

## 7. Error Handling Strategy

### Decision: Comprehensive error categorization with user-friendly messages

**Implementation Categories**:
1. **Input Validation Errors** (400): Malformed requests, missing required fields
2. **Content Errors** (422): No content found, empty documents
3. **API Errors** (502/503): OpenAI rate limits, Qdrant unavailability
4. **System Errors** (500): Unexpected failures, always logged

**Example Responses**:
```json
{
  "error": {
    "code": "NO_CONTENT_FOUND",
    "message": "No relevant content found in the book. Try rephrasing your question.",
    "details": "Query: 'tell me about this book' returned 0 results above threshold"
  }
}
```

## 8. Performance Optimizations

### Identified Optimizations:

1. **Batch Embedding Generation**
   - Process multiple chunks in parallel
   - Respect OpenAI rate limits (3000 RPM)

2. **Caching Strategy**
   - Cache frequently asked questions
   - TTL: 1 hour for content responses

3. **Connection Pooling**
   - Reuse Qdrant connections
   - Implement async HTTP client

4. **Vector Store Optimization**
   - Use HNSW indexing for faster search
   - Optimize ef_search parameter (default 128)

## Summary of Decisions

All technical clarifications resolved with specific implementation approaches. Research indicates:
- 600-token chunks with 100-token overlap optimal for semantic coherence
- SHA256 hashing provides efficient de-duplication
- MMR with λ=0.5 improves result diversity
- Configurable template filtering handles various book structures
- Dynamic similarity thresholds prevent empty results while maintaining quality