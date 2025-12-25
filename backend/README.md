# AI Book Backend

FastAPI backend for the AI Humanoid Robotics book application. Provides REST APIs for:

- **Authentication**: JWT-based auth with email/password and OAuth (Google)
- **Chat**: RAG-powered chat with document retrieval and streaming responses
- **Translation**: Multi-language translation using OpenAI and Gemini models
- **Personalization**: User preferences and background for personalized content

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --host 0.0.0.0 --port 7860
```

## Environment Variables

See `.env.example` for required configuration:
- `JWT_SECRET_KEY`: Required for authentication
- `DATABASE_URL`: SQLite (default) or PostgreSQL
- `ALLOWED_ORIGINS`: CORS allowed origins
- `OPENAI_API_KEY`: For chat and translation features

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:7860/docs`
- ReDoc: `http://localhost:7860/redoc`

## License

MIT
