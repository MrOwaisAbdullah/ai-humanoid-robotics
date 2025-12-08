# Quickstart: Authentication and UX Improvements

## Overview
This guide helps developers implement guest session persistence, authentication improvements, and UX enhancements for the AI Book platform.

## Prerequisites

1. **Backend Environment**
   - Python 3.11+
   - FastAPI installed
   - SQLAlchemy configured
   - JWT secret key configured

2. **Frontend Environment**
   - React 18+
   - TypeScript
   - Axios for API calls
   - AuthContext already set up

## Implementation Steps

### Phase 1: Guest Session Persistence (Backend)

1. **Create AnonymousSession Model**
   ```python
   # backend/models/anonymous_session.py
   from sqlalchemy import Column, String, Integer, DateTime
   from datetime import datetime, timedelta
   import uuid

   class AnonymousSession(Base):
       __tablename__ = "anonymous_sessions"
       id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
       message_count = Column(Integer, default=0)
       created_at = Column(DateTime, default=datetime.utcnow)
       expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
   ```

2. **Add Session Endpoint**
   ```python
   # backend/routes/auth.py
   @router.get("/anonymous-session/{session_id}")
   async def get_anonymous_session(session_id: str, db: Session = Depends(get_db)):
       session = db.query(AnonymousSession).filter(
           AnonymousSession.id == session_id,
           AnonymousSession.expires_at > datetime.utcnow()
       ).first()

       if not session:
           return {"id": str(uuid.uuid4()), "message_count": 0, "exists": False}

       return {"id": session.id, "message_count": session.message_count, "exists": True}
   ```

### Phase 2: Guest Session Persistence (Frontend)

1. **Create Session Storage Helper**
   ```typescript
   // src/utils/sessionStorage.ts
   class SessionStorage {
     private readonly STORAGE_KEY = 'anonymous_session_id';

     setSessionId(id: string): boolean {
       try {
         localStorage.setItem(this.STORAGE_KEY, id);
         return true;
       } catch {
         return false;
       }
     }

     getSessionId(): string | null {
       try {
         return localStorage.getItem(this.STORAGE_KEY);
       } catch {
         return null;
       }
     }

     clearSessionId(): void {
       try {
         localStorage.removeItem(this.STORAGE_KEY);
       } catch {
         // Ignore errors
       }
     }
   }

   export const sessionStorage = new SessionStorage();
   ```

2. **Update ChatWidgetContainer**
   ```typescript
   // src/components/ChatWidget/ChatWidgetContainer.tsx
   import { useEffect, useState } from 'react';
   import { sessionStorage } from '@/utils/sessionStorage';

   export function ChatWidgetContainer() {
     const [messageCount, setMessageCount] = useState(0);
     const [sessionId, setSessionId] = useState<string | null>(null);

     useEffect(() => {
       const loadSession = async () => {
         let id = sessionStorage.getSessionId();

         if (!id) {
           id = `anon_${Math.random().toString(36).substring(7)}${Date.now().toString(36)}`;
           sessionStorage.setSessionId(id);
         }

         setSessionId(id);

         // Fetch current count from backend
         try {
           const response = await fetch(`/auth/anonymous-session/${id}`);
           const data = await response.json();
           setMessageCount(data.message_count);
         } catch (error) {
           console.error('Failed to load session:', error);
           setMessageCount(0);
         }
       };

       loadSession();
     }, []);

     // Rest of component...
   }
   ```

### Phase 3: Authentication Persistence

1. **Update AuthContext**
   ```typescript
   // src/contexts/AuthContext.tsx
   export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
     const [user, setUser] = useState<User | null>(null);
     const [isLoading, setIsLoading] = useState(true);

     useEffect(() => {
       const checkAuth = async () => {
         const token = localStorage.getItem('auth_token');

         if (!token) {
           setIsLoading(false);
           return;
         }

         try {
           const response = await fetch('/auth/me', {
             headers: { 'Authorization': `Bearer ${token}` }
           });

           if (response.ok) {
             const userData = await response.json();
             setUser(userData);
             // Start token refresh timer
             startTokenRefreshTimer();
           } else {
             localStorage.removeItem('auth_token');
           }
         } catch (error) {
           localStorage.removeItem('auth_token');
         }

         setIsLoading(false);
       };

       checkAuth();
     }, []);

     const startTokenRefreshTimer = () => {
       // Check every 5 minutes
       const timer = setInterval(async () => {
         const refreshed = await refreshToken();
         if (!refreshed) {
           logout();
           clearInterval(timer);
         }
       }, 5 * 60 * 1000);

       return () => clearInterval(timer);
     };

     // Rest of context...
   };
   ```

### Phase 4: Registration with Background

1. **Create Registration Form**
   ```typescript
   // src/components/Auth/RegistrationForm.tsx
   interface RegistrationData {
     email: string;
     password: string;
     name: string;
     softwareExperience: 'Beginner' | 'Intermediate' | 'Advanced';
     hardwareExpertise: 'None' | 'Arduino' | 'ROS-Pro';
     yearsOfExperience: number;
   }

   export function RegistrationForm() {
     const [formData, setFormData] = useState<RegistrationData>({
       email: '',
       password: '',
       name: '',
       softwareExperience: 'Beginner',
       hardwareExpertise: 'None',
       yearsOfExperience: 0
     });

     const handleSubmit = async (e: React.FormEvent) => {
       e.preventDefault();

       try {
         const response = await fetch('/auth/register', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify(formData)
         });

         if (response.ok) {
           // Handle successful registration
           window.location.href = '/dashboard';
         }
       } catch (error) {
         // Handle error
       }
     };

     return (
       <form onSubmit={handleSubmit}>
         {/* Form fields */}
       </form>
     );
   }
   ```

### Phase 5: Navigation Updates

1. **Update sidebars.ts**
   ```typescript
   // sidebars.ts
   export default tutorialSidebar = {
     tutorialSidebar: [
       {
         type: 'category',
         label: 'Module 1: Foundations',
         collapsed: false,  // Changed from true
         items: [
           { type: 'doc', id: 'intro', label: 'Introduction' },
           { type: 'doc', id: 'sensors', label: 'Sensors & Perception' },
           // ... other chapters
         ]
       },
       {
         type: 'category',
         label: 'Module 2: Nervous System',
         collapsed: true,
         items: [
           { type: 'doc', id: 'ros2', label: 'ROS2 Architecture' },
           // ... other chapters
         ]
       }
       // ... continue with all modules
     ]
   };
   ```

2. **Add Mobile CSS**
   ```css
   /* src/css/custom.css */
   @media (max-width: 996px) {
     .navbar__items--right .navbar__link[href*="github"],
     .navbar__items--right .navbar__link[href*="/docs"] {
       display: none !important;
     }

     .mobile-sidebar {
       position: fixed;
       top: 0;
       left: 0;
       width: 280px;
       height: 100vh;
       background: white;
       transform: translateX(-100%);
       transition: transform 0.3s ease;
       z-index: 1000;
       box-shadow: 2px 0 8px rgba(0,0,0,0.1);
     }

     .mobile-sidebar.open {
       transform: translateX(0);
     }
   }
   ```

### Phase 6: Message Limit Notifications

1. **Update ChatInterface**
   ```typescript
   // src/components/ChatWidget/components/ChatInterface.tsx
   const [showLimitWarning, setShowLimitWarning] = useState(false);

   useEffect(() => {
     const userMessages = messages.filter(m => m.role === 'user').length;
     setMessageCount(userMessages);

     // Show warning after 2 messages
     if (userMessages >= 2 && !isAuthenticated) {
       setShowLimitWarning(true);
     } else {
       setShowLimitWarning(false);
     }
   }, [messages, isAuthenticated]);

   const shouldDisableInput = !isAuthenticated && messageCount >= 3;

   return (
     <div>
       {showLimitWarning && (
         <div className="warning-banner">
           You have 1 message remaining. Sign in to continue chatting!
           <button onClick={() => setShowLoginModal(true)}>
             Sign In
           </button>
         </div>
       )}

       <InputArea
         disabled={shouldDisableInput}
         onSend={handleSendMessage}
       />
     </div>
   );
   ```

## Testing

### Backend Tests
```python
# tests/test_anonymous_session.py
async def test_anonymous_session_creation(client):
    response = await client.get(f"/auth/anonymous-session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message_count"] == 0
    assert data["exists"] == False

async def test_session_persistence(client, db):
    # Create session
    session = AnonymousSession(id="test-123", message_count=2)
    db.add(session)
    db.commit()

    response = await client.get("/auth/anonymous-session/test-123")
    assert response.status_code == 200
    data = response.json()
    assert data["message_count"] == 2
    assert data["exists"] == True
```

### Frontend Tests
```typescript
// src/components/__tests__/ChatInterface.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import ChatInterface from '../ChatInterface';

test('shows warning after 2 messages', () => {
  const messages = [
    { role: 'user', content: 'First message' },
    { role: 'assistant', content: 'Response 1' },
    { role: 'user', content: 'Second message' }
  ];

  render(<ChatInterface messages={messages} isAuthenticated={false} />);

  expect(screen.getByText('You have 1 message remaining')).toBeInTheDocument();
});

test('disables input after 3 messages', () => {
  const messages = [
    { role: 'user', content: 'Message 1' },
    { role: 'assistant', content: 'Response 1' },
    { role: 'user', content: 'Message 2' },
    { role: 'assistant', content: 'Response 2' },
    { role: 'user', content: 'Message 3' }
  ];

  render(<ChatInterface messages={messages} isAuthenticated={false} />);

  const input = screen.getByPlaceholderText('Type your message...');
  expect(input).toBeDisabled();
});
```

## Deployment Notes

### Environment Variables
```env
# Backend
JWT_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./database/auth.db
SESSION_DURATION_HOURS=24

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database Migration
```sql
-- Create tables
CREATE TABLE anonymous_sessions (
    id VARCHAR(36) PRIMARY KEY,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    ip_address VARCHAR(45),
    user_agent TEXT,
    fingerprint VARCHAR(64)
);

CREATE INDEX idx_expires_at ON anonymous_sessions(expires_at);
CREATE INDEX idx_fingerprint ON anonymous_sessions(fingerprint);
```

## Common Issues and Solutions

1. **localStorage not available**
   - Solution: Use fingerprint fallback
   - Fallback: Create new session

2. **CORS errors**
   - Solution: Configure CORS origins
   - Add credentials: 'include'

3. **Token refresh failures**
   - Solution: Force re-login
   - Implement retry logic with backoff

4. **Mobile navigation not showing**
   - Solution: Check Docusaurus config
   - Verify CSS media queries

## Next Steps

1. Run backend tests: `pytest tests/`
2. Run frontend tests: `npm test`
3. Verify functionality manually
4. Deploy to staging
5. Monitor performance metrics

## Support

For issues or questions:
- Check the implementation plan: `/specs/001-auth-ux-improvements/plan.md`
- Review data models: `/specs/001-auth-ux-improvements/data-model.md`
- Reference API contracts: `/specs/001-auth-ux-improvements/contracts/`