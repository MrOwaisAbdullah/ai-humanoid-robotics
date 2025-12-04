/sp.specify
Build the RAG (Retrieval-Augmented Generation) Backend API.

**Context & Goals:**
This is Module 3. We need a robust backend to serve the chatbot. We will deploy this to **Hugging Face Spaces** (Docker SDK).

**Requirements:**

1.  **Framework**: FastAPI (Python 3.11+).
    *   *Action*: Use `mcp__context7__get-library-docs` with libraryID="fastapi" for best practices (Lifespan events, Dependency Injection).
2.  **Vector Database**: Qdrant Cloud.
    *   *Action*: Use `mcp__context7__get-library-docs` with libraryID="qdrant" for the latest Python client usage (AsyncQdrantClient).
3.  **LLM & Embeddings**: OpenAI.
    *   Embeddings: `text-embedding-3-small`.
    *   Chat: `gpt-4o-mini`.
    *   *Action*: Use `mcp__context7__get-library-docs` with libraryID="openai" for the latest Async API usage.
4.  **API Endpoints**:
    *   `POST /embed`: Ingests the markdown files (receives text or path), chunks them (RecursiveCharacterTextSplitter or similar), embeds them, and upserts to Qdrant.
    *   `POST /chat`: Accepts `messages` and `user_id`. Performs semantic search in Qdrant, retrieves context, and generates a response using OpenAI.
    *   `POST /chat/selection`: Accepts `selected_text`, `surrounding_context`, and `question`. Restricts context to the selection (or prioritizes it).
    *   `GET /health`: Simple health check.
5.  **Streaming**:
    *   Implement Server-Sent Events (SSE) or standard chunked streaming for the `/chat` endpoints to allow real-time text display on the frontend.
6.  **Deployment (Hugging Face Spaces)**:
    *   Create a `Dockerfile` optimized for Hugging Face Spaces (user 1000, port 7860).
    *   Create `requirements.txt` with pinned versions.
    *   Instructions for setting Secrets in HF Spaces.

**Technical Constraints:**
- Use Async/Await everywhere.
- Robust error handling (try/except blocks with proper HTTPExceptions).
- CORS middleware configured to allow the GitHub Pages frontend.

**Deliverable:**
- A complete `backend/` (or `chatbot/`) directory with `main.py`, `Dockerfile`, and helper modules for RAG logic.
