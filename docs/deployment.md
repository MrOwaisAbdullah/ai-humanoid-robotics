# Deployment Guide

This guide explains how to deploy the AI Book application to production:
- **Backend**: FastAPI RAG API to Hugging Face Spaces
- **Frontend**: Docusaurus site to GitHub Pages

## Prerequisites

### Required Accounts
- GitHub account with repository access
- Hugging Face account with Spaces enabled
- OpenAI API key with sufficient credits

### Required Secrets
Set up these secrets in your GitHub repository:
- `HF_TOKEN`: Hugging Face access token
- `OPENAI_API_KEY`: OpenAI API key (for backend)

## Architecture

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

## Backend Deployment (Hugging Face Spaces)

### Option 1: Automatic Deployment via GitHub Actions

1. **Configure HF Token**:
   ```bash
   # Get your token from https://huggingface.co/settings/tokens
   # Add it as a secret in your GitHub repo: Settings > Secrets > Actions
   ```

2. **Push to main branch**:
   ```bash
   git add backend/
   git commit -m "Update backend for deployment"
   git push origin main
   ```

3. **Monitor deployment**:
   - Check the Actions tab in GitHub
   - Wait for the workflow to complete
   - Verify at `https://huggingface.co/spaces/mrowaisabdullah-ai-humanoid-robotics`

### Option 2: Manual Deployment

1. **Create Hugging Face Space**:
   - Go to https://huggingface.co/new-space
   - Choose "Docker" as SDK
   - Name it: `mrowaisabdullah-ai-humanoid-robotics`
   - Make it public

2. **Deploy locally**:
   ```bash
   # Set your HF token
   export HF_TOKEN=your_token_here

   # Run the deployment script
   chmod +x backend/scripts/deploy_hf.sh
   ./backend/scripts/deploy_hf.sh mrowaisabdullah-ai-humanoid-robotics
   ```

### Backend Configuration

The backend reads these environment variables:

```env
# Required
OPENAI_API_KEY=sk-...  # OpenAI API key
QDRANT_URL=...         # Qdrant database URL

# Optional
OPENAI_MODEL=gpt-4-turbo-preview
QDRANT_API_KEY=...     # If using Qdrant cloud
RATE_LIMIT_REQUESTS=60
ALLOWED_ORIGINS=https://mrowaisabdullah.github.io,https://huggingface.co
```

## Frontend Deployment (GitHub Pages)

### Option 1: Automatic Deployment via GitHub Actions

1. **Enable GitHub Pages**:
   - Go to repository Settings > Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` and `/ (root)`

2. **Push changes**:
   ```bash
   git add src/ docs/
   git commit -m "Update frontend for deployment"
   git push origin main
   ```

3. **Wait for deployment**:
   - Check the Actions tab
   - Site will be available at: `https://mrowaisabdullah.github.io/ai-humanoid-robotics/`

### Option 2: Manual Deployment

1. **Build the site**:
   ```bash
   npm ci
   npm run build
   ```

2. **Deploy to GitHub Pages**:
   ```bash
   npm run deploy:gh
   ```

## Post-Deployment Configuration

### 1. Update Chat Widget API URL

The frontend needs to know where the backend is deployed:

1. **Option A: Environment Variable (Recommended)**:
   ```bash
   # Set before building
   export REACT_APP_CHAT_API_URL=https://mrowaisabdullah-ai-humanoid-robotics.hf.space/chat
   npm run build
   ```

2. **Option B: Update Hardcoded URL**:
   Edit `src/theme/Root.tsx` and update the default URL.

### 2. Verify CORS Configuration

Ensure the backend allows your frontend domain:

```env
ALLOWED_ORIGINS=https://mrowaisabdullah.github.io,https://huggingface.co
```

### 3. Test the Integration

1. Visit your deployed site
2. Click the chat widget
3. Send a test message
4. Check for errors in browser console

## Monitoring and Troubleshooting

### Health Checks

- Backend: `https://mrowaisabdullah-ai-humanoid-robotics.hf.space/health`
- Frontend: `https://mrowaisabdullah.github.io/ai-humanoid-robotics/`

### Common Issues

1. **CORS Errors**:
   - Check `ALLOWED_ORIGINS` in backend
   - Verify the exact URLs match

2. **Build Failures**:
   - Check dependency versions
   - Ensure all files are present
   - Review workflow logs

3. **Chat Not Working**:
   - Verify backend is running
   - Check API endpoint URL
   - Look at browser console for errors

4. **404 Errors**:
   - Ensure GitHub Pages is enabled
   - Check `baseUrl` in `docusaurus.config.ts`

### Logs and Debugging

1. **Hugging Face Spaces**:
   - Go to your space page
   - Click "Files and versions"
   - Check "Logs" tab

2. **GitHub Actions**:
   - Go to repository Actions tab
   - Click on workflow runs
   - Review detailed logs

## Maintenance

### Updates

1. **Backend Updates**:
   - Push changes to `backend/` directory
   - GitHub Actions auto-deploys

2. **Frontend Updates**:
   - Push changes to `src/` or `docs/`
   - GitHub Actions auto-deploys

### Scaling

- **Free Tier Limits**:
  - HF Spaces: 1 CPU, 512MB RAM
  - GitHub Pages: 100GB bandwidth/month

- **When to Upgrade**:
  - High traffic
  - Large documents
  - Frequent API calls

## Security Considerations

1. **API Keys**:
   - Never commit to repository
   - Use GitHub Secrets
   - Rotate regularly

2. **Rate Limiting**:
   - Configure in backend
   - Monitor usage
   - Set reasonable limits

3. **CORS**:
   - Restrict to specific domains
   - Avoid wildcard origins
   - Review regularly

## Backup and Recovery

1. **Code**: Stored in GitHub
2. **Data**:
   - Qdrant: Configure backups
   - Logs: Export regularly
3. **Recovery**:
   - Redeploy from repo
   - Restore from backups

## Performance Optimization

1. **Backend**:
   - Monitor response times
   - Optimize embeddings cache
   - Use batch processing

2. **Frontend**:
   - Enable static optimization
   - Use CDN for assets
   - Minimize bundle size

## Support

For issues:
1. Check GitHub Issues
2. Review documentation
3. Contact maintainers
4. Create bug reports with details