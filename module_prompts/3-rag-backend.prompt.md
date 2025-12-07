Use the `rag-pipeline-builder` skill to generate a production-ready RAG Backend API for our book.

**Context & Goals:**
This is Module 3. We need a robust backend to serve the chatbot for the "Physical AI & Humanoid Robotics" book. This backend will ingest the book's content (Markdown files) and serve answers via a streaming API (Server-Sent Events) to our custom React frontend. We will deploy this to **Hugging Face Spaces** (Docker SDK).

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
        *   CMD should be: `uvicorn main:app --host 0.0.0.0 --port 7860`.

3.  **API Refinements**:
    *   **Endpoint Protocol**: The `/chat` endpoint MUST return **Server-Sent Events (SSE)**.
        *   Format: `data: {"content": "text chunk", "done": false}\n\n`
        *   Metadata Event: `data: {"metadata": {...}, "done": false}\n\n` (First event)
        *   Done Event: `data: {"done": true}\n\n`
    *   **Ingestion**:
        *   Add a `POST /ingest` endpoint that triggers the `ingest_documents.py` logic.
        *   Ensure it can read files from the `book_content` directory (copied into the image or mounted).
    *   **CORS**:
        *   Configure `CORSMiddleware` to explicitly allow our GitHub Pages domain: `https://mrowaisabdullah.github.io` and `http://localhost:3000` for dev.

4.  **LangChain-Free Implementation**:
    *   Strictly adhere to the "LangChain-free" architecture provided by the skill.
    *   Use the pure Python `chunking_example.py` logic for splitting text, but apply the **`min_chunk_size=50`** improvement we identified to filter out empty headers.
    *   Implement **deduplication** in the retrieval logic (fetch 2x `top_k`, then filter unique text content) as identified in our RAG analysis.

5.  **Configuration**:
    *   Generate a `.env.example` that includes `OPENAI_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY`.

**Deliverables:**
- A complete `backend/` directory containing:
    - `main.py` (FastAPI app with lifespan events).
    - `rag/` package (chunking, embedding, vector logic).
    - `Dockerfile` (HF Spaces optimized, Port 7860).
    - `requirements.txt` (pinned versions).
    - `scripts/` (ingestion utilities).

**Constraint Checklist & Confidence Score:**
1. Use `rag-pipeline-builder` skill? Yes.
2. Hugging Face Spaces (Port 7860)? Yes.
3. SSE Streaming (Custom Format)? Yes.
4. No LangChain? Yes.
5. Deduplication & Min Chunk Size? Yes.

Confidence Score: 5/5

**Key Libraries:**
- `fastapi`, `uvicorn`, `openai`, `qdrant-client`, `tiktoken` (No langchain).

/sp.plan
1.  **Scaffold Backend Structure**:
    *   Create `backend/` directory.
    *   Create `backend/rag/` package for core logic.
    *   Initialize `requirements.txt`.

2.  **Implement RAG Core (Enhanced)**:
    *   `backend/rag/chunking.py`: Port `RecursiveTextSplitter` with `min_chunk_size` fix.
    *   `backend/rag/embeddings.py`: Implement `EmbeddingGenerator` using `AsyncOpenAI`.
    *   `backend/rag/vector_store.py`: Implement `QdrantManager`.
    *   `backend/rag/retrieval.py`: Implement deduplication logic (fetch 2x, filter).

3.  **Develop API Endpoints**:
    *   `backend/main.py`:
        *   Setup FastAPI app with Lifespan events.
        *   Add CORS for GitHub Pages.
        *   Implement `POST /chat`: Streaming endpoint using `StreamingResponse` with SSE format.
        *   Implement `POST /ingest`: Trigger ingestion.
        *   Implement `GET /health`.

4.  **Ingestion Logic**:
    *   `backend/scripts/ingest.py`: Script to traverse `backend/book_content/`, chunk, embed, upsert.

5.  **Deployment Configuration**:
    *   `backend/Dockerfile`: HF Spaces optimized (Port 7860, User 1000).
    *   `backend/.env.example`.
