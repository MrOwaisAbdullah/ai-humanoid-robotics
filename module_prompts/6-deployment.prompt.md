/sp.specify
Deploy the full stack application: Backend to Hugging Face Spaces and Frontend to GitHub Pages.

**Context & Goals:**
Finalize the project by deploying the "Physical AI & Humanoid Robotics" book. The backend API (RAG system) will be hosted on Hugging Face Spaces using Docker, and the Docusaurus frontend will be hosted on GitHub Pages.

**Prerequisites:**
- Backend `Dockerfile` must be ready (Port 7860, User 1000).
- Frontend `docusaurus.config.ts` must be configured for GitHub Pages.

**Instructions for the Agent:**

1.  **Backend Deployment (Hugging Face Spaces)**:
    *   **Metadata File**: Create `backend/README.md` with the required YAML frontmatter for Hugging Face Spaces.
        ```yaml
        ---
        title: Physical AI RAG API
        emoji: 🤖
        colorFrom: blue
        colorTo: indigo
        sdk: docker
        pinned: false
        app_port: 7860
        ---
        ```
    *   **Sync Workflow**: Create a GitHub Action (`.github/workflows/sync-backend.yml`) to automatically push the `backend/` directory to the Hugging Face Spaces repository whenever changes are pushed to `main`.
        *   *Note*: This requires a `HF_TOKEN` secret in GitHub.
    *   **Manual Fallback**: Provide a script `backend/scripts/deploy_hf.sh` for manual deployment using `git push`.

2.  **Frontend Deployment (GitHub Pages)**:
    *   **Config Update**: specifically update `docusaurus.config.ts`:
        *   `url`: 'https://<user>.github.io' (Placeholder, ask user to confirm).
        *   `baseUrl`: '/<repo>/' (Placeholder, ask user to confirm).
        *   `organizationName`: '<user>'.
        *   `projectName`: '<repo>'.
        *   `trailingSlash`: false.
    *   **Environment Variables**: Ensure the frontend can access the backend URL. Add a `customFields` section to `docusaurus.config.ts` for `API_URL`.
    *   **Deployment Workflow**: Create `.github/workflows/deploy-frontend.yml` that builds and deploys to the `gh-pages` branch.

3.  **CORS & Security**:
    *   Verify `backend/main.py` has CORS configured to allow the specific GitHub Pages URL (and `localhost` for dev).

**Deliverables:**
- `backend/README.md` (HF Spaces config).
- `.github/workflows/sync-backend.yml`.
- `.github/workflows/deploy-frontend.yml`.
- `backend/scripts/deploy_hf.sh`.
- Updated `docusaurus.config.ts`.

**Constraint Checklist & Confidence Score:**
1. Hugging Face Spaces Metadata? Yes.
2. GitHub Actions for both? Yes.
3. CORS verification? Yes.

Confidence Score: 5/5
