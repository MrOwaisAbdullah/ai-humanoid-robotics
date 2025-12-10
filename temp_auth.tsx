/**
 * Authentication context for managing user authentication state.
 */

import React, { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react';
import axios from 'axios';

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

// Determine API base URL
export const getApiBaseUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:7860';

  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:7860';
  }
  return 'https://mrowaisabdullah-ai-humanoid-robotics.hf.space';
};

// API base URL
const API_BASE_URL = getApiBaseUrl();

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;
axios.defaults.withCredentials = true; // Important for cookies

// Ensure all requests have proper headers
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Set a reasonable timeout for requests
axios.defaults.timeout = 10000; // 10 seconds

// Auth Provider Component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  // Token refresh timer ref
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Check authentication on mount
  useEffect(() => {
    checkAuth();
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
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Check for stored token in localStorage
      const storedToken = localStorage.getItem('access_token');

      if (storedToken) {
        // Set the authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      }

      // Try to get current user from API
      const response = await axios.get('/auth/me');

      if (response.data) {
        setState({
          user: response.data,
          isLoading: false,
          isAuthenticated: true,
        });
        // Start token refresh timer when authenticated
        startTokenRefreshTimer();
      } else {
        setState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
        });
      }
    } catch (error: any) {
      // Not authenticated - clear stored token and auth header
      if (error?.code === 'ECONNABORTED') {
        console.error('Authentication check timed out - backend may be down');
      } else if (error?.response?.status === 401) {
        console.error('Token expired or invalid');
      } else {
        console.error('Authentication check failed:', error?.message || 'Unknown error');
      }
      localStorage.removeItem('access_token');
      delete axios.defaults.headers.common['Authorization'];
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
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

      const response = await axios.post(
        '/auth/login',
        { email, password },
        { headers }
      );

      if (response.status === 200) {
        // Store JWT token if provided
        if (response.data.access_token) {
          // Store token in localStorage (or you could use httpOnly cookies)
          localStorage.setItem('access_token', response.data.access_token);
          // Set default authorization header for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
        }

        // Clear anonymous session ID from storage
        localStorage.removeItem('anonymous_session_id');

        // After successful login, fetch user data
        await checkAuth();

        // Return migration info
        return {
          migratedSessions: response.data.migrated_sessions || 0,
          migratedMessages: response.data.migrated_messages || 0
        };
      }
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

      const response = await axios.post(
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
          // Set default authorization header for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
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
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  // Refresh token function
  const refreshToken = async (): Promise<boolean> => {
    try {
      const response = await axios.post('/auth/refresh');

      if (response.data && response.data.token) {
        // Store new token
        localStorage.setItem('access_token', response.data.token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
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

      await axios.post('/auth/logout');
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
      // Clear authorization header
      delete axios.defaults.headers.common['Authorization'];
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
