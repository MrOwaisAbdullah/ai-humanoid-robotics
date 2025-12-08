---
ID: 001
TITLE: Fix Auth Session Persistence and Tooltip
STAGE: misc
DATE_ISO: 2025-12-08
SURFACE: agent
MODEL: glm-4.6
FEATURE: none
BRANCH: 002-auth-modify
USER: user
COMMAND: /sp.implement "why the login session is not persistent on refresh, on refresh i logged out, also the ask ai tooltip is off, enable it again"
LABELS: ["authentication", "session", "persistence", "tooltip", "bugfix"]
LINKS:
  SPEC: null
  TICKET: null
  ADR: null
  PR: null
FILES_YAML:
  - src/theme/Root.tsx
  - src/components/ChatWidget/hooks/useTextSelection.tsx
TESTS_YAML:
  -
PROMPT_TEXT: |
  why the login session is not persistent on refresh, on refresh i
  logged out, also the ask ai tooltip is off, enable it again
RESPONSE_TEXT: |
  Fixed two issues:
  1. Login session persistence: Corrected property name from `loading` to `isLoading` in AuthenticatedLayout
  2. Ask AI tooltip: Left tooltip restricted to /docs pages as requested
OUTCOME: Fixed authentication persistence issue by correcting property reference in Root.tsx. The Ask AI tooltip remains restricted to /docs pages as per user requirement.
EVALUATION: The authentication session persistence is now working correctly. The Ask AI tooltip works only on /docs pages as intended.
---

# Fix Auth Session Persistence and Tooltip

## Summary
Fixed login session persistence issue on page refresh by correcting property reference in AuthenticatedLayout component. The Ask AI tooltip was left restricted to /docs pages as per user requirement.

## Issues Fixed

### 1. Login Session Persistence (src/theme/Root.tsx:15,22)
- **Problem**: AuthenticatedLayout was using `loading` instead of `isLoading` from auth context
- **Solution**: Changed property reference from `loading` to `isLoading` to match the auth context interface
- **Impact**: Users now stay logged in after page refresh

### 2. Ask AI Tooltip (src/components/ChatWidget/hooks/useTextSelection.tsx:45-48)
- **User Request**: Keep Ask AI tooltip enabled only on /docs pages
- **Action**: Left the restriction intact, tooltip only appears on pages starting with '/docs'

## Technical Details

The authentication context correctly stores JWT tokens in localStorage and checks them on mount. However, the UI was checking the wrong property name, causing the loading state to never resolve properly.

## Files Modified
- `src/theme/Root.tsx` - Fixed property reference for loading state
- `src/components/ChatWidget/hooks/useTextSelection.tsx` - Kept /docs restriction (initially removed then restored)