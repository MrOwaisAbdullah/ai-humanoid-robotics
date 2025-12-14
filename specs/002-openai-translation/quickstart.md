# Quick Start Guide: OpenAI Translation System

This guide helps you quickly set up and use the OpenAI Translation System for translating book content from English to Urdu.

## Prerequisites

1. **Python 3.11+** installed
2. **Gemini API key** from Google AI Studio
3. **Git** for cloning the repository
4. **PostgreSQL** (production) or **SQLite** (development)

## Setup Steps

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/ai-book.git
cd ai-book
git checkout 002-openai-translation

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment

Create a `.env` file in the backend directory:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./translations.db
# For production: postgresql://user:password@localhost/translations

# Translation Settings
DEFAULT_SOURCE_LANGUAGE=en
DEFAULT_TARGET_LANGUAGE=ur
MAX_CHUNK_SIZE=2000
CACHE_TTL_HOURS=24

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Server Configuration
HOST=0.0.0.0
PORT=7860
DEBUG=false
```

### 3. Initialize Database

```bash
cd backend

# Run migrations
alembic upgrade head

# (Optional) Load sample data
python scripts/load_sample_data.py
```

### 4. Start Services

```bash
# Terminal 1: Start backend server
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 7860 --reload

# Terminal 2: Start frontend development server
cd frontend
npm run dev
```

### 5. Verify Installation

1. Open http://localhost:3000 in your browser
2. Navigate to any book page
3. Click the "Translate to Urdu" button
4. Verify translation appears within 3 seconds

## API Usage

### Basic Translation

```python
import requests

# Prepare translation request
payload = {
    "pageUrl": "https://example.com/book/chapter-1",
    "content": "<h1>Chapter 1</h1><p>Welcome to the book.</p>",
    "sessionId": "user-session-123"
}

# Make translation request
response = requests.post(
    "http://localhost:7860/api/v1/translation",
    json=payload,
    headers={"Authorization": "Bearer your-api-key"}
)

job_id = response.json()["jobId"]
print(f"Translation job started: {job_id}")
```

### Check Translation Status

```python
# Poll for completion
while True:
    status = requests.get(
        f"http://localhost:7860/api/v1/translation/{job_id}",
        headers={"Authorization": "Bearer your-api-key"}
    )

    data = status.json()
    if data["status"] == "COMPLETED":
        print("Translation complete!")
        print(data["result"]["translatedContent"])
        break
    elif data["status"] == "FAILED":
        print(f"Translation failed: {data['error']['message']}")
        break

    print(f"Progress: {data['progress']['percentage']}%")
    time.sleep(1)
```

### Streaming Translation

```python
import sseclient

def handle_translation_stream(job_id):
    response = requests.get(
        f"http://localhost:7860/api/v1/translation/{job_id}/stream",
        headers={"Accept": "text/event-stream"},
        stream=True
    )

    client = sseclient.SSEClient(response)
    for event in client.events():
        if event.event == "progress":
            data = json.loads(event.data)
            print(f"Progress: {data['percentage']}%")
        elif event.event == "complete":
            data = json.loads(event.data)
            print("Translation complete!")
            print(data["translatedContent"])
            break
        elif event.event == "error":
            print(f"Error: {event.data}")
            break
```

## Frontend Integration

### React Component Example

```tsx
import { useState } from 'react';
import { translateContent, getTranslationStatus } from '../services/translation';

export const TranslateButton: React.FC<{ content: string; pageUrl: string }> = ({
  content,
  pageUrl
}) => {
  const [isTranslating, setIsTranslating] = useState(false);
  const [translatedContent, setTranslatedContent] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const handleTranslate = async () => {
    setIsTranslating(true);
    setProgress(0);

    try {
      // Start translation
      const response = await translateContent({
        pageUrl,
        content,
        sessionId: 'user-session'
      });

      const jobId = response.jobId;

      // Poll for completion
      const checkStatus = async () => {
        const status = await getTranslationStatus(jobId);

        if (status.status === 'COMPLETED') {
          setTranslatedContent(status.result.translatedContent);
          setIsTranslating(false);
        } else if (status.status === 'FAILED') {
          console.error('Translation failed:', status.error);
          setIsTranslating(false);
        } else {
          setProgress(status.progress?.percentage || 0);
          setTimeout(checkStatus, 500);
        }
      };

      checkStatus();
    } catch (error) {
      console.error('Translation error:', error);
      setIsTranslating(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleTranslate}
        disabled={isTranslating}
        className="translate-button"
      >
        {isTranslating ? `Translating... ${progress}%` : 'Translate to Urdu'}
      </button>

      {translatedContent && (
        <div
          className="translated-content"
          dangerouslySetInnerHTML={{ __html: translatedContent }}
        />
      )}
    </div>
  );
};
```

## Common Patterns

### 1. Check Cache First

```python
def translate_with_cache(page_url: str, content: str):
    import hashlib

    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check cache
    cache_response = requests.post(
        "http://localhost:7860/api/v1/translation/cache",
        json={
            pageUrl: page_url,
            contentHash: content_hash
        }
    )

    if cache_response.json().get("cached"):
        return cache_response.json()["translatedContent"]

    # Translate if not cached
    # ... translation logic
```

### 2. Handle Rate Limits

```python
def translate_with_retry(payload: dict, max_retries: int = 3):
    for attempt in range(max_retries):
        response = requests.post(
            "http://localhost:7860/api/v1/translation",
            json=payload
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = response.json().get("error", {}).get("retryAfter", 60)
            time.sleep(retry_after)
            continue
        else:
            response.raise_for_status()

    raise Exception("Max retries exceeded")
```

### 3. Streaming Updates

```typescript
// Frontend streaming with EventSource
function streamTranslation(jobId: string) {
  const eventSource = new EventSource(
    `/api/v1/translation/${jobId}/stream`
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case 'progress':
        updateProgressBar(data.percentage);
        break;
      case 'complete':
        displayTranslation(data.content);
        eventSource.close();
        break;
      case 'error':
        showError(data.message);
        eventSource.close();
        break;
    }
  };
}
```

## Monitoring

### Health Check

```bash
curl http://localhost:7860/api/v1/translation/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "checks": {
    "database": "pass",
    "cache": "pass",
    "external_api": "pass"
  }
}
```

### Metrics

```bash
curl "http://localhost:7860/api/v1/translation/metrics?period=daily"
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: Invalid Gemini API key
   ```
   Solution: Verify your API key in `.env` file

2. **Rate Limited**
   ```
   Error: Too many requests
   ```
   Solution: Wait for the retry period or implement exponential backoff

3. **Translation Timeout**
   ```
   Error: Translation request timeout
   ```
   Solution: Check content size, ensure it's under 100,000 characters

4. **Cache Miss**
   ```
   Translation not cached
   ```
   Solution: Verify content hash calculation and URL consistency

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# Backend logs
tail -f backend/logs/app.log

# Database queries
tail -f backend/logs/db.log
```

## Performance Tips

1. **Enable Caching**: Always check cache before translating
2. **Batch Requests**: Use session IDs for related translations
3. **Optimize Content**: Remove unnecessary HTML before translation
4. **Monitor Metrics**: Track latency and error rates
5. **Use Streaming**: Provide real-time feedback for long translations

## Next Steps

1. Read the [API documentation](contracts/api.md)
2. Review the [data model](data-model.md)
3. Check the [research findings](research.md)
4. Explore the [task list](tasks.md) for implementation details

## Support

- Create an issue on GitHub for bugs
- Check the [FAQ](docs/faq.md) for common questions
- Review the [architecture guide](docs/architecture.md) for deep understanding