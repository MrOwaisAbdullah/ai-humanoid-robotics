# Google OAuth Setup Instructions

## The Problem
The user was experiencing `Error 400: redirect_uri_mismatch` when trying to authenticate with Google OAuth.

## The Root Cause
The `AUTH_REDIRECT_URI` environment variable was incorrectly set to the frontend URL instead of the backend callback URL.

## The Solution

### 1. Correct OAuth Flow
The correct OAuth flow should be:
1. Frontend (GitHub Pages) calls `/auth/login/google`
2. Backend generates OAuth URL with `redirect_uri=https://mrowaisabdullah-ai-humanoid-robotics.hf.space/auth/google/callback`
3. User authenticates with Google
4. Google redirects to backend's callback URL (`/auth/google/callback`)
5. Backend processes the callback and redirects to frontend with token

### 2. Environment Variables
Ensure your `.env` file has the correct values:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
AUTH_REDIRECT_URI=https://mrowaisabdullah-ai-humanoid-robotics.hf.space/auth/google/callback
FRONTEND_URL=https://mrowaisabdullah.github.io

# CORS Configuration
ALLOWED_ORIGINS=https://mrowaisabdullah.github.io,https://huggingface.co,https://mrowaisabdullah-ai-humanoid-robotics.hf.space
```

### 3. Google Cloud Console Configuration
In your Google Cloud Console, you must add the following authorized redirect URIs:

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Select your OAuth 2.0 Client ID
3. In "Authorized redirect URIs", add:
   - `https://mrowaisabdullah-ai-humanoid-robotics.hf.space/auth/google/callback`
   - `http://localhost:7860/auth/google/callback` (for local development)

### 4. Deployment Steps
After updating the environment variables:

1. Commit and push the changes to your repository
2. Redeploy your HuggingFace Space with the new environment variables
3. Test the OAuth flow by clicking the Google login button on your frontend

### 5. Common Issues and Fixes

#### Issue: redirect_uri_mismatch error
- **Fix**: Ensure the `AUTH_REDIRECT_URI` in your `.env` file exactly matches what's configured in Google Cloud Console
- The redirect URI should be your backend's callback endpoint, not your frontend

#### Issue: CORS errors
- **Fix**: Add your HuggingFace Space URL to `ALLOWED_ORIGINS` in the `.env` file

#### Issue: Frontend doesn't receive the token
- **Fix**: Ensure `FRONTEND_URL` is correctly set to your GitHub Pages URL
- The backend will redirect to `${FRONTEND_URL}/auth/callback?token=${access_token}` after successful authentication

## Testing the OAuth Flow

### Local Testing
1. Set `AUTH_REDIRECT_URI=http://localhost:7860/auth/google/callback` in your local `.env`
2. Add this URI to your Google Cloud Console authorized redirect URIs
3. Run the backend locally and test

### Production Testing
1. Use the production HuggingFace Space URL in `AUTH_REDIRECT_URI`
2. Ensure the production URL is added to Google Cloud Console
3. Deploy and test the full flow

## Security Considerations

1. **Never expose secrets**: Ensure `.env` files are never committed to version control
2. **Use HTTPS**: Always use HTTPS URLs in production
3. **Validate origins**: Keep `ALLOWED_ORIGINS` restrictive to prevent CORS attacks
4. **Token security**: JWT tokens are set to expire after 7 days by default

## Troubleshooting Checklist

- [ ] `AUTH_REDIRECT_URI` points to backend, not frontend
- [ ] URI in Google Cloud Console matches `AUTH_REDIRECT_URI` exactly
- [ ] Backend URL is added to `ALLOWED_ORIGINS`
- [ ] Google Client ID and Secret are correct
- [ ] Backend is deployed with updated environment variables
- [ ] Frontend URL matches `FRONTEND_URL` in .env