import axios, { AxiosInstance, AxiosError } from 'axios';
import { AuthResponse, CreateUserData, LoginData, UpdateProfileData, PasswordResetData, ConfirmPasswordResetData } from '../types/auth-new';

// API base URL - adjust according to your backend
// For Docusaurus, this should be configured in docusaurus.config.js or use window.location for relative URLs
const API_BASE_URL = typeof window !== 'undefined'
  ? (window as any).__API_BASE_URL__ || 'http://localhost:7860'
  : 'http://localhost:7860';

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // For cookies if needed
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await authAPI.refreshToken(refreshToken);
          const { token, refreshToken: newRefreshToken } = response.data;

          localStorage.setItem('auth_token', token);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }

          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token, logout user
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Authentication API endpoints
export const authAPI = {
  // Register new user
  async register(data: CreateUserData): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/register', data);
    return response.data;
  },

  // Login user
  async login(data: LoginData): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/login', data);
    return response.data;
  },

  // Logout user
  async logout(): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/logout');
    return response.data;
  },

  // Get current user
  async getCurrentUser(): Promise<AuthResponse> {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  },

  // Update profile
  async updateProfile(data: UpdateProfileData): Promise<AuthResponse> {
    const response = await apiClient.put('/api/v1/auth/me', data);
    return response.data;
  },

  // Request password reset
  async requestPasswordReset(data: PasswordResetData): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/password-reset', data);
    return response.data;
  },

  // Confirm password reset
  async confirmPasswordReset(data: ConfirmPasswordResetData): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/password-reset/confirm', data);
    return response.data;
  },

  // Verify email
  async verifyEmail(token: string): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/verify-email', { token });
    return response.data;
  },

  // Resend verification email
  async resendVerificationEmail(email: string): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/verify-email/resend', { email });
    return response.data;
  },

  // Refresh token
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post('/api/v1/auth/refresh', { refreshToken });
    return response.data;
  },

  // Link anonymous sessions
  async linkAnonymousSessions(sessionIds: string[]): Promise<any> {
    const response = await apiClient.post('/api/v1/auth/link-sessions', {
      anonymousSessionIds: sessionIds
    });
    return response.data;
  }
};

// Helper functions for local storage management
export const tokenManager = {
  setTokens(token: string, refreshToken?: string) {
    localStorage.setItem('auth_token', token);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
  },

  getTokens() {
    return {
      token: localStorage.getItem('auth_token'),
      refreshToken: localStorage.getItem('refresh_token')
    };
  },

  clearTokens() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  },

  // Check if token is expired
  isTokenExpired(token?: string): boolean {
    const storedToken = token || localStorage.getItem('auth_token');
    if (!storedToken) return true;

    try {
      const payload = JSON.parse(atob(storedToken.split('.')[1]));
      const now = Date.now() / 1000;
      return payload.exp < now;
    } catch {
      return true;
    }
  },

  // Get token expiration time
  getTokenExpiry(token?: string): Date | null {
    const storedToken = token || localStorage.getItem('auth_token');
    if (!storedToken) return null;

    try {
      const payload = JSON.parse(atob(storedToken.split('.')[1]));
      return new Date(payload.exp * 1000);
    } catch {
      return null;
    }
  }
};

// Error handling utilities
export const handleAuthError = (error: AxiosError<AuthResponse>): string => {
  if (error.response?.data?.error) {
    return error.response.data.error;
  }

  switch (error.response?.status) {
    case 401:
      return 'Your session has expired. Please login again.';
    case 403:
      return 'You do not have permission to perform this action.';
    case 429:
      return 'Too many requests. Please try again later.';
    case 500:
      return 'Server error. Please try again later.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
};

// Export the configured axios instance for other API calls
export default apiClient;