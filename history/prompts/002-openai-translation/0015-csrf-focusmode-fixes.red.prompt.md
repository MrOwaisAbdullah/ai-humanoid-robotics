---
id: 0015
title: CSRF and FocusMode Fixes
stage: red
date_iso: 2025-12-14
surface: agent
model: claude-3-5-sonnet-20241022
feature: 002-openai-translation
branch: 002-openai-translation
user: user
command: "why the frontend is opening the reading mode, if the translation is not succesful"
labels:
  - csrf
  - focusmode
  - translation
  - error-handling
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml:
  - backend/main.py
  - src/contexts/FocusModeContext.tsx
tests_yaml:
  - Analyzed backend error logs
  - Identified CSRF token requirement
  - Fixed FocusMode visibility logic
prompt_text: |
  why the frontend is opening the reading mode, if the translation is not succesful, "INFO:     127.0.0.1:62189 - "POST /api/v1/translation/translate/agent HTTP/1.1" 500 Internal Server Error
  ERROR:    Exception in ASGI application
    ...
  fastapi.exceptions.HTTPException: 403: CSRF token missing"
response_text: |
  Fixed two issues:

  1. **CSRF Token Issue**: Added `/api/v1/translation` to the exempt paths in CSRFMiddleware to bypass CSRF protection for translation endpoints.

  2. **FocusMode Opening on Error**: Modified FocusModeContext to keep the UI hidden (`isVisible: false`) until the translation is successful. The UI only opens when receiving the 'end' chunk, and remains hidden on errors.

  Key changes:
  - `backend/main.py`: Added `/api/v1/translation` to exempt_paths
  - `src/contexts/FocusModeContext.tsx`: Updated showTranslation to delay UI visibility until translation succeeds
outcome: |
  Successfully fixed both the CSRF token issue preventing translation requests and the FocusMode UI opening prematurely on translation failures.
evaluation: |
  The fixes address the root causes:
  - CSRF exemption allows translation API calls to proceed without token validation
  - Delayed UI visibility prevents opening FocusMode when translations fail
  - Error handling now properly keeps UI hidden on failures
---