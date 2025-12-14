# OpenAI Agents SDK Implementation Fix for Gemini API Quota Errors

## Problem Summary

The translation system was experiencing Gemini API quota exceeded errors (HTTP 429) due to several issues with the OpenAI Agents SDK implementation:

1. **Incorrect Package Name**: The code was importing from `agents` package instead of the correct `openai-agents-sdk`
2. **Not Actually Using OpenAI Agents SDK**: Despite claiming to use the SDK, the implementation was using the OpenAI client directly
3. **Insufficient Rate Limit Handling**: Basic error handling that didn't properly implement exponential backoff
4. **Missing Per-User Rate Limiting**: No per-user or per-IP rate limiting to prevent quota exhaustion

## Solution Implementation

### 1. Fixed Package Dependencies

Updated `pyproject.toml`:

```toml
# Before
"openai-agents>=0.1.0"

# After
"openai-agents-sdk>=0.2.9"
```

### 2. Created Proper OpenAI Agents SDK Implementation

**File**: `src/services/openai_translation/openai_agent.py`

- Correct imports from `openai_agents_sdk`
- Proper agent implementation with tools
- Enhanced error handling for rate limits
- Exponential backoff with jitter
- Detailed error reporting

Key features:

```python
from openai_agents_sdk import Agent, Runner, function_tool, RunContextWrapper
from openai_agents_sdk.errors import RateLimitError as OpenAIRateLimitError
```

### 3. Enhanced Error Handling

**File**: `src/services/openai_translation/enhanced_service.py`

- Per-user rate limiting
- Exponential backoff implementation
- Detailed rate limit error responses
- Retry attempt tracking
- Backoff time accumulation

Example retry logic:

```python
for attempt in range(request.max_retries + 1):
    try:
        # API call
        result = await api_call()
        return result
    except RateLimitError as e:
        if attempt < request.max_retries:
            delay = min(
                request.retry_delay * (request.backoff_factor ** attempt),
                request.max_retry_delay
            )
            # Add jitter
            delay *= (0.5 + random.random() * 0.5)
            await asyncio.sleep(delay)
            continue
        else:
            raise
```

### 4. Enhanced API Endpoints

**File**: `src/api/v1/enhanced_translation.py`

- Proper HTTP 429 status codes
- Retry-After headers
- Detailed rate limit information
- Per-endpoint rate limiting

Example response:

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "User rate limit exceeded. Please wait 45.2 seconds.",
  "retry_after": 45.2,
  "rate_limit_info": {
    "retry_after": 45.2,
    "limit_type": "quota_exceeded",
    "user_id": "user123"
  },
  "timestamp": 1703847123.45
}
```

### 5. Rate Limiting Middleware

**File**: `src/middleware/rate_limit.py`

- Per-IP rate limiting
- Per-user rate limiting (if authenticated)
- Sliding window algorithm
- Redis support for distributed systems
- In-memory fallback

## How to Use the Enhanced System

### 1. Update Your Environment

```bash
cd backend
pip install -e .
```

### 2. Update Your `.env` File

Make sure you have:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL=gemini-2.0-flash-lite
```

### 3. Add Rate Limiting to Your App

In your FastAPI app initialization:

```python
from src.middleware.rate_limit import TranslationRateLimitMiddleware

app.add_middleware(TranslationRateLimitMiddleware)
```

### 4. Use Enhanced Endpoints

Instead of `/translation/translate`, use the enhanced endpoint:

```http
POST /translation/translate
```

This provides better error handling and rate limit information.

## Rate Limit Configuration

Default limits:

- **Per IP**: 60 requests per minute, 1000 per hour
- **Per User (if authenticated)**: 10 translations per minute, 500 per hour
- **Translation Endpoints**: Stricter limits (10/min, 500/hour)

These can be configured via environment variables or in the middleware initialization.

## Monitoring and Metrics

The enhanced system provides detailed metrics:

```json
{
  "period": "24h",
  "total_requests": 1250,
  "successful_requests": 1180,
  "failed_requests": 45,
  "rate_limited_requests": 25,
  "cache_hit_rate": 0.35,
  "avg_processing_time_ms": 2340,
  "total_cost_usd": 2.45,
  "active_users": 15,
  "user_rate_limits": {
    "user123": {
      "requests_last_minute": 3,
      "last_reset": 1703847123.45
    }
  }
}
```

## Best Practices

1. **Handle Rate Limit Errors Properly**

   ```python
   try:
       result = await translate_text(text)
   except RateLimitError as e:
       print(f"Rate limited. Retry after {e.retry_after} seconds")
       await asyncio.sleep(e.retry_after)
       # Retry with backoff
   ```

2. **Use Caching When Possible**

   - The system automatically caches successful translations
   - Cache hits don't count against rate limits
   - Provide `page_url` for better cache keys

3. **Batch Large Translations**

   - The system automatically chunks large texts
   - Configure `chunk_size` and `max_chunks` appropriately
   - Monitor processing time to optimize chunk size

4. **Monitor Your Usage**
   - Use `/translation/metrics` endpoint (admin only)
   - Watch for rate limit errors in logs
   - Adjust retry settings based on your quota

## Testing the Fix

To test the rate limiting:

```python
import asyncio
import httpx

async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        # Make rapid requests to trigger rate limit
        for i in range(15):
            response = await client.post(
                "http://localhost:8000/translation/translate",
                json={
                    "text": f"Test translation {i}",
                    "source_language": "en",
                    "target_language": "ur"
                }
            )
            print(f"Request {i}: Status {response.status_code}")
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                print(f"Rate limited. Retry after {retry_after} seconds")
                break

asyncio.run(test_rate_limit())
```

## Troubleshooting

### Still Getting 429 Errors?

1. **Check Your Gemini API Quota**

   - Visit Google AI Studio
   - Verify your daily/monthly quota
   - Request quota increase if needed

2. **Implement Client-Side Rate Limiting**

   ```python
   import asyncio
   from asyncio import Semaphore

   # Limit concurrent requests
   semaphore = Semaphore(5)  # Max 5 concurrent requests

   async def translate_with_limit(text):
       async with semaphore:
           return await translate_text(text)
   ```

3. **Use Backoff in Your Client**

   ```python
   import backoff

   @backoff.on_exception(backoff.expo, RateLimitError, max_tries=3)
   async def safe_translate(text):
       return await translate_text(text)
   ```

### Performance Issues?

1. **Reduce Chunk Size**

   - Smaller chunks process faster
   - Less chance of timeout
   - Better error recovery

2. **Enable Caching**

   - Set `page_url` for content-based caching
   - Cache hits are instant
   - Reduces API usage

3. **Monitor Memory Usage**
   - Large translations use more memory
   - Consider streaming for very large texts
   - Implement pagination for batch jobs

## Migration Guide

To migrate from the old implementation:

1. **Update Dependencies**

   ```bash
   pip install openai-agents-sdk>=0.2.9
   ```

2. **Update Imports**

   ```python
   # Old
   from agents import Agent, Runner

   # New
   from openai_agents_sdk import Agent, Runner
   ```

3. **Update Error Handling**

   ```python
   # Old
   except Exception as e:
       if "429" in str(e):
           # Handle rate limit

   # New
   except RateLimitError as e:
       retry_after = e.retry_after
       # Handle with proper backoff
   ```

4. **Add Rate Limiting**
   ```python
   from src.middleware.rate_limit import TranslationRateLimitMiddleware
   app.add_middleware(TranslationRateLimitMiddleware)
   ```

## Conclusion

The enhanced OpenAI Agents SDK implementation provides:

- ✅ Correct package usage and imports
- ✅ Proper agent implementation with tools
- ✅ Robust rate limit error handling
- ✅ Exponential backoff with jitter
- ✅ Per-user and per-IP rate limiting
- ✅ Detailed error reporting and metrics
- ✅ Caching to reduce API usage
- ✅ Monitoring and health checks

This should significantly reduce Gemini API quota errors and provide a better user experience with proper error handling and retry logic.
