# Phase 0: Research & Technical Decisions

**Feature**: Urdu Translation Improvements and Personalization
**Date**: 2025-12-10
**Status**: Complete

## Translation Service Selection

### Decision: Google Gemini API

**Rationale**:
- Superior multilingual capabilities including Urdu
- Cost-effective compared to GPT-4
- Built-in support for technical term transliteration
- High rate limits suitable for production

**Alternatives Considered**:
- OpenAI GPT-4: More expensive, similar capabilities
- Azure Translator: Less context-aware, poor for technical content
- Custom model: High development cost, maintenance burden

## Caching Strategy

### Decision: Hybrid Server-Side + localStorage

**Implementation**:
- Primary: PostgreSQL/SQLite database for server-side cache
- Fallback: localStorage for offline capability
- Cache key: Content hash + source language + target language
- TTL: 7 days for translations, 30 days for user preferences

**Rationale**:
- Balances performance with offline capability
- Reduces API costs significantly
- Provides resilience during network issues

## Text Processing & Code Block Handling

### Decision: Pre-processing with Code Block Detection

**Approach**:
1. Parse markdown to identify code blocks (```language)
2. Extract and preserve code blocks unchanged
3. Translate only the narrative content
4. Reassemble with original code blocks

**Implementation Library**:
- Frontend: `marked` for markdown parsing
- Backend: `markdown-it-py` for Python processing

## Content Chunking Strategy

### Decision: Semantic Chunking with Overlap

**Parameters**:
- Maximum: 50,000 characters per request
- Target: 40,000 characters for safety margin
- Overlap: 500 characters between chunks
- Preserve: Sentence boundaries when possible

**Rationale**:
- Meets the clarified requirement
- Preserves context across chunk boundaries
- Optimizes for API token usage

## Personalization Architecture

### Decision: Prompt Engineering Based

**Approach**:
1. Collect user preferences (reading level, interests)
2. Modify Gemini prompts with user context
3. Cache personalized versions per user
4. Allow preference inheritance for similar content

**Personalization Dimensions**:
- Reading level (Beginner/Intermediate/Advanced)
- Topic preferences (e.g., focus on examples vs theory)
- Learning goals (quick overview vs deep understanding)

## UI/UX Considerations

### Focus Mode Implementation
- Full-screen modal with backdrop blur
- Smooth animations using Framer Motion
- Keyboard navigation (ESC to close, arrow keys to navigate)
- Progress indicator for reading position

### Translation Feedback
- Simple thumbs up/down buttons
- Optional text feedback (max 280 characters)
- Feedback stored for quality improvement
- No user identifying information with feedback

## Security & Privacy

### Data Handling
- No PII in translation requests
- Content hashed for cache keys
- Feedback anonymized
- User preferences encrypted at rest

### API Security
- Rate limiting: 10 requests/minute per user
- API key rotation support
- Request size validation
- Input sanitization

## Performance Optimizations

### Frontend
- Lazy load translation component
- Debounce translation requests (500ms)
- Preload common UI elements
- Service worker for offline caching

### Backend
- Connection pooling for database
- Async/await throughout
- Response compression
- CDN for static assets

## Testing Strategy

### Unit Tests
- Translation service mocking
- Cache logic validation
- Text processing edge cases
- Personalization prompt generation

### Integration Tests
- End-to-end translation flow
- Cache fallback behavior
- Error handling paths
- Performance benchmarks

### E2E Tests
- Full user journeys
- Cross-browser compatibility
- Mobile responsiveness
- Accessibility compliance (WCAG AA)

## Monitoring & Observability

### Metrics to Track
- Translation latency (p95 < 3s)
- Cache hit rate (target > 70%)
- Error rate (< 2%)
- User engagement with personalization

### Logging
- Structured JSON logs
- Correlation IDs for request tracing
- Error contexts with full stack traces
- Performance metrics per endpoint

## Deployment Considerations

### Environment Variables Required
```
GEMINI_API_KEY
DATABASE_URL
CACHE_REDIS_URL (if using Redis)
LOG_LEVEL
ENABLE_PERSONALIZATION=true
```

### Feature Flags
- `ENABLE_TRANSLATION`: Master toggle
- `ENABLE_PERSONALIZATION`: Personalization feature
- `FORCE_URDU_RTL`: RTL text direction testing
- `CACHE_DISABLED`: Disable caching for debugging