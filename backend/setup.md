# RAG Backend Setup Guide

Complete guide to set up and deploy the RAG backend for the Physical AI & Humanoid Robotics book.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Qdrant Setup](#qdrant-setup)
4. [Book Content Preparation](#book-content-preparation)
5. [Ingestion Process](#ingestion-process)
6. [Testing the API](#testing-the-api)
7. [Hugging Face Spaces Deployment](#hugging-face-spaces-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Configuration Reference](#configuration-reference)

## Prerequisites

### Required Software
- Python 3.11+
- Docker Desktop (for local Qdrant)
- Git
- OpenAI API account with credits

### Required Accounts/Services
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [Hugging Face Account](https://huggingface.co/join) (for deployment)

## Local Setup

### 1. Clone and Navigate

```bash
# Navigate to the backend directory
cd D:\GIAIC\Quarter 4\ai-book\backend
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Or (Mac/Linux)
source venv/bin/activate
```

### 3. Install uv and Dependencies

#### Option A: Using uv (Recommended - 10-100x faster)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install project dependencies
uv sync

# For development dependencies (includes testing, linting)
uv sync --dev

# Verify installation
uv run python -c "import fastapi, openai, qdrant_client, uvicorn; print('All dependencies installed successfully')"
```

#### Option B: Using pip (Legacy)

```bash
# Install dependencies (slower, not recommended)
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(fastapi|openai|qdrant|uvicorn)"
```

### 4. Configure Environment

Create a `.env` file from the template:

```bash
# Copy the template
copy .env.example .env
```

Edit `.env` with your configuration:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local instance

# Content Path
BOOK_CONTENT_PATH=./book_content

# API Configuration
API_HOST=0.0.0.0
API_PORT=7860
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# Conversation Settings
MAX_CONTEXT_MESSAGES=3
CONTEXT_WINDOW_SIZE=4000

# Ingestion Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
BATCH_SIZE=100
MAX_CONCURRENT_REQUESTS=10
```

## Qdrant Setup

### Option 1: Local Docker Instance (Recommended for Development)

```bash
# Pull and run Qdrant
docker run -d ^
  --name qdrant ^
  -p 6333:6333 ^
  -p 6334:6334 ^
  -v qdrant_storage:/qdrant/storage ^
  qdrant/qdrant:latest

# Verify it's running
docker ps
```

### Option 2: Qdrant Cloud (For Production)

1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a new cluster
3. Get your cluster URL and API key
4. Update `.env`:
   ```env
   QDRANT_URL=https://your-cluster-url.qdrant.io
   QDRANT_API_KEY=your-cloud-api-key
   ```

### Option 3: Local Installation

```bash
# Install Qdrant locally
pip install qdrant-client[fastembed]

# Run Qdrant server
qdrant --host 0.0.0.0 --port 6333
```

## Book Content Preparation

### 1. Create Content Directory

```bash
# Create the book content directory
mkdir book_content
```

### 2. Organize Your Book Files

Place your Markdown files in the following structure:

```
book_content/
├── README.md              # Optional: Book overview
├── chapter1_introduction.md
├── chapter2_fundamentals.md
├── chapter3_kinematics.md
├── chapter4/
│   ├── section1.md
│   ├── section2.md
│   └── subsections/
│       └── sub1.md
├── chapter5_dynamics.md
├── appendix_a.md
└── glossary.md
```

### 3. File Naming Best Practices

- Use descriptive names with lowercase and underscores
- Include chapter numbers for ordering: `chapter1_introduction.md`
- Keep filenames under 50 characters
- Use only `.md` extension

### 4. Content Formatting Tips

Each Markdown file should:

```markdown
# Chapter Title

## Section 1: Introduction

Content here with proper formatting.

### Subsection

More detailed content.

#### Code Examples

```python
# Code blocks will be extracted as separate chunks
def example():
    return "Hello"
```

## Section 2: Advanced Topics

More content...
```

## Ingestion Process

### Option 1: Using the Python Script (Recommended)

#### Using uv (Recommended)

```bash
# Basic ingestion
uv run python scripts/ingest.py --content-path ./book_content

# With custom parameters
uv run python scripts/ingest.py ^
  --content-path ./book_content ^
  --chunk-size 800 ^
  --chunk-overlap 150 ^
  --batch-size 50

# Force reindex (clears existing data)
uv run python scripts/ingest.py ^
  --content-path ./book_content ^
  --force-reindex

# Or using the script command defined in pyproject.toml
uv run rag-ingest --content-path ./book_content
```

#### Using pip directly

```bash
# If you installed with pip
python scripts/ingest.py --content-path ./book_content
```

### Option 2: Using the API Endpoint

```bash
# Start the server first
uvicorn main:app --reload

# In another terminal, trigger ingestion
curl -X POST "http://localhost:7860/ingest" ^
  -H "Content-Type: application/json" ^
  -d '{
    "content_path": "./book_content",
    "force_reindex": false,
    "batch_size": 100
  }'
```

### Monitor Ingestion Progress

```bash
# Check task status
curl "http://localhost:7860/ingest/status"

# Get specific task status (replace TASK_ID)
curl "http://localhost:7860/ingest/status?task_id=TASK_ID"

# View ingestion statistics
curl "http://localhost:7860/ingest/stats"
```

## Testing the API

### 1. Start the Server

#### Using uv (Recommended)

```bash
# Development mode with auto-reload
uv run uvicorn main:app --host 0.0.0.0 --port 7860 --reload

# Production mode
uv run uvicorn main:app --host 0.0.0.0 --port 7860

# Or using the script command defined in pyproject.toml
uv run rag-server
```

#### Using pip directly

```bash
# If you installed with pip
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

### 2. Health Check

```bash
curl http://localhost:7860/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 45.2,
  "services": {
    "qdrant": {"status": "healthy"},
    "openai": {"status": "configured"},
    "task_manager": {"status": "healthy"}
  },
  "metrics": {
    "chunks_count": 1250,
    "documents_count": 15,
    "active_tasks": 0
  }
}
```

### 3. Test Chat Endpoint

#### Non-Streaming Chat
```bash
curl -X POST "http://localhost:7860/chat" ^
  -H "Content-Type: application/json" ^
  -d '{
    "question": "What is humanoid robotics?",
    "stream": false
  }'
```

#### Streaming Chat (Using PowerShell)
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:7860/chat" -Method POST -ContentType "application/json" -Body '{
    "question": "Explain robotic kinematics",
    "stream": true
}' -ResponseHeadersVariable headers

# Handle streaming response
$reader = [System.IO.StreamReader]::new($response.GetResponseStream())
while (($line = $reader.ReadLine()) -ne $null) {
    if ($line.StartsWith("data: ")) {
        $data = $line.Substring(6) | ConvertFrom-Json
        Write-Host $data.content -NoNewline
    }
}
```

### 4. Test with Session Context

```bash
# First question
curl -X POST "http://localhost:7860/chat" ^
  -H "Content-Type: application/json" ^
  -d '{
    "question": "What are the main types of robots?",
    "session_id": "test-session-123",
    "stream": false
  }'

# Follow-up question (will have context)
curl -X POST "http://localhost:7860/chat" ^
  -H "Content-Type: application/json" ^
  -d '{
    "question": "Can you elaborate on industrial robots?",
    "session_id": "test-session-123",
    "stream": false
  }'
```

## Hugging Face Spaces Deployment

### 1. Prepare Repository

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial RAG backend implementation"

# Create README.md for Space
echo "# Physical AI & Humanoid Robotics RAG API

RAG backend for querying the Physical AI & Humanoid Robotics book content.

## Features
- Semantic search with OpenAI embeddings
- Streaming chat responses
- Source citations
- Conversation context

## Usage
See the API documentation at /docs" > README.md
```

### 2. Create Hugging Face Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in:
   - **Space name**: `robotics-rag-api` (or your choice)
   - **Owner**: Your username
   - **Visibility**: Public or Private
   - **SDK**: Docker
   - **Hardware**: CPU basic (free tier) or T4 GPU for faster embedding generation

### 3. Configure Space Secrets

In your Space settings, add these secrets:

| Secret | Value |
|--------|-------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `QDRANT_URL` | Your Qdrant URL (cloud or self-hosted) |
| `QDRANT_API_KEY` | Your Qdrant API key (if using cloud) |

### 4. Push to Hugging Face

```bash
# Add Hugging Face remote
git remote add space https://huggingface.co/spaces/your-username/your-space-name

# Push to deploy
git push space main

# The Space will automatically build and deploy
```

### 5. Deploy Your Book Content

#### Option A: Include in Repository

```bash
# Add your book_content directory
git add book_content/
git commit -m "Add book content"
git push space main
```

Then trigger ingestion via the API or create a startup script.

#### Option B: Use External Storage

1. Upload your book files to a cloud storage (GitHub, S3, etc.)
2. Create a startup script to download and ingest:

```python
# startup_script.py (add to main.py startup)
import os
import subprocess
import requests

def download_and_ingest():
    # Download from GitHub
    repo_url = "https://github.com/your-username/your-book-repo"
    subprocess.run(f"git clone {repo_url} book_content", shell=True)

    # Trigger ingestion
    subprocess.run("python scripts/ingest.py --content-path ./book_content", shell=True)

# Add to lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup code ...

    # Download and ingest on first run
    if not os.path.exists("./book_content"):
        download_and_ingest()
```

### 6. Access Your Deployed API

Your API will be available at:
```
https://your-username-your-space-name.huggingface.space
```

### 7. Test Deployment

```bash
# Test health
curl https://your-username-your-space-name.huggingface.space/health

# Test chat
curl -X POST "https://your-username-your-space-name.huggingface.space/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this book about?", "stream": false}'
```

## Advanced Configuration

### Using a Custom Qdrant Instance

1. **Self-hosted Qdrant Server**:
   ```bash
   docker run -d --name qdrant \
     -p 6333:6333 \
     -e QDRANT__SERVICE__HTTP_PORT=6333 \
     -v $(pwd)/qdrant_storage:/qdrant/storage \
     qdrant/qdrant
   ```

2. **Update Configuration**:
   ```env
   QDRANT_URL=http://your-server:6333
   QDRANT_API_KEY=your-api-key
   ```

### Optimizing for Performance

1. **Increase Batch Sizes**:
   ```env
   BATCH_SIZE=200
   MAX_CONCURRENT_REQUESTS=20
   ```

2. **Use GPU for Embeddings** (if available):
   ```bash
   # Install with GPU support
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Enable Compression**:
   ```env
   # Add to main.py app creation
   app = FastAPI(
       title="RAG API",
       description="API for robotics book",
       version="1.0.0",
       lifespan=lifespan,
       root_path="/api"  # Optional: add prefix
   )
   ```

### Adding Authentication

```python
# Add to main.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implement your token verification logic
    valid_tokens = os.getenv("VALID_TOKENS", "").split(",")
    if credentials.credentials not in valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return credentials

# Protect endpoints
@app.post("/chat")
async def protected_chat(
    request: ChatRequest,
    token: HTTPAuthorizationCredentials = Depends(verify_token)
):
    # Your chat logic
    pass
```

## Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**
   ```bash
   # Check if Qdrant is running
   docker ps | grep qdrant

   # Check logs
   docker logs qdrant

   # Test connection
   curl http://localhost:6333/collections
   ```

2. **OpenAI API Errors**
   ```bash
   # Verify API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

   # Check quota
   # Visit: https://platform.openai.com/account/usage
   ```

3. **Memory Issues**
   - Reduce `BATCH_SIZE` in `.env`
   - Reduce `CHUNK_SIZE` for smaller chunks
   - Monitor memory usage:
     ```python
     import psutil
     print(psutil.virtual_memory())
     ```

4. **Slow Response Times**
   - Check network latency to Qdrant
   - Increase `MAX_CONCURRENT_REQUESTS`
   - Use Qdrant Cloud for better performance

5. **Citation Issues**
   - Ensure Markdown files have proper headers
   - Check chunk size - too large chunks lose granularity
   - Verify file paths are correct

### Debug Mode

Enable detailed logging:

```bash
# Windows
set LOG_LEVEL=DEBUG
uvicorn main:app --reload

# Linux/Mac
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

### Check Logs

```bash
# Docker logs (if running in Docker)
docker logs <container-name>

# Application logs
tail -f logs/app.log
```

### Reset Everything

```bash
# Stop Qdrant
docker stop qdrant
docker rm qdrant

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Remove virtual environment and cache
rm -rf venv
rm -rf .venv
rm -rf .pytest_cache
rm -rf .mypy_cache
rm -rf .ruff_cache

# Re-initialize with uv
rm -rf uv.lock
uv sync --dev
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | **Required**: OpenAI API key |
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | Chat model to use |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_API_KEY` | - | Qdrant API key (optional for local) |
| `BOOK_CONTENT_PATH` | `./book_content` | Path to book files |
| `CHUNK_SIZE` | `1000` | Target chunk token count |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `BATCH_SIZE` | `100` | Processing batch size |
| `MAX_CONTEXT_MESSAGES` | `3` | Conversation history length |
| `CONTEXT_WINDOW_SIZE` | `4000` | Max tokens for context |
| `RATE_LIMIT_REQUESTS` | `60` | Requests per minute |
| `API_PORT` | `7860` | Server port |

### Performance Tuning

| Use Case | Recommended Settings |
|----------|---------------------|
| **Development** | `BATCH_SIZE=50`, `CHUNK_SIZE=800` |
| **Production (Small)** | `BATCH_SIZE=100`, `CHUNK_SIZE=1000` |
| **Production (Large)** | `BATCH_SIZE=200`, `CHUNK_SIZE=1200` |
| **Memory Constrained** | `BATCH_SIZE=25`, `CHUNK_SIZE=600` |

## Support

- **Issues**: Check logs and troubleshooting section
- **Documentation**: See `docs/api.md` for detailed API reference
- **Examples**: Check the `examples/` directory for sample code

## Next Steps

1. **Monitor Usage**: Set up monitoring for API usage and costs
2. **Add Analytics**: Track user questions and satisfaction
3. **Implement Caching**: Add Redis for response caching
4. **Scale Up**: Move to larger instances for high traffic
5. **Add Features**: Document search, bookmarking, user accounts