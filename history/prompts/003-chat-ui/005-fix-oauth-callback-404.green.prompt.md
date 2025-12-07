---
id: 005
title: Fix OAuth Callback 404 Error
stage: green
date_iso: 2025-12-08
surface: agent
model: glm-4.6
feature: 003-chat-ui
branch: main
user: user
command: STILL, https://mrowaisabdullah.github.io/auth/callback?token=... 404
labels: ["authentication", "oauth", "github-pages", "bug-fix"]
links:
  spec: "specs/003-chat-ui/spec.md"
  ticket: null
  adr: null
  pr: null
files_yaml:
  - src/pages/auth/callback.tsx
tests_yaml:
  - Build test: npm run build (passed)
  - Git status: clean
prompt_text: |
  STILL, https://mrowaisabdullah.github.io/auth/callback?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZW1haWwiOiJtcm93YWlzYWJkdWxsYWhAZ21haWwuY29tIiwiZXhwIjoxNzY1NzUwMTc0fQ.JTYOe-MdXyWnIalgRJfRuMyY4Yrs59fr7GVHNKVUDhc, 404 There isn't a GitHub Pages site here.
response_text: |
  Fixed the OAuth callback 404 error by creating a dedicated route handler in the Docusaurus site.

  The OAuth authentication was working successfully on the backend (logs showed successful user info retrieval and JWT token creation), but GitHub Pages didn't have a route to handle `/auth/callback`.

  Created `src/pages/auth/callback.tsx` that renders the `OAuthCallbackHandler` component from AuthContext to process the JWT token from URL parameters and complete the authentication flow.

  The build completed successfully and changes were pushed to GitHub.
outcome: Successfully fixed the OAuth callback 404 error by creating a dedicated page route at `/auth/callback` that handles the OAuth completion flow. The page uses the existing `OAuthCallbackHandler` component from AuthContext to process the JWT token and authenticate the user.
evaluation: The fix addresses the specific 404 error by leveraging Docusaurus's static page routing. When Google OAuth redirects to `https://mrowaisabdullah.github.io/auth/callback?token=...`, GitHub Pages will now serve the callback page, which processes the token and completes authentication. The backend configuration with `FRONTEND_URL=https://mrowaisabdullah.github.io` was already correct.

---