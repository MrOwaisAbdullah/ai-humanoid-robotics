import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { User, AuthContextType, CreateUserData, LoginData, UpdateProfileData, PasswordResetData, ConfirmPasswordResetData, AuthResponse } from '../types/auth-new';
import { authAPI, tokenManager } from '../services/auth-api';

// Auth state interface
interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

// Action types
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; token: string; refreshToken?: string } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_USER'; payload: User }
  | { type: 'SET_LOADING'; payload: boolean };

// Initial state function - called when component mounts, not at module load
const getInitialState = (): AuthState => {
  const tokens = tokenManager.getTokens();
  console.log('[AuthContext] getInitialState:', {
    hasToken: !!tokens.token,
    token: tokens.token ? `${tokens.token.substring(0, 20)}...` : null,
    isLoading: !!tokens.token
  });
  return {
    user: null,
    token: tokens.token,
    refreshToken: tokens.refreshToken,
    isLoading: !!tokens.token, // Start loading if token exists
    isAuthenticated: false,
    error: null,
  };
};

// Auth reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken || null,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      };
    case 'AUTH_FAILURE':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
        isAuthenticated: false,
      };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    default:
      return state;
  }
};

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// AuthProvider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, undefined, getInitialState);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const { token } = tokenManager.getTokens();

      console.log('[AuthContext] checkAuth:', {
        hasToken: !!token,
        isExpired: token ? tokenManager.isTokenExpired(token) : 'no token'
      });

      if (token && !tokenManager.isTokenExpired(token)) {
        try {
          dispatch({ type: 'AUTH_START' });
          const response = await authAPI.getCurrentUser();

          console.log('[AuthContext] getCurrentUser response:', response);

          // Backend returns user object directly, not wrapped in {success, user}
          if (response && response.id) {
            dispatch({
              type: 'SET_USER',
              payload: response,
            });
          } else {
            console.log('[AuthContext] Invalid response, clearing tokens');
            // Invalid token, clear it
            tokenManager.clearTokens();
            dispatch({ type: 'LOGOUT' });
          }
        } catch (error) {
          console.log('[AuthContext] checkAuth error:', error);
          // Token is invalid or error occurred
          tokenManager.clearTokens();
          dispatch({ type: 'LOGOUT' });
        }
      } else {
        console.log('[AuthContext] No valid token, logging out');
        // No valid token
        tokenManager.clearTokens();
        dispatch({ type: 'LOGOUT' });
      }
    };

    checkAuth();
  }, []);

  // Login function
  const login = async (data: LoginData): Promise<AuthResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await authAPI.login(data);

      if (response.success && response.user && response.token) {
        // Store tokens
        tokenManager.setTokens(response.token, response.refreshToken);

        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: response.user,
            token: response.token,
            refreshToken: response.refreshToken,
          },
        });
      } else {
        dispatch({
          type: 'AUTH_FAILURE',
          payload: response.error || 'Login failed',
        });
      }

      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.error || 'Login failed';
      dispatch({
        type: 'AUTH_FAILURE',
        payload: errorMessage,
      });
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  // Register function
  const register = async (data: CreateUserData): Promise<AuthResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await authAPI.register(data);

      console.log('Register response:', response);
      console.log('Has token:', !!response.token);
      console.log('Has refreshToken:', !!response.refreshToken);

      if (response.success && response.user && response.token) {
        // Store tokens
        tokenManager.setTokens(response.token, response.refreshToken);
        console.log('Tokens stored in localStorage');

        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: response.user,
            token: response.token,
            refreshToken: response.refreshToken,
          },
        });
      } else {
        console.log('Registration check failed:', {
          success: response.success,
          hasUser: !!response.user,
          hasToken: !!response.token
        });
        dispatch({
          type: 'AUTH_FAILURE',
          payload: response.error || 'Registration failed',
        });
      }

      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.error || 'Registration failed';
      dispatch({
        type: 'AUTH_FAILURE',
        payload: errorMessage,
      });
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      await authAPI.logout();
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API call failed:', error);
    }

    // Clear tokens and state
    tokenManager.clearTokens();
    dispatch({ type: 'LOGOUT' });
  };

  // Refresh token function
  const refreshAuthToken = async (): Promise<void> => {
    const { refreshToken } = tokenManager.getTokens();

    if (!refreshToken) {
      await logout();
      return;
    }

    try {
      const response = await authAPI.refreshToken(refreshToken);

      if (response.success && response.token) {
        tokenManager.setTokens(response.token, response.refreshToken);
        // State update will be handled by axios interceptor
      } else {
        await logout();
      }
    } catch (error) {
      await logout();
    }
  };

  // Update profile function
  const updateProfile = async (data: UpdateProfileData): Promise<AuthResponse> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await authAPI.updateProfile(data);

      if (response.success && response.user) {
        dispatch({
          type: 'SET_USER',
          payload: response.user,
        });
      } else {
        dispatch({
          type: 'AUTH_FAILURE',
          payload: response.error || 'Profile update failed',
        });
      }

      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Profile update failed';
      dispatch({
        type: 'AUTH_FAILURE',
        payload: errorMessage,
      });
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  // Password reset request
  const requestPasswordReset = async (data: PasswordResetData): Promise<AuthResponse> => {
    try {
      const response = await authAPI.requestPasswordReset(data);
      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Password reset request failed';
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  // Confirm password reset
  const confirmPasswordReset = async (data: ConfirmPasswordResetData): Promise<AuthResponse> => {
    try {
      const response = await authAPI.confirmPasswordReset(data);
      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Password reset confirmation failed';
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  // Verify email
  const verifyEmail = async (token: string): Promise<AuthResponse> => {
    try {
      const response = await authAPI.verifyEmail(token);

      // If user is logged in, update their email verification status
      if (state.user) {
        const updatedUser = { ...state.user, emailVerified: true };
        dispatch({
          type: 'SET_USER',
          payload: updatedUser,
        });
      }

      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Email verification failed';
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  // Resend verification email
  const resendVerificationEmail = async (email: string): Promise<AuthResponse> => {
    try {
      const response = await authAPI.resendVerificationEmail(email);
      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Resending verification email failed';
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  // Clear error function
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  // Context value
  const value: AuthContextType = {
    user: state.user,
    token: state.token,
    refreshToken: state.refreshToken,
    isLoading: state.isLoading,
    isAuthenticated: state.isAuthenticated,
    login,
    register,
    logout,
    refreshAuthToken,
    updateProfile,
    requestPasswordReset,
    confirmPasswordReset,
    verifyEmail,
    resendVerificationEmail,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export context for direct access if needed
export default AuthContext;