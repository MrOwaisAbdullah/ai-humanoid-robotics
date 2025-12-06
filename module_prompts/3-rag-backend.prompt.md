Use the `rag-pipeline-builder` skill to generate a production-ready RAG Backend API for our book.

**Context & Goals:**
This is Module 3. We need a robust backend to serve the chatbot for the "Physical AI & Humanoid Robotics" book. This backend will ingest the book's content (Markdown files) and serve answers via a streaming API. We will deploy this to **Hugging Face Spaces** (Docker SDK).

**Instructions for the Agent:**

1.  **Use Sub-Agent & Skills**:
    *   Delegate the core implementation to the **rag-specialist** sub-agent if available, or directly utilize the `rag-pipeline-builder` skill capabilities.
    *   Use the `rag-pipeline-builder` skill to scaffold the core architecture (ingestion, storage, retrieval).
    *   Use `mcp__context7__get-library-docs` to verify latest best practices for `fastapi` and `qdrant-client` if the skill templates need strict verification.

2.  **Customize for Deployment**:
    *   Update the `Dockerfile` to match **Hugging Face Spaces** requirements:
        *   Expose port **7860** (not 8000).
        *   Create a non-root user with ID **1000**.
        *   Set the working directory permissions correctly.

3.  **API Refinements**:
    *   Ensure the `/chat` endpoint supports **Server-Sent Events (SSE)** for compatibility with our frontend `chatbot-widget-creator`.
    *   Add a specific `POST /ingest` endpoint that triggers the `ingest_documents.py` logic (can be protected or run manually, but having the endpoint is useful for updates).
    *   Configure **CORS** to explicitly allow our GitHub Pages domain: `https://mrowaisabdullah.github.io`.

4.  **LangChain-Free Implementation**:
    *   Strictly adhere to the "LangChain-free" architecture provided by the skill. Use the pure Python `chunking_example.py` logic for splitting text.

5.  **Configuration**:
    *   Generate a `.env.example` that includes `OPENAI_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY`.

**Deliverables:**
- A complete `backend/` directory containing:
    - `main.py` (FastAPI app with lifespan events).
    - `rag/` package (chunking, embedding, vector logic).
    - `Dockerfile` (HF Spaces optimized).
    - `requirements.txt` (pinned versions).
    - `scripts/` (ingestion utilities).

**Constraint Checklist & Confidence Score:**
1. Use `rag-pipeline-builder` skill? Yes.
2. Hugging Face Spaces (Port 7860)? Yes.
3. Async/Await everywhere? Yes.
4. No LangChain? Yes.
5. Streaming SSE? Yes.

Confidence Score: 5/5

**Key Libraries:**
- `fastapi`, `uvicorn`, `openai`, `qdrant-client`, `tiktoken` (No langchain).

/sp.plan
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