---
name: rag-pipeline-builder
description: Complete RAG (Retrieval-Augmented Generation) pipeline implementation with document ingestion, vector storage, semantic search, and response generation. Supports FastAPI backends with OpenAI and Qdrant.
category: backend
version: 1.0.0
---

# RAG Pipeline Builder Skill

## Purpose

Quickly scaffold and implement production-ready RAG systems with:
- Intelligent document chunking strategies
- Vector embeddings generation (OpenAI)
- Vector storage and retrieval (Qdrant)
- Context-aware response generation
- Streaming API endpoints

## When to Use This Skill

Use this skill when:
- Building Q&A systems over custom documents
- Creating chatbots with knowledge bases
- Implementing semantic search
- Adding AI-powered assistance to documentation

## Core Capabilities

### 1. Document Chunking Strategies

**Strategy Selection Matrix:**

| Document Type | Chunk Size | Overlap | Strategy |
|---------------|------------|---------|----------|
| Technical docs | 1000 tokens | 200 tokens | Recursive (preserve code blocks) |
| Narrative text | 800 tokens | 150 tokens | Sentence-based |
| API reference | 600 tokens | 100 tokens | Section-based |
| Mixed content | 1000 tokens | 200 tokens | Markdown-aware |

**Implementation Template:**
```python
# See scripts/chunking_example.py for complete implementation

from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

class IntelligentChunker:
    """
    Markdown-aware chunking that preserves structure
    """

    def __init__(self, chunk_size=1000, overlap=200):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=self._count_tokens,
            separators=[
                "\n\n\n",  # Major sections
                "\n\n",    # Paragraphs
                "\n",      # Lines
                ". ",      # Sentences
                " ",       # Words
                "",        # Characters
            ],
            keep_separator=True,
        )

    def _count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def chunk_document(self, text: str, metadata: dict) -> list:
        # Protect code blocks from splitting
        text = self._protect_code_blocks(text)
        chunks = self.splitter.split_text(text)
        text = self._restore_code_blocks(text)

        return [
            {
                "text": chunk,
                "metadata": {**metadata, "chunk_index": i}
            }
            for i, chunk in enumerate(chunks)
        ]
```

### 2. Embedding Generation

**Best Practices:**
```python
from openai import AsyncOpenAI
import asyncio

class EmbeddingGenerator:
    """
    Efficient batch embedding with rate limiting
    """

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"  # 1536 dimensions, cost-effective

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100
    ) -> list[list[float]]:
        """
        Embed multiple texts with batching and error handling
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                # Rate limiting (3000 RPM for tier 1)
                await asyncio.sleep(0.02)  # 20ms between batches

            except Exception as e:
                print(f"Batch {i//batch_size} failed: {e}")
                # Implement exponential backoff here
                raise

        return all_embeddings
```

### 3. Qdrant Integration

**Collection Setup:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class QdrantManager:
    """
    Qdrant collection management and search
    """

    def __init__(self, url: str, api_key: str):
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = "book_content"

    def create_collection(self, vector_size: int = 1536):
        """
        Create collection with optimal settings
        """
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,  # Best for semantic similarity
            ),
            # Optimize for search speed
            optimizers_config={
                "default_segment_number": 2,
            },
            # Enable payload indexing for filtering
            payload_schema={
                "chapter": {"type": "keyword"},
                "section": {"type": "keyword"},
            }
        )

    def upsert_documents(self, documents: list[dict]):
        """
        Batch upsert with proper point structure
        """
        points = [
            PointStruct(
                id=i,
                vector=doc["embedding"],
                payload={
                    "text": doc["text"],
                    **doc["metadata"],
                },
            )
            for i, doc in enumerate(documents)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filters: dict = None,
    ) -> list:
        """
        Semantic search with optional filtering
        """
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=self._build_filter(filters) if filters else None,
            score_threshold=0.7,  # Minimum relevance score
        )
```

### 4. FastAPI Endpoints

**Template:** (see `templates/fastapi-endpoint-template.py`)
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    context: dict = {}

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Streaming chat endpoint with RAG
    """
    try:
        # 1. Embed query
        query_embedding = await embedder.embed(request.message)

        # 2. Retrieve relevant chunks
        results = qdrant.search(query_embedding, top_k=5)

        # 3. Build context
        context = "\n\n".join([r.payload["text"] for r in results])

        # 4. Generate response (streaming)
        async def generate():
            async for token in openai_generator.stream(
                query=request.message,
                context=context,
            ):
                yield token

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. Complete RAG Pipeline

**End-to-End Implementation:**
```python
class RAGPipeline:
    """
    Orchestrates complete RAG workflow
    """

    def __init__(self, config):
        self.chunker = IntelligentChunker()
        self.embedder = EmbeddingGenerator(config.openai_key)
        self.qdrant = QdrantManager(config.qdrant_url, config.qdrant_key)
        self.generator = ResponseGenerator(config.openai_key)

    async def ingest_documents(self, file_paths: list[str]):
        """
        Ingest documents into vector store
        """
        all_chunks = []

        for path in file_paths:
            # Read document
            with open(path) as f:
                content = f.read()

            # Extract metadata
            metadata = self._extract_metadata(path)

            # Chunk document
            chunks = self.chunker.chunk_document(content, metadata)
            all_chunks.extend(chunks)

        # Generate embeddings
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = await self.embedder.embed_batch(texts)

        # Add embeddings to chunks
        for chunk, embedding in zip(all_chunks, embeddings):
            chunk["embedding"] = embedding

        # Store in Qdrant
        self.qdrant.upsert_documents(all_chunks)

        return {
            "documents_processed": len(file_paths),
            "chunks_created": len(all_chunks),
            "status": "success"
        }

    async def query(self, question: str, selected_text: str = None):
        """
        Query pipeline with streaming response
        """
        # Embed query
        query_embedding = await self.embedder.embed(question)

        # Retrieve relevant chunks
        filters = None
        if selected_text:
            # Boost chunks from same page if text selected
            filters = {"page_has_selection": True}

        results = self.qdrant.search(query_embedding, top_k=5, filters=filters)

        # Generate response
        async for token in self.generator.stream(
            query=question,
            context=results,
            selected_text=selected_text,
        ):
            yield token
```

## Usage Instructions

### Basic Ingestion
```python
# Initialize pipeline
pipeline = RAGPipeline(config)

# Ingest all markdown files
await pipeline.ingest_documents([
    "docs/chapter-1.md",
    "docs/chapter-2.md",
    # ... more files
])
```

### Query with Text Selection
```python
# User selected text and asked a question
async for token in pipeline.query(
    question="What does this mean?",
    selected_text="The text user highlighted...",
):
    print(token, end="", flush=True)
```

## Quality Metrics

Track these metrics for RAG quality:
```python
# Retrieval Quality
- Precision@5: % of top 5 results that are relevant
- Recall@5: % of relevant docs in top 5
- MRR (Mean Reciprocal Rank): 1/rank of first relevant result

# Generation Quality
- Groundedness: % of claims supported by retrieved context
- Relevance: How well answer addresses question
- Coherence: Readability and logical flow

# Performance
- Retrieval latency: < 500ms
- First token latency: < 1s
- Streaming latency: < 100ms per token
```

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Low relevance scores | Poor chunking | Adjust chunk size, use semantic splitting |
| Slow retrieval | Too many vectors | Add filters, reduce top_k |
| Irrelevant responses | Weak retrieval | Improve embeddings, add re-ranking |
| High costs | Too many API calls | Cache embeddings, batch requests |

## Integration with Subagents

**Use with:**
- **rag-specialist** subagent: For implementing this pipeline
- **deployment-engineer** subagent: For deploying to production

## Output Format

When this skill is invoked, provide:
1. **Complete Pipeline Code** (all components)
2. **Configuration File** (.env.example)
3. **Ingestion Script** (scripts/ingest_documents.py)
4. **FastAPI Endpoints** (api/routes/chat.py)
5. **Testing Script** (scripts/test_rag.py)
6. **Performance Metrics** (expected latency, costs)

## Time Savings

**Without this skill:** 8-12 hours to implement RAG from scratch
**With this skill:** 30-45 minutes to generate and customize

Efficiency gain: **~95% time reduction**