---
title: AI Book RAG API
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# RAG Backend for Physical AI & Humanoid Robotics Book

A production-ready Retrieval-Augmented Generation (RAG) backend API for querying the "Physical AI & Humanoid Robotics" book content.

## Features

- **Document Ingestion**: Automatic processing of Markdown book content
- **Semantic Search**: OpenAI embeddings for intelligent content retrieval
- **Streaming Chat**: Server-Sent Events for real-time responses
- **Citations**: Automatic source attribution in markdown format
- **Conversation Context**: Short-term memory for follow-up questions
- **Rate Limiting**: Token bucket pattern with API key support
- **Health Monitoring**: Comprehensive system health checks
- **Task Management**: Background ingestion with progress tracking

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Qdrant instance (local or cloud)

### Installation

1. **Install uv** (if not already installed):
   ```bash
   # Unix/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and setup**:
   ```bash
   cd backend

   # Install dependencies (10-100x faster than pip)
   uv sync

   # For development dependencies
   uv sync --dev
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Qdrant** (local):
   ```bash
   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
   ```

4. **Run the API**:
   ```bash
   # Using uv (recommended)
   uv run uvicorn main:app --host 0.0.0.0 --port 7860

   # Or using the script command
   uv run rag-server

   # With auto-reload for development
   uv run uvicorn main:app --host 0.0.0.0 --port 7860 --reload
   ```

### Ingest Book Content

1. **Prepare content structure**:
   ```
   book_content/
   ├── chapter1.md
   ├── chapter2.md
   └── chapter3/
       ├── section1.md
       └── section2.md
   ```

2. **Trigger ingestion**:
   ```bash
   # Using the API
   curl -X POST "http://localhost:7860/ingest" \
     -H "Content-Type: application/json" \
     -d '{"content_path": "./book_content"}'

   # Or using the script
   python scripts/ingest.py --content-path ./book_content
   ```

### Chat with the Book

```bash
curl -X POST "http://localhost:7860/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is humanoid robotics?",
    "stream": true
  }'
```

## API Endpoints

### Health Check
- `GET /health` - System health status

### Chat
- `POST /chat` - Ask questions about the book
  - Supports streaming responses (`stream: true`)
  - Optional session ID for conversation context
  - Configurable retrieval parameters

### Ingestion
- `POST /ingest` - Trigger document ingestion
- `GET /ingest/status` - Get ingestion task status
- `GET /ingest/stats` - Get ingestion statistics
- `POST /ingest/{task_id}/cancel` - Cancel an ingestion task

### Management
- `GET /collections` - List Qdrant collections
- `DELETE /collections/{collection_name}` - Delete a collection

## Configuration

Environment variables:

```env
# OpenAI
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key

# Content
BOOK_CONTENT_PATH=./book_content
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# API
API_HOST=0.0.0.0
API_PORT=7860
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# Conversation
MAX_CONTEXT_MESSAGES=3
CONTEXT_WINDOW_SIZE=4000
```

## Architecture

### Core Components

1. **Ingestion Pipeline**:
   - Markdown discovery and parsing
   - Semantic chunking with overlap
   - OpenAI embedding generation
   - Qdrant vector storage

2. **Chat System**:
   - Query embedding generation
   - Semantic document retrieval
   - Context-aware response generation
   - Server-Sent Events streaming

3. **Management Layer**:
   - Background task management
   - Progress tracking
   - Health monitoring
   - Rate limiting

### Design Principles

- **Pure Python**: No LangChain dependency
- **Async/Await**: Full async implementation
- **Production Ready**: Error handling, logging, monitoring
- **HF Spaces Compatible**: Docker configuration for deployment

## Deployment

### Hugging Face Spaces

1. Create a new Space with Docker template
2. Add secrets in Space Settings > Variables and secrets:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_qdrant_api_key  # If using Qdrant Cloud
   ```
3. Push code to Space

**Required for Qdrant Cloud**: You must have the `QDRANT_URL` pointing to your Qdrant Cloud cluster URL. The API key is optional for public clusters but recommended for production.

### Docker

```bash
# Build
docker build -t rag-backend .

# Run
docker run -d \
  --name rag-backend \
  -p 7860:7860 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e QDRANT_URL=$QDRANT_URL \
  rag-backend
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=rag tests/
```

### Code Style

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy .
```

## Monitoring

### Health Checks

The `/health` endpoint provides:
- Service status
- Connection health
- System metrics
- Active tasks

### Logging

Structured JSON logging with:
- Request tracing
- Error details
- Performance metrics

### Metrics

Track:
- Response times
- Token usage
- Error rates
- Active conversations

## Security

- Rate limiting with slowapi
- Optional API key authentication
- Input validation
- Error message sanitization

## Performance

- Connection pooling for Qdrant
- Batch embedding generation
- Efficient token counting
- Configurable batch sizes

## Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**:
   - Check Qdrant is running
   - Verify URL and API key
   - Check network connectivity

2. **OpenAI API Errors**:
   - Verify API key is valid
   - Check quota limits
   - Implement retries

3. **Memory Issues**:
   - Reduce batch sizes
   - Limit concurrent requests
   - Monitor chunk sizes

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.