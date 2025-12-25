---
title: AI Book Backend
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
sdk_version: "3.11"
app_file: main.py
pinned: false
license: mit
---

# AI Book Backend

FastAPI backend for the AI Humanoid Robotics book application.

## Features

- **Authentication**: JWT-based auth with email/password and OAuth (Google)
- **Chat**: RAG-powered chat with document retrieval and streaming responses
- **Translation**: Multi-language translation using OpenAI and Gemini models
- **Personalization**: User preferences and background for personalized content

## API Endpoints

Once running:
- **Health Check**: `/health`
- **API Docs**: `/docs` (Swagger UI)
- **Authentication**: `/api/v1/auth/*`
- **Chat**: `/api/chat/*`
- **Translation**: `/api/translate`

## Environment Variables

Required secrets (set in Space Settings):
- `JWT_SECRET_KEY` - Required for authentication
- `DATABASE_URL` - SQLite (default) or PostgreSQL
- `ALLOWED_ORIGINS` - CORS allowed origins

See `.env.hf-template` for full configuration options.

## License

MIT
