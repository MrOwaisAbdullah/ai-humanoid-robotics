# RAG Embedding System Quick Start Guide

**Purpose**: Get the RAG embedding system running with proper configuration to avoid template responses

## Prerequisites

1. **Python 3.11+** installed
2. **OpenAI API key** with access to text-embedding models
3. **Qdrant instance** (local or cloud)
4. **Book content** in markdown format

## Installation

```bash
# Clone repository
git clone <repository-url>
cd ai-book

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create `.env` file in project root:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=text-embedding-3-small

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key  # Optional for local

# Application Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
```

## Directory Structure

Ensure your book content follows this structure:

```
backend/
├── book_content/          # canonical source for book content
│   ├── chapter1.md
│   ├── chapter2.md
│   └── appendix.md
└── rag/
    ├── chat.py
    ├── chunking.py
    ├── ingestion.py
    └── retrieval.py
```

**Important**: Only content in `backend/book_content` will be ingested. Other directories like `docs/` are excluded to prevent duplication.

## Step 1: Verify Content

Check that your book content exists and contains actual content:

```bash
# List book content files
ls -la backend/book_content/

# Preview content (should not be just "How to Use This Book")
head -20 backend/book_content/chapter1.md
```

## Step 2: Clear Existing Data (if any)

```bash
# Clear Qdrant collection
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='http://localhost:6333')
client.delete_collection(collection_name='book_chunks')
print('Collection cleared')
"
```

## Step 3: Ingest Documents

```bash
# Run ingestion
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content_path": "./backend/book_content",
    "force_reindex": true,
    "config": {
      "chunk_size": 600,
      "chunk_overlap": 100,
      "exclude_patterns": ["*.draft", "README.md"],
      "template_patterns": [
        "^how to use this book$",
        "^table of contents$",
        "^foreword$",
        "^preface$"
      ]
    }
  }'
```

Expected response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Ingestion job started",
  "estimated_time": 45
}
```

## Step 4: Monitor Ingestion

```bash
# Check job status
curl http://localhost:8000/api/v1/ingest/550e8400-e29b-41d4-a716-446655440000

# Expected final status:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": {
    "files_processed": 15,
    "chunks_created": 1250,
    "chunks_skipped": 25,
    "percent_complete": 100
  }
}
```

## Step 5: Verify Health

```bash
# Check system health
curl http://localhost:8000/api/v1/health

# Expected metrics:
{
  "status": "healthy",
  "services": {
    "qdrant": {
      "status": "connected",
      "collection_count": 1,
      "vector_count": 1250
    }
  },
  "metrics": {
    "chunks_count": 1250,
    "last_ingestion": "2024-12-06T10:30:00Z"
  }
}
```

## Step 6: Test Chat Functionality

### Good Query Example

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main concepts in Physical AI?",
    "config": {
      "similarity_threshold": 0.7,
      "max_results": 5,
      "use_mmr": true,
      "exclude_templates": true
    }
  }'
```

**Expected Response**:
- Contains specific information from your book
- Sources point to actual chapters/sections
- No "How to Use This Book" in sources

### Bad Query Symptoms

If you see:
```json
{
  "response": "Based on the context provided, each source repeats 'How to Use This Book'...",
  "sources": [
    {
      "section_header": "How to Use This Book",
      "similarity_score": 0.89
    }
  ]
}
```

**Troubleshooting**:
1. Check if content was ingested: `/api/v1/health` → `chunks_count`
2. Verify content in `backend/book_content` has actual book content
3. Try lower `similarity_threshold` to 0.5 for testing
4. Check ingestion skipped template chunks

## Step 7: Advanced Configuration

### Custom Template Patterns

```python
# In backend/rag/ingestion.py
CUSTOM_TEMPLATES = [
    r'^how to use this book$',
    r'^table of contents$',
    r'^about this book$',
    r'^introduction to this edition$',
    r'^legal notices?$',
    r'^copyright \d{4}$'
]
```

### Similarity Threshold Tuning

```python
# For more diverse content
LOWER_THRESHOLD = 0.5

# For higher precision
HIGHER_THRESHOLD = 0.8

# Adaptive threshold (recommended)
USE_ADAPTIVE = True  # Adjusts based on result count
```

### Chunk Size Optimization

```python
# For technical content with code examples
SMALL_CHUNKS = 400

# For narrative content
LARGE_CHUNKS = 800
```

## Common Issues and Solutions

### Issue: All results are "How to Use This Book"

**Cause**: Wrong ingestion path or template filtering not working

**Solution**:
```bash
# Verify ingestion path
grep -r "ingest_directory" backend/rag/

# Check what was actually ingested
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Physical AI", "limit": 10}'
```

### Issue: No content found

**Cause**: Empty book_content directory or ingestion failed

**Solution**:
```bash
# Check files exist
find backend/book_content -name "*.md" | wc -l

# Re-ingest with force_reindex
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content_path": "./backend/book_content",
    "force_reindex": true
  }'
```

### Issue: Duplicates in results

**Cause**: De-duplication not enabled

**Solution**:
- Verify `backend/rag/retrieval.py` implements content hash filtering
- Check vector store for duplicate entries

## Testing Your Setup

Create a test script `test_rag.py`:

```python
import requests
import json

def test_query(query: str, expected_keywords: list):
    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json={"query": query, "config": {"exclude_templates": true}}
    )

    data = response.json()

    print(f"\nQuery: {query}")
    print(f"Response: {data['response'][:200]}...")
    print(f"Sources: {[s['section_header'] for s in data['sources']]}")

    # Check for template responses
    if "How to Use This Book" in data['response']:
        print("❌ ERROR: Template response detected!")
        return False

    # Check for expected keywords
    for keyword in expected_keywords:
        if keyword.lower() in data['response'].lower():
            print(f"✅ Found keyword: {keyword}")
        else:
            print(f"❌ Missing keyword: {keyword}")

    return True

# Test queries
test_query("What is Physical AI?", ["physical", "ai", "robotics"])
test_query("Explain the key concepts", ["concept", "chapter"])
test_query("Tell me about implementation", ["implement", "code", "example"])
```

## Production Tips

1. **Monitor**: Set up alerts for `similarity_threshold` failures
2. **Cache**: Implement query result caching for common questions
3. **Scaling**: Use batch processing for large documents
4. **Backup**: Regular vector store backups
5. **Analytics**: Track query patterns to improve content

## Next Steps

1. Run the full test suite: `pytest tests/`
2. Review logs for any warnings
3. Fine-tune parameters based on your specific content
4. Set up monitoring for production deployment