---
id: 001
title: "Fix Translation and AI Bar Issues"
stage: green
date_iso: 2025-12-10
model: claude-sonnet-3.5
feature: 001-urdu-translation-fix
branch: 001-urdu-translation-fix
user: K TECH
command: /sp.implement
labels: ["translation", "ui-fix", "backend-error"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml:
  - src/contexts/LocalizationContext.tsx
  - src/theme/DocItem/AIFeaturesBar.tsx
  - backend/src/utils/errors.py
tests_yaml: []
prompt_text: |
  Translation is disabled, the ai bar has to be offset because on scroll its going behind the header, login is not working here is the error on backend log PS D:\GIAIC\Quarter 4\ai-book\backend> uv run uvicorn main:app --host 0.0.0.0 --port 7860 --reload
  INFO:     Will watch for changes in these directories: ['D:\\GIAIC\\Quarter 4\\ai-book\\backend']
  INFO:     Uvicorn running on http://0.0.0.0:7860 (Press CTRL+C to quit)
  INFO:     Started reloader process [22708] using WatchFiles
  Process SpawnProcess-1:
  Traceback (most recent call last):
  ...
  ImportError: cannot import name 'CacheError' from 'src.utils.errors' (D:\GIAIC\Quarter 4\ai-book\backend\src\utils\errors.py)
response_text: |
  Fixed three issues:
  1. Translation disabled - Updated LocalizationContext to default to true if localStorage doesn't have translationEnabled set
  2. AI bar positioning - Changed top offset from 20px to 80px and reduced z-index to 90 to prevent it from going behind the navbar
  3. Backend ImportError - Added missing CacheError class to errors.py with proper error handling and status code mapping
outcome: Successfully fixed all reported issues. Translation now defaults to enabled, AI bar is properly positioned below navbar, and backend can start without CacheError import error.
evaluation: All issues resolved with minimal changes. Fixes address root causes rather than symptoms.
---

# Fix Translation and AI Bar Issues

## User Request
Translation is disabled, the AI bar goes behind the header on scroll, and login is not working due to a backend ImportError for CacheError.

## Implementation Details

### 1. Fixed Translation Disabled Issue
**File**: `src/contexts/LocalizationContext.tsx`
- Changed how `translationEnabled` is loaded from localStorage
- Now defaults to `true` if the value doesn't exist in localStorage
- Previously was defaulting to `false` when localStorage item was null

### 2. Fixed AI Bar Positioning
**File**: `src/theme/DocItem/AIFeaturesBar.tsx`
- Updated `top` position from `20px` to `80px` to account for navbar height
- Changed `z-index` from `100` to `90` to ensure it stays below the navbar
- This prevents the AI bar from going behind the header when scrolling

### 3. Fixed Backend ImportError
**File**: `backend/src/utils/errors.py`
- Added missing `CacheError` class that extends `BaseError`
- Included optional `operation` and `key` parameters for better error context
- Added `CacheError` to the `ERROR_STATUS_MAP` with HTTP 500 status code

## Testing
- Build completes successfully for both English and Urdu locales
- Translation feature is now enabled by default
- AI bar positioning is fixed and no longer overlaps with navbar
- Backend can start without ImportError

## Future Considerations
- Consider extracting navbar height as a CSS variable for easier maintenance
- Add unit tests for the new CacheError class
- Document the default translation enabled behavior in user documentation