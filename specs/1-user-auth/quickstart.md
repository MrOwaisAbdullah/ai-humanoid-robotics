# Quick Start Guide: User Authentication Implementation

## Overview

This guide helps developers quickly set up and understand the authentication system for the AI Book application.

## Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- Google Cloud Platform account for OAuth credentials

## 1. Google OAuth Setup

### 1.1 Create Google OAuth Application

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API and Google OAuth2 API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client IDs
5. Select "Web application"
6. Add authorized redirect URIs:
   - Development: `http://localhost:3000/auth/google/callback`
   - Production: `https://yourdomain.com/auth/google/callback`
7. Save Client ID and Client Secret

### 1.2 Environment Variables

Create `.env` file in backend directory:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
AUTH_REDIRECT_URI=http://localhost:3000/auth/google/callback
FRONTEND_URL=http://localhost:3000

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080  # 7 days

# Database
DATABASE_URL=sqlite:///./database/auth.db
```

## 2. Backend Setup

### 2.1 Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2.2 Database Setup

```bash
# Create database directory
mkdir -p database

# Initialize database
python -c "from database.config import create_tables; create_tables()"
```

### 2.3 Test Authentication Server

```bash
cd backend
uvicorn main:app --reload --port 7860
```

Verify endpoints:
- Health: http://localhost:7860/health
- OAuth Login: http://localhost:7860/auth/login/google

## 3. Frontend Setup

### 3.1 Install Dependencies

```bash
npm install axios react-router-dom
```

### 3.2 Authentication Context Setup

Create `src/contexts/AuthContext.tsx`:

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';

interface User {
  id: number;
  email: string;
  name: string;
  image_url?: string;
  email_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  login: () => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = () => {
    window.location.href = '/auth/login/google';
  };

  const logout = async () => {
    try {
      await axios.post('/auth/logout');
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### 3.3 Protected Routes

Create `src/components/ProtectedRoute.tsx`:

```typescript
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  anonymousLimit?: number;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  anonymousLimit = 3
}) => {
  const { user } = useAuth();

  if (requireAuth && !user) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
```

## 4. Integration Steps

### 4.1 Update FastAPI Main App

Add to `backend/main.py`:

```python
from routes import auth
from database.config import create_tables

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Include auth routes
app.include_router(auth.router, tags=["authentication"])

# Add auth middleware if needed
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Add session validation logic here
    response = await call_next(request)
    return response
```

### 4.2 Update Chat Endpoint

Modify `backend/rag/chat.py`:

```python
from auth.auth import get_current_user, get_or_create_user
from models.auth import ChatSession, ChatMessage

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Handle anonymous users
    if not current_user:
        # Check anonymous limit
        # Create temporary session
        pass

    # Create/retrieve chat session
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
    else:
        session = ChatSession(
            user_id=current_user.id,
            title=request.question[:50] + "..."
        )
        db.add(session)
        db.commit()

    # Process chat with RAG
    # Save messages to database

    return StreamingResponse(...)
```

### 4.3 Update Docusaurus Theme

Modify `src/theme/Root.tsx`:

```typescript
import React from 'react';
import { AuthProvider } from '../contexts/AuthContext';
import { useAuth } from '../contexts/AuthContext';

function AuthenticatedLayout({ children }) {
  const { user, login, logout } = useAuth();

  return (
    <>
      {user ? (
        <div className="auth-controls">
          <img src={user.image_url} alt={user.name} />
          <span>{user.name}</span>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <button onClick={login} className="login-button">
          Sign in with Google
        </button>
      )}
      {children}
    </>
  );
}

export default function Root({ children }) {
  return (
    <AuthProvider>
      <AuthenticatedLayout>{children}</AuthenticatedLayout>
    </AuthProvider>
  );
}
```

## 5. Testing the Implementation

### 5.1 Test OAuth Flow

1. Start backend: `uvicorn main:app --reload`
2. Start frontend: `npm start`
3. Navigate to homepage
4. Click "Sign in with Google"
5. Complete Google OAuth flow
6. Verify user profile appears in navigation

### 5.2 Test Chat Integration

1. Sign in with Google account
2. Open chat widget
3. Send a message
4. Verify message is saved
5. Refresh page
6. Verify chat history persists

### 5.3 Test Anonymous Access

1. Open new incognito window
2. Send up to 3 messages as anonymous user
3. Verify prompt to sign in appears
4. Sign in and verify messages are migrated

## 6. Common Issues & Solutions

### Issue: OAuth redirect URI mismatch
**Solution**: Ensure redirect URI in Google Console matches `AUTH_REDIRECT_URI` exactly

### Issue: CORS errors
**Solution**: Add frontend URL to FastAPI CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: JWT token not being sent
**Solution**: Ensure cookies are configured with correct domain and secure flags

### Issue: Anonymous sessions not persisting
**Solution**: Check session storage implementation and ensure proper UUID generation

## 7. Production Checklist

- [ ] HTTPS enabled on all endpoints
- [ ] Google OAuth production credentials configured
- [ ] JWT secret key is sufficiently long and random
- [ ] Database migrations are tested
- [ ] Rate limiting is enabled
- [ ] Error logging is configured
- [ ] Session cleanup job is scheduled
- [ ] CSRF protection is implemented
- [ ] Security headers are configured

## 8. Monitoring & Debugging

### Check Authentication Status
```bash
curl http://localhost:7860/auth/me \
  -H "Cookie: access_token=<your-token>"
```

### View Database
```bash
sqlite3 backend/database/auth.db
.tables
SELECT * FROM users;
SELECT * FROM sessions;
```

### Debug OAuth Flow
1. Check Google Console for OAuth errors
2. Verify redirect URI matches
3. Check browser console for JavaScript errors
4. Monitor backend logs for authentication events

## 9. Next Steps

1. Implement user settings page
2. Add email verification flow
3. Implement password reset (if needed)
4. Add multi-factor authentication
5. Create admin dashboard for user management
6. Implement audit logging
7. Add analytics for user behavior

## 10. Resources

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Authlib Documentation](https://docs.authlib.org/en/latest/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [React Authentication Best Practices](https://reactjs.org/docs/context.html)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)