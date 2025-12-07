# Authentication Implementation Guide

## Overview

This document provides a comprehensive guide to the authentication system implemented for the AI Book application. The system uses Google OAuth for user authentication, JWT tokens for session management, and includes anonymous user support with message limits.

## Architecture

### Backend Components

1. **Database Models** (`backend/models/auth.py`)
   - `User`: Stores user information from Google OAuth
   - `Session`: Manages active user sessions with JWT tokens
   - `ChatSession`: Links chat sessions to authenticated users
   - `ChatMessage`: Stores individual chat messages with metadata
   - `UserPreferences`: Stores user-specific settings and preferences

2. **Authentication Routes** (`backend/routes/auth.py`)
   - `GET /auth/me`: Get current user information
   - `POST /auth/login/google`: Initiate Google OAuth flow
   - `GET /auth/login/google/callback`: Handle OAuth callback
   - `POST /auth/logout`: Logout user and clear session
   - `GET /auth/preferences`: Get user preferences
   - `PUT /auth/preferences`: Update user preferences

3. **Middleware** (`backend/middleware/`)
   - `auth_middleware.py`: Validates JWT tokens and manages anonymous sessions
   - `csrf_middleware.py`: Provides CSRF protection for cookie-based authentication
   - `rate_limiter.py`: Applies rate limiting to authentication endpoints

### Frontend Components

1. **AuthContext** (`src/contexts/AuthContext.tsx`)
   - Manages authentication state globally
   - Provides login/logout functionality
   - Handles OAuth callback processing

2. **Authentication Components** (`src/components/Auth/`)
   - `LoginButton`: Google OAuth login button with branding
   - `UserProfile`: User profile dropdown with logout option
   - `AuthenticationBanner`: Encourages anonymous users to sign up
   - `AnonymousLimitBanner`: Shows when users reach message limits
   - `NavbarAuth`: Injects auth buttons into Docusaurus navbar
   - `OnboardingManager`: Handles new user onboarding flow
   - `OnboardingModal`: Collects user background information

3. **Chat Integration**
   - Modified `ChatInterface` to track anonymous user messages
   - Disables input after 3 messages for anonymous users
   - Shows authentication prompts for conversion to signed-in users

## Setup Instructions

### Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# Database Configuration
DATABASE_URL=sqlite:///./database/auth.db

# Frontend URL (for OAuth redirect)
FRONTEND_URL=http://localhost:3000
```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:7860/auth/login/google/callback`
6. Copy Client ID and Client Secret to environment variables

### Database Initialization

The SQLite database will be created automatically when the backend starts. The database file is located at `backend/database/auth.db`.

### Running the Application

1. Start the backend server:
   ```bash
   cd backend
   uv run python main.py
   ```

2. Start the frontend:
   ```bash
   npm start
   ```

## Features

### Anonymous User Support

- Anonymous users can send up to 3 messages
- After 3 messages, a limit banner appears encouraging sign-up
- Anonymous sessions are tracked using temporary IDs
- No personal data is stored for anonymous users

### Authentication Flow

1. User clicks "Sign in with Google"
2. Redirected to Google OAuth consent screen
3. Google redirects back with authorization code
4. Backend exchanges code for access token and user profile
5. JWT token is created and stored in HTTP-only cookie
6. User is redirected back to the application

### Session Management

- JWT tokens are stored in secure, HTTP-only cookies
- Tokens expire after 7 days by default
- Automatic token refresh on API calls
- Secure logout clears all authentication cookies

### Security Features

1. **CSRF Protection**: Double-submit cookie pattern for state-changing requests
2. **Rate Limiting**: 5 requests per minute per IP for auth endpoints
3. **Secure Cookies**: HTTP-only, SameSite=Strict cookies
4. **Input Validation**: All inputs validated using Pydantic models
5. **HTTPS Required**: Production environment requires HTTPS

## User Preferences

The system stores user preferences including:

- Software background (Novice/Intermediate/Expert)
- Hardware/Robotics background (None/Arduino/ROS-Pro)
- Theme preferences
- Language settings
- Notification preferences

## API Reference

### Authentication Endpoints

#### Get Current User
```http
GET /auth/me
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "image_url": "https://...",
  "email_verified": true
}
```

#### Get User Preferences
```http
GET /auth/preferences
Authorization: Bearer <token>
```

#### Update User Preferences
```http
PUT /auth/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "chat_settings": {
    "software_background": "Intermediate",
    "hardware_background": "Arduino"
  },
  "theme": "light",
  "language": "en"
}
```

## Testing

The system includes a comprehensive test suite covering:

- Unit tests for authentication logic
- Integration tests for API endpoints
- OAuth flow testing
- Security vulnerability testing

Run tests:
```bash
cd backend
pytest tests/
```

## Troubleshooting

### Common Issues

1. **"Invalid JWT token" error**
   - Check JWT_SECRET_KEY environment variable
   - Ensure token hasn't expired
   - Verify cookie domain and path settings

2. **Google OAuth failing**
   - Verify redirect URI matches exactly
   - Check Google Cloud Console configuration
   - Ensure Client ID and Secret are correct

3. **Database errors**
   - Ensure backend has write permissions to database directory
   - Check SQLite file path is correct
   - Verify all required tables exist

4. **CORS errors**
   - Check CORS configuration in main.py
   - Verify frontend URL is allowed
   - Ensure preflight requests are handled

## Migration from Anonymous to Authenticated

When an anonymous user signs in:

1. Their temporary session ID is linked to their new user account
2. Existing chat history is preserved
3. User preferences are initialized with onboarding flow
4. All future interactions are tied to their authenticated account

## Future Enhancements

Potential improvements to consider:

1. **Multi-provider OAuth**: Add GitHub, Microsoft login options
2. **Two-Factor Authentication**: Add 2FA for enhanced security
3. **Role-based Access**: Implement admin/user roles
4. **Social Features**: Share conversations, public profiles
5. **Analytics Dashboard**: User engagement metrics
6. **API Keys**: Allow programmatic access with API keys

## Conclusion

This authentication system provides a secure, user-friendly way to manage access to the AI Book application while maintaining privacy for anonymous users and encouraging conversion to authenticated accounts. The implementation follows security best practices and provides a solid foundation for future enhancements.