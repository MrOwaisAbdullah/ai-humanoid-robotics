# Quickstart Guide: Content Personalization Implementation

## Overview
This guide walks through implementing the content personalization feature that adapts technical content based on user background and expertise.

## Prerequisites

### Environment Variables
```bash
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Personalization Settings
PERSONALIZATION_RATE_LIMIT=30
PERSONALIZATION_MAX_LENGTH=2000
PERSONALIZATION_CACHE_TTL=86400

# Database (already configured)
DATABASE_URL=postgresql://user:password@localhost:5432/aibook
```

### Dependencies
```bash
# Backend
pip install "openai-agents[litellm]" python-jose[cryptography] passlib[bcrypt]
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install tenacity python-dotenv

# Frontend (already in package.json)
npm install axios react-query
```

## Implementation Steps

### Phase 1: Backend Setup

#### 1. Create Personalization Agent
File: `backend/src/agents/personalization_agent.py`

```python
import os
import json
from typing import Dict, Any
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig

class PersonalizationEngine:
    def __init__(self):
        # Configure Gemini client
        self.client = AsyncOpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        self.model = OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",
            openai_client=self.client
        )

        self.config = RunConfig(
            model=self.model,
            model_provider=self.client,
            tracing_disabled=True
        )

        # Initialize agents
        self.personalizer = Agent(
            name="ContentPersonalizer",
            instructions=self._get_personalization_instructions(),
            model=self.model
        )

    def _get_personalization_instructions(self) -> str:
        return """
        You are a Content Personalization AI that adapts technical content based on user expertise.

        For Software Experts:
        - Use code examples and API references
        - Include implementation patterns
        - Focus on practical application

        For Hardware Experts:
        - Include physical constraints and considerations
        - Reference material properties
        - Focus on system-level implications

        Guidelines:
        - Maintain technical accuracy
        - Add context-specific analogies
        - Preserve content length (~2000 words)
        - Use clear section headers
        """

    async def personalize_content(self, content: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize content based on user background"""

        personalized_input = f"""
        Please personalize the following content for a user with this background:

        User Profile:
        {json.dumps(user_profile, indent=2)}

        Content to Personalize:
        {content}

        Please adapt the content while maintaining all technical details and accuracy.
        """

        result = await Runner.run(
            agent=self.personalizer,
            input=personalized_input,
            run_config=self.config,
            max_turns=3
        )

        return {
            "personalized_content": result.final_output,
            "tokens_used": getattr(result, 'usage', {}).get('total_tokens', 0)
        }
```

#### 2. Create API Endpoints
File: `backend/src/api/routes/personalization.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Any
import hashlib
import time

from ...database import get_db
from ...security import get_current_user
from ...models.auth import User
from ...models.personalization import SavedPersonalization
from .schemas import PersonalizeRequest, PersonalizeResponse
from ..agents.personalization_agent import PersonalizationEngine

router = APIRouter(prefix="/personalize", tags=["personalization"])
security = HTTPBearer()
personalization_engine = PersonalizationEngine()

@router.post("/", response_model=PersonalizeResponse)
async def personalize_content(
    request: PersonalizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate personalized content for the authenticated user"""

    try:
        # Calculate content hash for deduplication
        content_hash = hashlib.sha256(request.content.encode()).hexdigest()

        # Get user background
        user_background = current_user.background
        if not user_background:
            # Default profile
            user_profile = {
                "experience_level": "intermediate",
                "primary_expertise": "software",
                "hardware_expertise": "none"
            }
        else:
            user_profile = {
                "experience_level": user_background.experience_level.value,
                "primary_expertise": user_background.primary_interest or "software",
                "hardware_expertise": user_background.hardware_expertise.value,
                "preferred_languages": user_background.preferred_languages or []
            }

        # Start timer
        start_time = time.time()

        # Generate personalized content
        result = await personalization_engine.personalize_content(
            content=request.content,
            user_profile=user_profile
        )

        processing_time = time.time() - start_time

        # Save if requested
        saved_id = None
        if request.save_result:
            saved = SavedPersonalization(
                user_id=current_user.id,
                original_content_hash=content_hash,
                content_url="",  # Can be populated from context
                content_title="Personalized Content",
                personalized_content=result["personalized_content"],
                personalization_metadata={
                    "target_length": request.target_length,
                    "user_profile": user_profile
                },
                adaptations_applied=["personalized"]  # Can be enhanced
            )
            db.add(saved)
            db.commit()
            saved_id = saved.id

        # Update user stats
        current_user.total_personalizations += 1
        db.commit()

        return PersonalizeResponse(
            success=True,
            data={
                "personalized_content": result["personalized_content"],
                "adaptations_made": ["personalized"],  # To be enhanced
                "complexity_score": "intermediate",  # To be calculated
                "original_length": len(request.content.split()),
                "personalized_length": len(result["personalized_content"].split()),
                "processing_time": processing_time,
                "tokens_used": result["tokens_used"],
                "saved_id": saved_id
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

#### 3. Add Route to Main App
File: `backend/src/api/routes/__init__.py`

```python
from .personalization import router as personalization_router

api_router.include_router(personalization_router)
```

### Phase 2: Frontend Implementation

#### 1. Create Personalization Modal
File: `src/components/Personalization/PersonalizationModal.tsx`

```typescript
import React from 'react';
import { motion } from 'framer-motion';
import { X, Save, Copy, Star } from 'lucide-react';

interface PersonalizationModalProps {
  isOpen: boolean;
  result: PersonalizationResult | null;
  onClose: () => void;
  onSave?: () => void;
  onRate?: (rating: number) => void;
}

export const PersonalizationModal: React.FC<PersonalizationModalProps> = ({
  isOpen,
  result,
  onClose,
  onSave,
  onRate
}) => {
  if (!isOpen || !result) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.personalized_content);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-white/10 backdrop-blur-md rounded-2xl p-6 max-w-4xl w-full max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Personalized Content</h2>
            <p className="text-white/70 mt-1">
              Adapted to your expertise level • {result.personalized_length} words
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="bg-white/5 rounded-xl p-4 mb-4 overflow-y-auto max-h-[50vh]">
          <div className="prose prose-invert max-w-none">
            {result.personalized_content.split('\n').map((paragraph, i) => (
              <p key={i} className="text-white/90 leading-relaxed mb-4">
                {paragraph}
              </p>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors flex items-center gap-2"
            >
              <Copy className="w-4 h-4" />
              Copy
            </button>
            {onSave && (
              <button
                onClick={onSave}
                className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 rounded-lg text-blue-400 transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save
              </button>
            )}
          </div>

          {onRate && (
            <div className="flex items-center gap-2">
              <span className="text-white/70 text-sm">Rate this:</span>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => onRate(star)}
                    className="text-yellow-400 hover:text-yellow-300 transition-colors"
                  >
                    <Star className="w-5 h-5" fill="currentColor" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="mt-4 pt-4 border-t border-white/10">
          <div className="flex justify-between text-sm text-white/60">
            <span>Processing time: {result.processing_time.toFixed(2)}s</span>
            <span>Tokens used: {result.tokens_used}</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
```

#### 2. Update AIFeaturesBar
File: `src/theme/DocItem/AIFeaturesBar.tsx`

```typescript
import React, { useState } from 'react';
import { Brain, Sparkles } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import { PersonalizationModal } from '../../Personalization/PersonalizationModal';
import { personalizeContent } from '../../../services/api';

export const AIFeaturesBar: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [isPersonalizing, setIsPersonalizing] = useState(false);
  const [personalizationResult, setPersonalizationResult] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const handlePersonalize = async () => {
    if (!isAuthenticated) {
      // Trigger login modal
      return;
    }

    setIsPersonalizing(true);

    try {
      // Extract current page content
      const content = extractPageContent();

      const result = await personalizeContent({
        content,
        context: window.location.pathname,
        save_result: false
      });

      setPersonalizationResult(result.data);
      setShowModal(true);
    } catch (error) {
      console.error('Personalization failed:', error);
    } finally {
      setIsPersonalizing(false);
    }
  };

  return (
    <>
      <div className="fixed bottom-8 right-8 flex gap-2">
        <button
          onClick={handlePersonalize}
          disabled={isPersonalizing}
          className="glass-effect p-4 rounded-full shadow-lg hover:scale-105 transition-transform"
        >
          {isPersonalizing ? (
            <Brain className="w-6 h-6 animate-pulse text-blue-400" />
          ) : (
            <Sparkles className="w-6 h-6 text-white" />
          )}
        </button>
      </div>

      <PersonalizationModal
        isOpen={showModal}
        result={personalizationResult}
        onClose={() => setShowModal(false)}
      />
    </>
  );
};
```

### Phase 3: Database Setup

#### 1. Create Migration
File: `backend/alembic/versions/001_add_personalization.py`

```python
"""Add personalization tables

Revision ID: 001
Revises:
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None

def upgrade():
    # Create saved_personalizations table
    op.create_table(
        'saved_personalizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('original_content_hash', sa.String(64), nullable=False),
        sa.Column('content_url', sa.String(512), nullable=False),
        sa.Column('content_title', sa.String(200), nullable=False),
        sa.Column('personalized_content', sa.Text(), nullable=False),
        sa.Column('personalization_metadata', sa.JSON(), nullable=False),
        sa.Column('adaptations_applied', sa.JSON(), nullable=False),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_accessed', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'original_content_hash')
    )

    # Create indexes
    op.create_index('idx_saved_personalizations_user_hash', 'saved_personalizations',
                    ['user_id', 'original_content_hash'], unique=True)

def downgrade():
    op.drop_table('saved_personalizations')
```

## Testing the Implementation

### 1. Unit Tests
```bash
# Test personalization agent
pytest tests/test_personalization_agent.py

# Test API endpoints
pytest tests/test_personalization_api.py
```

### 2. Integration Test
```typescript
// Frontend test
describe('Content Personalization', () => {
  it('should personalize content for authenticated user', async () => {
    // Mock authenticated user
    render(<AIFeaturesBar />);

    // Extract content
    const content = extractTestContent();

    // Click personalize button
    fireEvent.click(screen.getByRole('button'));

    // Wait for modal
    await waitFor(() => {
      expect(screen.getByText('Personalized Content')).toBeInTheDocument();
    });
  });
});
```

### 3. Manual Testing Steps
1. Login as a user with background profile
2. Navigate to any technical content page
3. Click the Personalize button (sparkle icon)
4. Verify personalized content appears
5. Test saving functionality
6. Test rating functionality
7. Verify saved items appear in user profile

## Performance Optimization

### 1. Caching Strategy
```python
# Redis cache for personalized content
@lru_cache(maxsize=1000)
def get_cached_personalization(content_hash: str, profile_hash: str):
    # Check cache first
    cache_key = f"personalization:{content_hash}:{profile_hash}"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    return None
```

### 2. Rate Limiting
```python
# Implement per-user rate limiting
rate_limiter = RateLimiter(requests_per_minute=10)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    user = await get_current_user(request)
    if user:
        await rate_limiter.acquire(user.id)
    return await call_next(request)
```

## Monitoring and Analytics

### 1. Track Metrics
- Personalization success rate
- Average processing time
- User satisfaction scores
- Tokens consumed per request

### 2. Error Tracking
```python
# Sentry integration
import sentry_sdk

@sentry_sdk.trace
async def personalize_with_tracking(content: str, user_profile: dict):
    # Implementation with automatic error tracking
    pass
```

## Next Steps

1. **Implement feedback system** - Collect user ratings to improve personalization
2. **Add more personalization strategies** - Implement different adaptation approaches
3. **A/B testing** - Test different prompting strategies
4. **Performance optimization** - Implement streaming for long content
5. **Advanced features** - Add support for multi-language personalization