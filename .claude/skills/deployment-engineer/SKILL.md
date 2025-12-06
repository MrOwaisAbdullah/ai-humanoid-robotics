---
name: deployment-engineer
description: Expert deployment automation for cloud platforms. Handles CI/CD pipelines, container orchestration, infrastructure setup, and production deployments with battle-tested configurations. Specializes in GitHub Actions, Docker, HuggingFace Spaces, and GitHub Pages.
category: devops
version: 1.0.0
---

# Deployment Engineer Skill

## Purpose

Automate and manage production deployments across multiple platforms with zero-downtime, proper monitoring, and rollback capabilities. This skill encapsulates hard-won lessons from real-world deployment scenarios.

## When to Use This Skill

Use this skill when:
- Setting up CI/CD pipelines for web applications
- Deploying to HuggingFace Spaces, Vercel, Netlify, or GitHub Pages
- Configuring Docker containers and orchestration
- Implementing environment-specific configurations
- Troubleshooting deployment failures
- Setting up monitoring and health checks

## Core Deployment Patterns

### 1. Multi-Platform Deployment Strategy

**Lesson Learned**: Always verify platform-specific requirements before deployment.

```yaml
# .github/workflows/deploy-backend.yml
# Critical patterns discovered through painful debugging:

# 1. Branch Name Consistency
on:
  push:
    # NEVER assume 'main' - always verify actual branch name
    branches: [master]  # Fixed from 'main' after repo inspection

# 2. Authentication for External Services
- name: Deploy to HuggingFace
  env:
    HF_TOKEN: ${{ secrets.HF_TOKEN }}
  run: |
    # Pattern: Use credential helper for Git auth
    git config credential.helper store
    echo "https://hf:$HF_TOKEN@huggingface.co" > ~/.git-credentials
    git remote set-url origin https://hf:$HF_TOKEN@huggingface.co/spaces/${{ env.HF_SPACE_NAME }}

# 3. Error Handling and Verification
- name: Verify Deployment
  run: |
    # Always add post-deployment verification
    curl -f "${{ env.DEPLOY_URL }}/health" || echo "Health check failed - space might still be starting"
```

### 2. Docker Configuration Best Practices

**Lesson Learned**: Order of operations in Dockerfile is critical for build success.

```dockerfile
# backend/Dockerfile - Battle-tested pattern

# 1. Use specific Python version
FROM python:3.11-slim

# 2. Install system dependencies FIRST
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Set working directory early
WORKDIR /app

# 4. Copy requirements BEFORE source code (leverages Docker cache)
COPY pyproject.toml requirements.txt README.md ./

# 5. Install Python dependencies
RUN pip install uv
RUN uv pip install --system -e .

# 6. Copy application code
COPY . .

# 7. Create non-root user AFTER installation
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# 8. Expose port and health check
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# 9. CMD must be last
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
```

### 3. Environment Variables Management

**Lesson Learned**: Different platforms require different environment variable strategies.

```python
# backend/main.py - Environment loading pattern

from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

class Settings(BaseSettings):
    """Always provide defaults for critical settings"""

    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to stable model

    # Platform Detection
    is_hf_spaces: bool = os.getenv("SPACE_ID") is not None
    is_production: bool = os.getenv("NODE_ENV") == "production"

    @property
    def api_endpoint(self) -> str:
        """Auto-detect API endpoint based on platform"""
        if self.is_hf_spaces:
            # HuggingFace Spaces
            space_name = os.getenv("SPACE_ID", "")
            return f"https://{space_name.replace(' ', '-').lower()}.hf.space"
        elif self.is_production:
            # Production environment
            return os.getenv("API_URL", "")
        else:
            # Local development
            return "http://localhost:7860"
```

### 4. CORS Configuration for Cross-Origin Requests

**Lesson Learned**: Frontend and backend on different domains require explicit CORS setup.

```python
# backend/main.py - CORS configuration

app = FastAPI()

# Dynamic CORS origins based on environment
cors_origins = []
if os.getenv("NODE_ENV") == "production":
    cors_origins = [
        "https://yourusername.github.io",
        "https://yourdomain.com"
    ]
else:
    cors_origins = ["http://localhost:3000", "http://localhost:7860"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Frontend Configuration Pattern

**Lesson Learned**: Frontend must adapt to different deployment environments.

```typescript
// src/theme/Root.tsx - Dynamic API endpoint detection
const getChatkitEndpoint = () => {
  // Check environment variable first
  if (process.env.REACT_APP_CHAT_API_URL) {
    return process.env.REACT_APP_CHAT_API_URL;
  }

  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:7860/chat';
  }

  // Production URLs
  if (hostname.includes('github.io')) {
    // GitHub Pages
    return 'https://your-space.hf.space/chat';
  } else if (hostname.includes('hf.space')) {
    // HuggingFace Spaces
    return `https://${hostname}/chat`;
  }

  return '/chat'; // Same domain deployment
};
```

## Common Pitfalls & Solutions

### 1. Branch Name Mismatch
**Problem**: GitHub Actions configured for 'main' but repo uses 'master'
```yaml
# NEVER hard-code branch names
branches: [master]  # Verify with `git branch` first
```

### 2. Docker Build Failures
**Problem**: Permission errors during package installation
```dockerfile
# Install dependencies BEFORE switching to non-root user
RUN uv pip install --system -e .  # As root
USER user  # Switch AFTER installation
```

### 3. Model Compatibility Issues
**Problem**: Using models that require different APIs
```python
# Wrong: gpt-5-nano requires Responses API, not Chat Completions
# Correct: Use compatible models
openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
```

### 4. Query Validation Errors
**Problem**: Backend crashes on short queries like "hi"
```python
# Allow single character queries
if not query or len(query.strip()) < 1:
    raise ValueError("Query must be at least 1 character long")
```

### 5. Missing Health Checks
**Problem**: No way to verify deployment success
```python
@app.get("/health")
async def health_check():
    """Always implement health endpoints"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await check_database(),
            "openai": bool(os.getenv("OPENAI_API_KEY"))
        }
    }
```

## Deployment Checklist

### Pre-Deployment
- [ ] Verify branch names in workflows match actual branches
- [ ] Test Docker build locally: `docker build -t test .`
- [ ] Run container locally: `docker run -p 7860:7860 test`
- [ ] Check all environment variables are documented
- [ ] Validate API endpoints with health checks
- [ ] Test CORS configuration in browser dev tools

### Deployment
- [ ] Ensure secrets are configured in GitHub
- [ ] Monitor build logs for errors
- [ ] Verify deployment URL accessibility
- [ ] Test critical user flows
- [ ] Check error logs in production

### Post-Deployment
- [ ] Set up monitoring/alerting
- [ ] Document rollback procedure
- [ ] Update API documentation
- [ ] Notify stakeholders of deployment

## Platform-Specific Configurations

### HuggingFace Spaces
```yaml
# README.md frontmatter for HF Spaces
---
title: Your App Title
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---
```

### GitHub Pages
```yaml
# docusaurus.config.ts for GitHub Pages
baseUrl: '/your-repo-name/',
organizationName: 'your-username',
projectName: 'your-repo',
deploymentBranch: 'gh-pages',
```

### Environment Variables
Create `.env.example`:
```env
# Required
OPENAI_API_KEY=your_key_here
QDRANT_URL=your_qdrant_url

# Optional
OPENAI_MODEL=gpt-4o-mini
NODE_ENV=production
```

## Troubleshooting Guide

### "HF_TOKEN not provided"
1. Check GitHub repository settings > Secrets
2. Verify secret name matches exactly: `HF_TOKEN`
3. Ensure workflow has permissions to access secrets

### Docker "Permission denied"
1. Install packages before creating non-root user
2. Use `--system` flag with uv/pip
3. Set proper file ownership: `chown -R user:user /app`

### CORS Errors
1. Add frontend domain to CORS origins
2. Check browser network tab for preflight requests
3. Verify API endpoint URLs are correct

### Application won't start
1. Check health endpoint: `curl /health`
2. Verify all environment variables
3. Check application logs for startup errors

## Scripts Directory

Include deployment helper scripts:
```bash
# scripts/deploy.sh
#!/bin/bash
set -e

echo "Starting deployment..."

# Build and test locally
docker build -t app .
docker run -d -p 7860:7860 --name test-app app
sleep 5
curl -f http://localhost:7860/health || exit 1
docker stop test-app

# Push to registry
echo "Deployment test passed!"
```

## Monitoring Setup

Always include basic monitoring:
```python
# Add to main.py
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        "request_processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )

    return response
```

## Security Considerations

1. **Never commit secrets**: Use environment variables
2. **Use HTTPS in production**: Configure SSL certificates
3. **Implement rate limiting**: Prevent abuse
4. **Validate inputs**: Sanitize all user inputs
5. **Regular updates**: Keep dependencies updated

## Rolling Back Deployments

```bash
# Git rollback
git revert <commit-hash>
git push origin master

# Or if using tags
git checkout previous-tag
git push -f origin master
```

Remember: The goal is not just to deploy, but to deploy reliably and maintainably. Test thoroughly, monitor continuously, and always have a rollback plan.