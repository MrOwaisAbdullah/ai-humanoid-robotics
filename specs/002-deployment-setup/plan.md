# Deployment Implementation Plan

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  HF Spaces API   │◀───│    OpenAI API   │
│   (Source)      │    │  (Backend)       │    │   (LLM)         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │
        ▼                        │
┌─────────────────┐              │
│  GitHub Pages   │◀─────────────┘
│  (Frontend)     │
└─────────────────┘
```

## Implementation Strategy

### Phase 1: Backend Deployment (Hugging Face Spaces)

#### 1.1 Docker Configuration

- Create Dockerfile optimized for HF Spaces
- Use Python 3.11 slim base image
- Multi-stage build to reduce image size
- Expose port 7860 (HF Spaces default)

#### 1.2 HF Spaces Setup

- Create `README.md` with YAML frontmatter
- Configure environment variables
- Add health check endpoint
- Set up proper startup script

#### 1.3 API Adjustments

- Configure CORS for frontend domain
- Add `/health` endpoint
- Ensure all paths are relative to base URL
- Implement graceful shutdown

### Phase 2: Frontend Deployment (GitHub Pages)

#### 2.1 Docusaurus Configuration

- Update `baseUrl` for GitHub Pages
- Configure `trailingSlash: false`
- Set organization and project names
- Update asset paths

#### 2.2 Chat Widget Configuration

- Make backend API URL configurable
- Add environment variable support
- Implement error handling for CORS
- Add loading states

#### 2.3 Build Optimization

- Enable static optimization
- Minimize bundle size
- Configure proper sitemap
- Add robots.txt

### Phase 3: CI/CD Integration

#### 3.1 Backend Pipeline

- Create `.github/workflows/deploy-backend.yml`
- Trigger on push to `main` branch
- Build and push to HF Spaces
- Include deployment status

#### 3.2 Frontend Pipeline

- Create `.github/workflows/deploy-frontend.yml`
- Trigger on changes to `src/` directory
- Build and deploy to GitHub Pages
- Cache dependencies for faster builds

#### 3.3 Environment Management

- Separate dev/staging/prod configurations
- Secure secret management
- Automatic rollback on failure

## Detailed Implementation Steps

### 1. Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### 2. HF Spaces README

````yaml
---
title: AI Book RAG API
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

## AI Book RAG API

A retrieval-augmented generation API for answering questions about "Physical AI and Humanoid Robotics".

### Usage
```python
import requests

response = requests.post("https://your-space.hf.space/chat", json={
    "query": "What is humanoid robotics?",
    "session_id": "demo"
})
````

````

### 3. Docusaurus Config Updates
```typescript
const config = {
  baseUrl: '/ai-humanoid-robotics/',
  trailingSlash: false,
  organizationName: 'your-username',
  projectName: 'ai-book',
  deploymentBranch: 'main',
  // ... rest of config
}
````

### 4. GitHub Actions Workflows

#### Backend Deployment

```yaml
name: Deploy to HF Spaces
on:
  push:
    branches: [main]
    paths: ["backend/**"]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to HF Spaces
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          # Deployment script
```

#### Frontend Deployment

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
    paths: ["src/**", "docs/**"]
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Build and Deploy
        run: |
          npm ci
          npm run build
          # Deploy to gh-pages
```

## Security Considerations

1. **API Keys**: Store in HF Spaces secrets, not in code
2. **CORS**: Restrict to specific frontend domains
3. **Rate Limiting**: Implement in FastAPI middleware
4. **Input Validation**: Sanitize all user inputs
5. **HTTPS**: Enforce SSL/TLS everywhere

## Monitoring and Observability

1. **Health Checks**: `/health` endpoint
2. **Metrics**: Basic request/response metrics
3. **Error Tracking**: Structured error logging
4. **Performance**: Response time monitoring
5. **Usage**: Track API calls and user sessions

## Rollback Strategy

### Backend

1. Keep previous Docker image tags
2. HF Spaces allows quick rollback
3. Monitor for errors post-deployment

### Frontend

1. GitHub Pages maintains history
2. Can quickly revert to previous commit
3. Use feature flags for gradual rollout

## Testing Strategy

1. **Local Testing**: Docker compose setup
2. **Staging**: Deploy to test HF Space first
3. **Integration**: Test frontend-backend connection
4. **Load Testing**: Verify performance under load
5. **E2E**: Full user journey testing

## Post-Deployment Checklist

1. Verify all endpoints respond correctly
2. Test chat functionality end-to-end
3. Check CORS configuration
4. Monitor error rates
5. Validate environment variables
6. Test health checks
7. Confirm static assets load
8. Verify SEO settings

## Timeline Estimate

- **Phase 1** (Backend): 4 hours
- **Phase 2** (Frontend): 3 hours
- **Phase 3** (CI/CD): 3 hours
- **Testing & Debugging**: 2 hours
- **Total**: ~12 hours

## Dependencies

1. HF Spaces account with token
2. GitHub repository with appropriate permissions
3. Domain name (optional)
4. OpenAI API key with sufficient quota
5. Test data for verification
