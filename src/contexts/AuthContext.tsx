/**
 * Authentication context for managing user authentication state.
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
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

export interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<{ migratedSessions?: number; migratedMessages?: number }>;
  register: (email: string, password: string, name?: string) => Promise<{ migratedSessions?: number; migratedMessages?: number }>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
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

// Auth Provider Component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  // Check authentication on mount
  useEffect(() => {
    checkAuth();
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
      } else {
        setState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
        });
      }
    } catch (error) {
      // Not authenticated - clear stored token and auth header
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
  const register = async (email: string, password: string, name?: string) => {
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

  // Logout function
  const logout = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      await axios.post('/auth/logout');
    } catch (error) {
      // Even if logout request fails, clear local state
      console.error('Logout error:', error);
    } finally {
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