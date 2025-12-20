# Hugging Face Spaces Deployment Guide

## Setup Instructions

### 1. Configure Your Hugging Face Space

1. **Create a new Space** with:
   - SDK: Docker
   - Space Hardware: CPU basic (free tier)
   - Visibility: Public
   - Repository: https://github.com/MrOwaisAbdullah/ai-humanoid-robotics

2. **Set Environment Variables** in Space Settings:
   Go to your Space > Settings > Variables and secrets > Add new secret

   **Required Secrets:**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   JWT_SECRET_KEY=your_random_jwt_secret_here
   ```

   **Optional Variables:**
   ```
   DATABASE_URL=sqlite:///./database/auth.db
   QDRANT_URL=https://your-qdrant-cloud-url.qdrant.io
   QDRANT_API_KEY=your_qdrant_api_key
   ```

### 2. Vector Database Setup

Since HF Spaces doesn't support persistent local databases, you have two options:

#### Option 1: Qdrant Cloud (Recommended)
1. Create a free account at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a new cluster
3. Add QDRANT_URL and QDRANT_API_KEY to your Space secrets

#### Option 2: In-Memory (Will reset on restart)
- The app will work but documents won't persist across restarts
- You'll need to re-ingest documents each time the Space restarts

### 3. Document Ingestion

Once your Space is running:
1. Visit: `https://your-space-id.hf.space/ingest`
2. Use the API endpoint to ingest documents:
   ```bash
   curl -X POST "https://your-space-id.hf.space/ingest" \
     -H "Content-Type: application/json" \
     -d '{"content_path": "book_content"}'
   ```

### 4. Troubleshooting

#### If Space fails to start:
- Check the logs in your Space's "Logs" tab
- Ensure all required secrets are set
- The Docker build takes time on first deployment

#### If search returns no results:
- Documents may not be ingested yet
- Check if Qdrant connection is working
- Try re-ingesting documents

#### Common Issues:
- **503 Error**: Usually missing environment variables or build issues
- **Search returns empty**: Documents not ingested or Qdrant not connected
- **Translation fails**: Missing OPENAI_API_KEY
- **Chat fails**: Missing OPENROUTER_API_KEY

### 5. Testing

Once deployed:
1. Health check: `https://your-space-id.hf.space/health`
2. Chat API: `https://your-space-id.hf.space/api/chat`
3. Translation API: `https://your-space-id.hf.space/api/translate`
4. Personalization API: `https://your-space-id.hf.space/api/personalize`

### 6. Monitoring

- Monitor Space usage in your HF dashboard
- Check logs regularly
- The free tier has limitations, consider upgrading for production use