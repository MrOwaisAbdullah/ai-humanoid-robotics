---
id: 006
title: Fix OAuth URLs for GitHub Pages Deployment
stage: green
date_iso: 2025-12-08
surface: agent
model: glm-4.6
feature: 003-chat-ui
branch: main
user: user
command: still same error. https://mrowaisabdullah.github.io/auth/callback?token=...
labels: ["authentication", "oauth", "github-pages", "url-fix", "deployment"]
links:
  spec: "specs/003-chat-ui/spec.md"
  ticket: null
  adr: null
  pr: null
files_yaml:
  - backend/.env (local changes)
  - backend/.env.example
tests_yaml:
  - Git commit successful
prompt_text: |
  still same error. https://mrowaisabdullah.github.io/auth/callback?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJtLm93YWlzbWFya3NtYW5AZ21haWwuY29tIiwiZXhwIjoxNzY1NzUwODYzfQ.34mOUzlLtTIU-NZNANu5baTD-hC-iR-xqAcHnN1cTGc, 404
response_text: |
  Fixed the OAuth URL mismatch issue. The problem was that the OAuth callback was redirecting to the wrong URL:

  - FRONTEND_URL was set to `https://mrowaisabdullah.github.io` but should be `https://mrowaisabdullah.github.io/ai-humanoid-robotics` (including the base path from Docusaurus config)
  - AUTH_REDIRECT_URI needed `/backend` prefix for the HuggingFace deployment

  Updated backend/.env with correct URLs and added production examples in .env.example.
outcome: Fixed OAuth callback URL mismatch by updating FRONTEND_URL to include the Docusaurus base path `/ai-humanoid-robotics`. The OAuth flow will now redirect to the correct GitHub Pages URL where the auth callback page exists.
evaluation: The issue was a path mismatch between the OAuth redirect URL and the actual GitHub Pages deployment structure. Docusaurus uses a base path (`/ai-humanoid-robotics/`) which must be included in all frontend URLs. The backend configuration has been updated to use the correct production URLs.

  Note: The Google OAuth client in Google Cloud Console must also be updated with the new AUTH_REDIRECT_URI: `https://mrowaisabdullah-ai-humanoid-robotics.hf.space/backend/auth/google/callback`

---