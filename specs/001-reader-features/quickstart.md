# Quick Start Guide: Reader Experience Enhancements

**Date**: 2025-01-09
**Phase**: 1 - Design & Contracts

## Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.11+ with pip
- SQLite database (existing in project)
- Git for version control

## Initial Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone <repository-url>
cd ai-book

# Switch to the feature branch
git checkout 001-reader-features

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` files for both frontend and backend:

**Frontend (.env)**:
```bash
# Search configuration
ALGOLIA_APP_ID=your_app_id
ALGOLIA_SEARCH_KEY=your_search_key

# API endpoints
REACT_APP_API_URL=http://localhost:8000/api/v1
```

**Backend (.env)**:
```bash
# Database
DATABASE_URL=sqlite:///./ai_book.db

# Authentication
JWT_SECRET=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Sync settings
PROGRESS_SYNC_INTERVAL=30000
BOOKMARK_SYNC_INTERVAL=60000
```

### 3. Database Migration

```bash
cd backend

# Run Alembic migration
alembic upgrade head

# Verify tables created
sqlite3 ai_book.db ".tables"
```

Expected tables:
- reading_progress
- bookmarks
- bookmark_tags
- user_preferences
- user_custom_notes
- content_localization
- search_index

## Frontend Setup

### 1. Configure Docusaurus i18n

Update `docusaurus.config.ts`:

```typescript
const config = {
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'ur', 'ur-roman'],
    localeConfigs: {
      ur: {
        label: 'اردو',
        direction: 'rtl',
        htmlLang: 'ur-PK',
        calendar: 'gregory'
      },
      'ur-roman': {
        label: 'Roman Urdu',
        direction: 'ltr',
        htmlLang: 'ur-PK',
        calendar: 'gregory'
      }
    }
  },
  themeConfig: {
    navbar: {
      items: [
        {
          type: 'localeDropdown',
          position: 'right'
        }
      ]
    }
  }
};
```

### 2. Add Urdu Fonts

Create `static/fonts/UrduFonts.css`:

```css
@font-face {
  font-family: 'Noto Nastaliq Urdu';
  src: url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap');
}

@font-face {
  font-family: 'Awami Nastaliq';
  src: url('https://fonts.googleapis.com/css2?family=Awami+Nastaliq&display=swap');
}
```

Update `src/css/custom.css`:

```css
[dir='rtl'] {
  font-family: 'Noto Nastaliq Urdu', 'Awami Nastaliq', serif;
  line-height: 1.8;
}

.urdu-text {
  font-family: 'Noto Nastaliq Urdu', serif;
}

.urdu-body {
  font-family: 'Awami Nastaliq', sans-serif;
  line-height: 1.9;
}
```

### 3. Install Search Package

```bash
cd frontend
npm install @pagefind/default-ui
```

## Backend Setup

### 1. Create New Models

Create `backend/src/models/reading_progress.py`:

```python
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class ReadingProgress(BaseModel):
    __tablename__ = "reading_progress"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    chapter_id = Column(String, nullable=False)
    section_id = Column(String, nullable=False)
    position = Column(Float, nullable=False)  # 0-100
    completed = Column(Boolean, default=False)
    time_spent = Column(Integer, default=0)  # Minutes
    last_accessed = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="reading_progress")
```

### 2. Add API Routes

Create `backend/src/api/v1/progress.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.reading_progress import ReadingProgress
from ..auth import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])

@router.get("/{chapter_id}")
async def get_chapter_progress(
    chapter_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.chapter_id == chapter_id
    ).all()

    return {
        "chapterProgress": calculate_chapter_progress(progress),
        "sections": progress
    }

@router.post("/{chapter_id}")
async def update_progress(
    chapter_id: str,
    progress_data: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Implementation here
    pass
```

### 3. Update Main App

In `backend/src/main.py`, add the new router:

```python
from .api.v1 import progress, bookmarks, preferences

app.include_router(progress.router, prefix="/api/v1")
app.include_router(bookmarks.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")
```

## Testing Setup

### Frontend Tests

Create test utilities in `src/test-utils/rtl.tsx`:

```typescript
import { render, RenderOptions } from '@testing-library/react';
import { DirectionProvider } from '../contexts/LocalizationContext';

const renderWithRTL = (
  ui: React.ReactElement,
  options?: RenderOptions
) => {
  return render(
    <DirectionProvider direction="rtl">
      {ui}
    </DirectionProvider>,
    options
  );
};

export { renderWithRTL };
```

### Backend Tests

Create `backend/tests/test_progress.py`:

```python
import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_get_progress_unauthorized():
    response = client.get("/api/v1/progress/chapter-1")
    assert response.status_code == 401

def test_update_progress():
    # Test with authenticated user
    pass
```

## Run the Application

### Frontend Development

```bash
cd frontend
npm start
```

Navigate to `http://localhost:3000`

### Backend Development

```bash
cd backend
uvicorn src.main:app --reload
```

API available at `http://localhost:8000`

## Verify Installation

### 1. Check Frontend

- Language switcher appears in navbar
- Can switch between English, Urdu, and Roman Urdu
- Urdu content displays right-to-left

### 2. Check Backend

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 3. Test Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'
```

## Common Issues & Solutions

### 1. Font Not Loading

**Problem**: Urdu text appears in default font
**Solution**: Ensure font CSS is imported in `src/pages/_app.tsx` or similar

### 2. RTL Layout Issues

**Problem**: Layout breaks when switching to Urdu
**Solution**: Use CSS logical properties instead of physical properties

### 3. Database Connection Error

**Problem**: Backend cannot connect to SQLite
**Solution**: Check DATABASE_URL in .env file and ensure file permissions

### 4. Search Not Working

**Problem**: PageFind returns no results
**Solution**: Ensure PageFind is initialized after page load

## Next Steps

1. Implement authentication flow
2. Create React components for each feature
3. Add comprehensive test coverage
4. Set up CI/CD pipeline
5. Configure production deployment

## Resources

- [Docusaurus i18n Guide](https://docusaurus.io/docs/i18n/introduction)
- [PageFind Documentation](https://pagefind.app/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [RTL Styling Guide](https://rtlstyling.com/)