# Quick Start Guide: Urdu Translation and Personalization

This guide helps developers get the Urdu translation and personalization feature running locally.

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Git
- Google Gemini API key

## 1. Backend Setup

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Environment Variables

Create `.env` file in backend directory:

```env
# Database
DATABASE_URL=sqlite:///./translations.db

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Cache Configuration
CACHE_TYPE=sqlite  # or redis for production
REDIS_URL=redis://localhost:6379  # if using redis

# App Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Feature Flags
ENABLE_TRANSLATION=true
ENABLE_PERSONALIZATION=true
```

### Database Initialization

```bash
# Create tables
alembic upgrade head

# Or run initialization script
python -m src.database.init_db
```

### Start Backend Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 2. Frontend Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Environment Variables

Create `.env.local` file in frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
NEXT_PUBLIC_ENABLE_TRANSLATION=true
NEXT_PUBLIC_ENABLE_PERSONALIZATION=true
```

### Start Development Server

```bash
npm run dev
```

## 3. Testing the Feature

### Basic Translation Test

1. Navigate to any content page
2. Click the "Translate to Urdu" button in the AI features bar
3. Verify the full-screen focus mode opens with Urdu translation
4. Test the EN/اردu toggle switch
5. Test the close button

### Personalization Test (Requires Auth)

1. Log in to your account
2. Click the "Personalize" button
3. Adjust preferences:
   - Reading level: Beginner/Intermediate/Advanced
   - Learning style: Visual/Practical/Theoretical/Balanced
   - Focus areas: Add topics of interest
4. Click "Apply" and verify content adapts

### Feedback Test

1. In focus mode, scroll to bottom
2. Click thumbs up or thumbs down
3. Optionally add a comment
4. Verify feedback is submitted

## 4. Development Workflow

### Adding New Translation Languages

1. Update `src/constants/languages.ts`:
```typescript
export const SUPPORTED_LANGUAGES = {
  en: 'English',
  ur: 'Urdu',
  // Add new language here
};
```

2. Update backend translation service to support new language

### Modifying Translation Prompts

Edit `backend/src/services/translation_service.py`:

```python
def get_translation_prompt(source_lang: str, target_lang: str) -> str:
    prompts = {
        ('en', 'ur'): """
        Translate the following English text to Urdu.
        - Keep technical terms in their original form or transliterate
        - Preserve code blocks unchanged
        - Maintain proper Urdu grammar and sentence structure
        """,
        # Add other language pairs
    }
    return prompts.get((source_lang, target_lang), default_prompt)
```

### Testing API Endpoints Directly

```bash
# Translation
curl -X POST http://localhost:8000/v1/translation \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "source_language": "en",
    "target_language": "ur"
  }'

# Get Personalization Profile (requires auth token)
curl -X GET http://localhost:8000/v1/personalization/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 5. Common Issues

### Translation Not Working
- Check Gemini API key is valid
- Verify API quota not exceeded
- Check backend logs for errors

### Focus Mode Not Opening
- Verify FocusModeContext is properly wrapped
- Check browser console for JavaScript errors
- Ensure AIFeaturesBar component is rendered

### Personalization Not Saving
- Verify user is authenticated
- Check database connection
- Review personalization API responses

### Cache Issues
- Clear browser localStorage
- Restart backend server
- Check cache configuration in `.env`

## 6. Performance Optimization

### Enabling Redis Cache

Update `.env`:
```env
CACHE_TYPE=redis
REDIS_URL=redis://localhost:6379
```

Install Redis:
```bash
# macOS
brew install redis

# Ubuntu
sudo apt-get install redis-server
```

### Monitoring Translation Performance

Enable debug logging:
```env
LOG_LEVEL=debug
```

Check backend logs for:
- Translation processing time
- Cache hit rates
- API response times

## 7. Deployment Considerations

### Environment-Specific Variables

```env
# Production
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://prod-host:6379

# Staging
NODE_ENV=staging
DATABASE_URL=postgresql://user:pass@staging-host/db
```

### Health Check Endpoints

- Backend: `GET /health`
- API readiness: `GET /v1/health`

### Monitoring Metrics

Key metrics to monitor:
- Translation latency (p95 < 3s)
- Cache hit rate (> 70%)
- Error rate (< 2%)
- Active users

## 8. Contributing Guidelines

### Code Style

- Python: Follow PEP 8, use black formatter
- TypeScript: Use Prettier, ESLint configuration
- Commits: Follow conventional commit format

### Testing Requirements

- Unit tests: 80% coverage minimum
- Integration tests: All API endpoints
- E2E tests: Critical user journeys

### Pull Request Checklist

- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Performance impact assessed
- [ ] Security review completed

## 9. Resources

### Documentation
- [API Reference](contracts/api.yaml)
- [Data Model](data-model.md)
- [Research Decisions](research.md)

### External Services
- [Google Gemini API](https://ai.google.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Support
- Create an issue for bugs
- Use discussions for questions
- Check existing issues before creating new ones