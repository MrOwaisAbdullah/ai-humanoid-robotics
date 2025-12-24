# API Contracts: User Authentication

**Version**: 1.0.0
**Date**: 2025-01-21
**Base URL**: `/api/v1/auth`

## Authentication Overview

All endpoints return JSON responses with consistent format:
- Success: `{ "success": true, "data": {...} }`
- Error: `{ "success": false, "error": "Error message", "code": "ERROR_CODE" }`

## JWT Token Format

```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "emailVerified": true,
  "role": "user",
  "iat": 1642781400,
  "exp": 1643386200,
  "type": "access"
}
```

## Endpoints

### 1. Register User

**POST** `/register`

Creates a new user account with email and password. Automatically sends verification email.

#### Request Body
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123",
  "confirmPassword": "SecurePass123"
}
```

#### Success Response (201)
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "emailVerified": false,
      "createdAt": "2025-01-21T10:00:00Z"
    },
    "message": "Registration successful. Please check your email to verify your account."
  }
}
```

#### Error Responses
- **400 Bad Request**: Invalid input data
  ```json
  {
    "success": false,
    "error": "Passwords do not match",
    "code": "PASSWORDS_MISMATCH"
  }
  ```
- **409 Conflict**: Email already exists
  ```json
  {
    "success": false,
    "error": "User with this email already exists",
    "code": "EMAIL_EXISTS"
  }
  ```

### 2. Login

**POST** `/login`

Authenticates a user and returns a JWT token valid for 7 days.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "emailVerified": true,
      "preferences": {
        "theme": "dark",
        "language": "en",
        "timezone": "UTC"
      }
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresAt": "2025-01-28T10:30:00Z"
  }
}
```

#### Error Responses
- **401 Unauthorized**: Invalid credentials
  ```json
  {
    "success": false,
    "error": "Incorrect email or password",
    "code": "INVALID_CREDENTIALS"
  }
  ```
- **403 Forbidden**: Email not verified
  ```json
  {
    "success": false,
    "error": "Please verify your email before logging in",
    "code": "EMAIL_NOT_VERIFIED"
  }
  ```

### 3. Logout

**POST** `/logout`

Invalidates the current session token.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

### 4. Refresh Token

**POST** `/refresh`

Refreshes an existing JWT token.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresAt": "2025-01-28T11:00:00Z"
  }
}
```

### 5. Get Current User

**GET** `/me`

Retrieves the current authenticated user's profile including preferences.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "emailVerified": true,
      "role": "user",
      "createdAt": "2025-01-21T10:00:00Z",
      "preferences": {
        "theme": "dark",
        "language": "en",
        "timezone": "UTC",
        "notificationPreferences": {
          "emailNotifications": true,
          "chatReminders": false,
          "featureUpdates": true,
          "securityAlerts": true
        },
        "chatSettings": {
          "modelPreference": "gpt-4",
          "temperature": 0.7,
          "maxTokens": 2000,
          "saveHistory": true,
          "showSources": true
        }
      }
    }
  }
}
```

### 6. Update Profile

**PUT** `/me`

Updates the current user's profile information and preferences.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Request Body
```json
{
  "name": "John Smith",
  "timezone": "America/New_York",
  "language": "en",
  "preferences": {
    "theme": "light",
    "notificationPreferences": {
      "emailNotifications": false
    },
    "chatSettings": {
      "temperature": 0.8
    }
  }
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Smith",
      "updatedAt": "2025-01-21T11:00:00Z",
      "preferences": { /* updated preferences */ }
    }
  }
}
```

### 7. Request Password Reset

**POST** `/password-reset`

Initiates the password reset process. Always returns success to prevent email enumeration.

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "message": "If an account exists with this email, a password reset link has been sent."
  }
}
```

### 8. Confirm Password Reset

**POST** `/password-reset/confirm`

Confirms and completes password reset with a token valid for 1 hour.

#### Request Body
```json
{
  "token": "reset_token_here",
  "password": "NewSecurePass123",
  "confirmPassword": "NewSecurePass123"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "message": "Password has been reset successfully"
  }
}
```

#### Error Responses
- **400 Bad Request**: Invalid or expired token
  ```json
  {
    "success": false,
    "error": "Invalid or expired reset token",
    "code": "INVALID_TOKEN"
  }
  ```

### 9. Verify Email

**POST** `/verify-email`

Verifies a user's email address with a token valid for 24 hours.

#### Request Body
```json
{
  "token": "verification_token_here"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "message": "Email verified successfully"
  }
}
```

### 10. Resend Verification Email

**POST** `/verify-email/resend`

Resends the email verification link.

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "message": "Verification email has been sent"
  }
}
```

### 11. Link Anonymous Sessions

**POST** `/link-sessions`

Links anonymous chat sessions to the authenticated user.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Request Body
```json
{
  "anonymousSessionIds": ["uuid1", "uuid2", "uuid3"]
}
```

#### Success Response (200)
```json
{
  "success": true,
  "data": {
    "linkedSessions": 3,
    "message": "Anonymous sessions linked successfully"
  }
}
```

## Error Codes Reference

| Code | Description | HTTP Status |
|------|-------------|-------------|
| INVALID_CREDENTIALS | Invalid email or password | 401 |
| EMAIL_NOT_VERIFIED | Email address not verified | 403 |
| EMAIL_EXISTS | Email already registered | 409 |
| PASSWORDS_MISMATCH | Password confirmation doesn't match | 400 |
| INVALID_TOKEN | Token is invalid or expired | 400 |
| TOKEN_EXPIRED | Token has expired | 400 |
| RATE_LIMIT_EXCEEDED | Too many requests | 429 |
| USER_NOT_FOUND | User does not exist | 404 |
| INVALID_PASSWORD | Password doesn't meet requirements | 400 |
| UNAUTHORIZED | No valid token provided | 401 |
| FORBIDDEN | Access denied | 403 |
| VALIDATION_ERROR | Input validation failed | 400 |
| SESSION_LINK_FAILED | Failed to link anonymous sessions | 400 |

## Rate Limiting

All authentication endpoints have the following rate limits:

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /register | 5 requests | 15 minutes |
| POST /login | 10 requests | 15 minutes |
| POST /password-reset | 3 requests | 1 hour |
| POST /verify-email/resend | 3 requests | 1 hour |
| POST /link-sessions | 10 requests | 1 hour |

## Security Headers

All API responses include these security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## WebSocket Authentication

For WebSocket connections, include the token as a query parameter:

```
ws://localhost:8000/ws?token=<jwt_token>
```

The server will validate the token and establish the connection if valid.

## Frontend API Client

```typescript
// frontend/src/services/api.ts

export class AuthAPI {
  private baseURL = '/api/v1/auth';

  async register(data: CreateUserData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async login(data: LoginData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async logout(token: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    return response.json();
  }

  async getProfile(token: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.json();
  }

  async updateProfile(data: UpdateProfileData, token: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseURL}/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async linkAnonymousSessions(sessionIds: string[], token: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/link-sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ anonymousSessionIds: sessionIds })
    });
    return response.json();
  }
}
```

## Middleware Implementation

```typescript
// Frontend request interceptor
export const apiClient = axios.create({
  baseURL: '/api/v1'
});

// Add JWT token to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await authAPI.refresh(refreshToken);
          localStorage.setItem('auth_token', data.token);
          // Retry the original request
          error.config.headers.Authorization = `Bearer ${data.token}`;
          return apiClient.request(error.config);
        } catch {
          // Refresh failed, redirect to login
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```