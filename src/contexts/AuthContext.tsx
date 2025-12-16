/**
 * Authentication context for managing user authentication state.
 */

import React, { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react';
import { api } from '../services/api';
import { API_BASE_URL } from '../config/api';

// Types
export interface User {
  id: string;
  email: string;
  name?: string;
  email_verified: boolean;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Background data interface for registration
export interface RegistrationBackground {
  software_experience?: 'Beginner' | 'Intermediate' | 'Advanced';
  hardware_expertise?: 'None' | 'Arduino' | 'ROS-Pro';
  years_of_experience?: number;
  primary_interest?: 'Computer Vision' | 'Machine Learning' | 'Control Systems' | 'Path Planning' | 'State Estimation' | 'Sensors & Perception' | 'Hardware Integration' | 'Human-Robot Interaction' | 'All of the Above';
}

export interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<{ migratedSessions?: number; migratedMessages?: number }>;
  register: (email: string, password: string, name?: string, background?: RegistrationBackground) => Promise<{ migratedSessions?: number; migratedMessages?: number }>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

// Create context
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Provider props
interface AuthProviderProps {
  children: ReactNode;
}

// API base URL is now imported from config/api.ts

// Auth Provider Component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: false, // Start with false for static deployments
    isAuthenticated: false,
  });

  // Token refresh timer ref
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Flag to prevent multiple simultaneous auth checks
  const isCheckingAuth = useRef(false);

  // Check authentication on mount
  useEffect(() => {
    // Skip auth check for static deployments (GitHub Pages)
    if (typeof window !== 'undefined' && window.location.hostname === 'mrowaisabdullah.github.io') {
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
      return;
    }

    // Only check auth if we haven't already checked
    if (!isCheckingAuth.current) {
      checkAuth();
    }
  }, []);

  // Cleanup refresh timer on unmount
  useEffect(() => {
    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, []);

  // Check authentication status
  const checkAuth = async () => {
    console.log('AuthContext: checkAuth started');
    // Prevent multiple simultaneous checks
    if (isCheckingAuth.current) {
      console.log('AuthContext: checkAuth skipped - already checking');
      return;
    }

    isCheckingAuth.current = true;

    try {
      console.log('AuthContext: Setting isLoading=true');
      setState(prev => ({ ...prev, isLoading: true }));

      // Check for stored token in localStorage
      const storedToken = localStorage.getItem('access_token');
      console.log('AuthContext: Stored token present?', !!storedToken);

      if (storedToken) {
        // Try to get current user from API
        console.log('AuthContext: Fetching /auth/me');
        const response = await api.get('/auth/me');
        console.log('AuthContext: /auth/me response status:', response.status);

        if (response.data) {
          console.log('AuthContext: User authenticated, setting state');
          setState({
            user: response.data,
            isLoading: false,
            isAuthenticated: true,
          });
          // Start token refresh timer when authenticated
          startTokenRefreshTimer();
          return;
        }
      }

      // No token or invalid token - user is not authenticated
      console.log('AuthContext: No token or invalid response, clearing state');
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });

    } catch (error: any) {
      console.error('AuthContext: checkAuth error:', error);
      // Not authenticated - clear stored token and auth header
      if (error?.code === 'ECONNABORTED') {
        console.error('Authentication check timed out - backend may be down');
      } else if (error?.response?.status === 401) {
        // Expected for users without authentication
        console.log('User not authenticated');
      } else {
        console.error('Authentication check failed:', error?.message || 'Unknown error');
      }
      localStorage.removeItem('access_token');
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
    } finally {
      isCheckingAuth.current = false;
      console.log('AuthContext: checkAuth finished');
    }
  };

  // Login function
  const login = async (email: string, password: string) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Get anonymous session ID from localStorage or generate one
      let anonymousSessionId = localStorage.getItem('anonymous_session_id');
      if (!anonymousSessionId) {
        // Try to get from existing chat widget
        const chatWidget = document.querySelector('[data-anonymous-session-id]');
        if (chatWidget) {
          anonymousSessionId = chatWidget.getAttribute('data-anonymous-session-id');
        }
      }

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      // Add anonymous session ID header if available
      if (anonymousSessionId) {
        headers['X-Anonymous-Session-ID'] = anonymousSessionId;
      }

      console.log('Attempting login to:', `${API_BASE_URL}/auth/login`);
      console.log('Login data:', { email, password: '***' });
      console.log('Headers:', headers);

      const response = await api.post(
        '/auth/login',
        { email, password },
        { headers }
      );

      if (response.status === 200) {
        // Store JWT token if provided
        if (response.data.access_token) {
          // Store token in localStorage (or you could use httpOnly cookies)
          localStorage.setItem('access_token', response.data.access_token);
        }

        // Clear anonymous session ID from storage
        localStorage.removeItem('anonymous_session_id');

        // Set user data from login response if available
        if (response.data.user) {
          console.log('Setting user data from login response:', response.data.user);
          setState(prevState => ({
            ...prevState,
            user: response.data.user,
            isLoading: false,
            isAuthenticated: true,
          }));
          console.log('State after setting user data');
          // Start token refresh timer when authenticated
          startTokenRefreshTimer();
        } else {
          console.log('No user data in response, calling checkAuth()');
          // If no user data in response, try to fetch it
          await checkAuth();
        }

        // Return migration info
        return {
          migratedSessions: response.data.migrated_sessions || 0,
          migratedMessages: response.data.migrated_messages || 0
        };
      }
      return { migratedSessions: 0, migratedMessages: 0 };
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  // Register function
  const register = async (
    email: string,
    password: string,
    name?: string,
    background?: RegistrationBackground
  ) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Get anonymous session ID from localStorage or generate one
      let anonymousSessionId = localStorage.getItem('anonymous_session_id');
      if (!anonymousSessionId) {
        // Try to get from existing chat widget
        const chatWidget = document.querySelector('[data-anonymous-session-id]');
        if (chatWidget) {
          anonymousSessionId = chatWidget.getAttribute('data-anonymous-session-id');
        }
      }

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      // Add anonymous session ID header if available
      if (anonymousSessionId) {
        headers['X-Anonymous-Session-ID'] = anonymousSessionId;
      }

      console.log('Attempting registration to:', `${API_BASE_URL}/auth/register`);

      const response = await api.post(
        '/auth/register',
        {
          email,
          password,
          name,
          software_experience: background?.software_experience,
          hardware_expertise: background?.hardware_expertise,
          years_of_experience: background?.years_of_experience,
          primary_interest: background?.primary_interest,
        },
        { headers }
      );

      if (response.status === 200) {
        // Store JWT token if provided
        if (response.data.access_token) {
          // Store token in localStorage (or you could use httpOnly cookies)
          localStorage.setItem('access_token', response.data.access_token);
        }

        // Clear anonymous session ID from storage
        localStorage.removeItem('anonymous_session_id');

        // After successful registration, fetch user data
        await checkAuth();

        // Return migration info
        return {
          migratedSessions: response.data.migrated_sessions || 0,
          migratedMessages: response.data.migrated_messages || 0
        };
      }
      return { migratedSessions: 0, migratedMessages: 0 };
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  // Refresh token function
  const refreshToken = async (): Promise<boolean> => {
    try {
      const response = await api.post('/auth/refresh');

      if (response.data && response.data.token) {
        // Store new token
        localStorage.setItem('access_token', response.data.token);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  };

  // Start token refresh timer
  const startTokenRefreshTimer = () => {
    // Clear any existing timer
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
    }

    // Check token every 5 minutes
    refreshTimerRef.current = setInterval(async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          // Decode JWT to check expiration
          const payload = JSON.parse(atob(token.split('.')[1]));
          const expiresAt = payload.exp * 1000; // Convert to milliseconds
          const now = Date.now();

          // Refresh if expiring within 5 minutes
          if (expiresAt - now < 5 * 60 * 1000) {
            const refreshed = await refreshToken();
            if (!refreshed) {
              // Token refresh failed, logout
              logout();
            }
          }
        } catch (error) {
          console.error('Error checking token expiration:', error);
          logout();
        }
      }
    }, 60000); // Check every minute
  };

  // Logout function
  const logout = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      await api.post('/auth/logout');
    } catch (error) {
      // Even if logout request fails, clear local state
      console.error('Logout error:', error);
    } finally {
      // Clear refresh timer
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
      // Clear token from localStorage
      localStorage.removeItem('access_token');
      // Clear auth state
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
    }
  };

  // Context value
  const value: AuthContextValue = {
    ...state,
    login,
    register,
    logout,
    checkAuth,
    refreshToken,
  };

  // Debug logging
  if (process.env.NODE_ENV === 'development') {
    console.log('AuthContext state update:', state);
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export context for testing
export { AuthContext };
// Cookie utility functions
export const getCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null;

  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    const cookieValue = parts.pop()?.split(';').shift();
    return cookieValue || null;
  }

  return null;
};

export const setCookie = (name: string, value: string, days: number = 7): void => {
  if (typeof document === 'undefined') return;

  const expires = new Date();
  expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));

  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
};

export const deleteCookie = (name: string): void => {
  if (typeof document === 'undefined') return;

  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
};