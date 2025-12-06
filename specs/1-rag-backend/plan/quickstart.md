# Quickstart Guide: RAG Backend API

This guide helps you quickly set up and deploy the RAG backend for the "Physical AI & Humanoid Robotics" book.

## Prerequisites

- Python 3.11+ installed
- Docker Desktop installed
- OpenAI API key
- Qdrant instance (local or cloud)
- Book content in Markdown format

## 1. Local Development Setup

### Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd <repository>
git checkout 1-rag-backend

# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant Configuration
QDRANT_URL=http://localhost:6333  # Or your cloud URL
QDRANT_API_KEY=your_qdrant_api_key  # Leave empty for local instance

# Content Path
BOOK_CONTENT_PATH=./book_content

# API Configuration
API_HOST=0.0.0.0
API_PORT=7860
LOG_LEVEL=INFO
```

### Start Qdrant (Local)
```bash
# Using Docker
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  qdrant/qdrant:latest

# Or install locally
pip install qdrant-client
qdrant
```

### Run the Backend
```bash
# Start the API server
uvicorn main:app --host 0.0.0.0 --port 7860 --reload

# The API will be available at http://localhost:7860
```

## 2. Ingest Book Content

### Prepare Content Structure
```
book_content/
├── chapter1.md
├── chapter2.md
├── chapter3/
│   ├── section1.md
│   └── section2.md
└── appendix.md
```

### Trigger Ingestion
```bash
# Using curl
curl -X POST "http://localhost:7860/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "content_path": "./book_content",
    "force_reindex": false,
    "batch_size": 100
  }'

# Check ingestion status
curl "http://localhost:7860/ingest/status?task_id=<task_id>"
```

### Python Script Alternative
```bash
# Run standalone ingestion script
python scripts/ingest.py --content-path ./book_content
```

## 3. Test the Chat API

### Basic Chat Request
```bash
curl -X POST "http://localhost:7860/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is humanoid robotics?",
    "context_window": 3000
  }'
```

### Chat with API Key (Higher Rate Limits)
```bash
curl -X POST "http://localhost:7860/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "question": "Explain the kinematics of robotic arms",
    "session_id": "optional-session-uuid"
  }'
```

### Streaming Response (JavaScript)
```javascript
const response = await fetch('http://localhost:7860/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'What are the main components of a robot?'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));

      if (data.type === 'chunk') {
        console.log(data.content);
      } else if (data.type === 'citation') {
        console.log('Source:', data.citation);
      } else if (data.type === 'done') {
        console.log('Stream completed');
      }
    }
  }
}
```

## 4. Health Check

```bash
# Check API health
curl "http://localhost:7860/health"

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 120.5,
  "qdrant_connected": true,
  "openai_connected": true,
  "documents_count": 15,
  "chunks_count": 1250
}
```

## 5. Deployment to Hugging Face Spaces

### Create Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose "Docker" template
4. Set Space name and visibility

### Deploy Code
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial RAG backend implementation"

# Add Hugging Face remote
git remote add space https://huggingface.co/spaces/your-username/your-space-name

# Push to deploy
git push space main
```

### Configure Space Secrets
1. Go to your Space settings
2. Add these secrets:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `QDRANT_URL`: Your Qdrant instance URL
   - `QDRANT_API_KEY`: Your Qdrant API key

### Verify Deployment
Your API will be available at: `https://your-username-your-space-name.hf.space`

## 6. Common Issues

### OpenAI API Errors
- **Rate Limits**: Implement exponential backoff in your client
- **Invalid API Key**: Check the OPENAI_API_KEY environment variable
- **Insufficient Quota**: Verify your OpenAI account has sufficient credits

### Qdrant Connection Issues
- **Connection Refused**: Ensure Qdrant is running and accessible
- **Authentication Error**: Verify QDRANT_API_KEY for cloud instances
- **Collection Not Found**: Run ingestion before using chat API

### Memory Issues
- **Large Documents**: Adjust chunk size in ingestion settings
- **High Concurrency**: Scale Qdrant instance or implement request queuing
- **Memory Leaks**: Monitor SSE connections and implement cleanup

## 7. Monitoring

### Check Logs
```bash
# Docker logs for HF Spaces
docker logs <space-container>

# Local development logs are printed to console
```

### Key Metrics to Monitor
- Response time per query
- Number of concurrent connections
- Token usage per request
- Error rates by endpoint

## 8. Next Steps

1. **Customize Prompting**: Modify system prompts in `generation.py`
2. **Add Rate Limiting**: Configure `slowapi` for your use case
3. **Implement Caching**: Add Redis for response caching
4. **Add Analytics**: Track user questions and satisfaction
5. **Scale Deployment**: Consider larger instances for production

## Support

- Check the [API documentation](http://localhost:7860/docs)
- Review error messages for debugging hints
- Monitor health endpoint for system status
- Check logs for detailed error information