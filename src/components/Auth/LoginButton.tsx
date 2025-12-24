/**
 * Login button component that opens a modal for email/password authentication.
 */

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../../context/AuthContext';
import { RegistrationBackground } from '../../context/AuthContext';
import { RegistrationForm } from './RegistrationForm';
import { PasswordInput } from './PasswordInput';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

// Form validation schemas
const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[a-zA-Z]/, 'Password must contain at least one letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
  name: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type LoginFormData = z.infer<typeof loginSchema>;
type RegisterFormData = z.infer<typeof registerSchema>;

interface LoginButtonProps {
  className?: string;
  children?: React.ReactNode;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const LoginButton: React.FC<LoginButtonProps> = ({
  className = "",
  children,
  onSuccess,
  onError
}) => {
  const { login, register, isLoading } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [isSigningIn, setIsSigningIn] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Check if dark mode is active using document element class
  const isDarkTheme = typeof window !== 'undefined' && document.documentElement.classList.contains('dark');
  const modalBgClass = isDarkTheme ? 'bg-zinc-900' : 'bg-white';
  const textClass = isDarkTheme ? 'text-zinc-100' : 'text-zinc-900';
  const subTextClass = isDarkTheme ? 'text-zinc-400' : 'text-zinc-600';
  const inputClass = isDarkTheme
    ? 'mt-1 block w-full px-3 py-2 border border-zinc-600 rounded-md shadow-sm bg-zinc-800 text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f]'
    : 'mt-1 block w-full px-3 py-2 border border-zinc-300 rounded-md shadow-sm focus:ring-[#10a37f] focus:border-[#10a37f]';
  const labelClass = isDarkTheme ? 'block text-sm font-medium text-zinc-200' : 'block text-sm font-medium text-zinc-700';
  const buttonClass = isDarkTheme
    ? 'px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#10a37f] disabled:opacity-50'
    : 'px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#10a37f] disabled:opacity-50';
  const primaryButtonClass = isDarkTheme
    ? 'bg-[#10a37f] text-white hover:bg-[#0d8f6c]'
    : 'bg-[#10a37f] text-white hover:bg-[#0d8f6c]';
  const secondaryButtonClass = isDarkTheme
    ? 'text-zinc-300 bg-zinc-700 border-zinc-600 hover:bg-zinc-600'
    : 'text-zinc-700 bg-white border-zinc-300 hover:bg-zinc-50';

  // Login form
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  // Register form
  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      name: '',
    },
  });

  const handleLogin = async (data: LoginFormData) => {
    try {
      setError(null);
      setSuccess(null);
      setIsSigningIn(true);
      const response = await login({ email: data.email, password: data.password });
      setIsModalOpen(false);
      loginForm.reset();
      setIsSigningIn(false);

      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }

      // Show success message if applicable
      if (response.success && response.message) {
        setSuccess(response.message);
      }
    } catch (error: any) {
      let errorMessage = 'Login failed. Please try again.';
      setIsSigningIn(false);

      // Handle different types of errors more specifically
      if (error.response?.status === 404) {
        // Email not registered - show specific error
        errorMessage = 'This email is not registered. Please create an account first.';
      } else if (error.response?.status === 401) {
        errorMessage = 'Incorrect password. Please check your password and try again.';
      } else if (error.response?.status === 400) {
        errorMessage = error.response?.data?.detail || 'Invalid input. Please check all fields.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many login attempts. Please wait a moment and try again.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message?.includes('Network Error')) {
        errorMessage = 'Network connection failed. Please check your internet connection and try again.';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Login request timed out. Please try again.';
      }

      setError(errorMessage);

      // Call onError callback if provided
      if (onError) {
        onError(errorMessage);
      }
    }
  };

  const handleRegister = async (data: RegisterFormData & { background?: RegistrationBackground }) => {
    try {
      setError(null);
      setSuccess(null);
      const response = await register({
        email: data.email,
        name: data.name || '',
        password: data.password,
        confirmPassword: data.confirmPassword,
      });
      setIsModalOpen(false);
      registerForm.reset();

      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }

      // Show success message if applicable
      if (response.success && response.message) {
        setSuccess(response.message);
      }
    } catch (error: any) {
      let errorMessage = 'Registration failed. Please try again.';

      // Handle different types of errors more specifically
      if (error.response?.status === 409) {
        errorMessage = 'An account with this email already exists. Please try logging in instead.';
      } else if (error.response?.status === 400) {
        errorMessage = error.response?.data?.detail || 'Invalid input. Please check all fields and passwords requirements.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many registration attempts. Please wait a moment and try again.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message?.includes('Network Error')) {
        errorMessage = 'Network connection failed. Please check your internet connection and try again.';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Registration request timed out. Please try again.';
      }

      setError(errorMessage);

      // Call onError callback if provided
      if (onError) {
        onError(errorMessage);
      }
    }
  };

  const switchMode = () => {
    setIsLoginMode(!isLoginMode);
    setError(null);
    setSuccess(null);
    setIsSigningIn(false);
    loginForm.reset();
    registerForm.reset();
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setError(null);
    setSuccess(null);
    setIsSigningIn(false);
    loginForm.reset();
    registerForm.reset();
  };

  // Modal content with portal
  const modalContent = isModalOpen && mounted ? (
    <div className="fixed inset-0 z-[60] overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-2 sm:px-4 py-4">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-black opacity-50"
          onClick={closeModal}
        />

        {/* Modal */}
        <div className={`relative bg-white dark:bg-zinc-900 rounded-lg w-full ${!isLoginMode ? 'py-6 px-3 sm:px-6' : 'p-6'} ${!isLoginMode ? 'max-w-4xl' : 'max-w-md'}`}>
          <button
            onClick={closeModal}
            className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Only show title for login mode - RegistrationForm has its own title */}
          {isLoginMode && (
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-6">
              Sign In
            </h2>
          )}

          {/* Error/Success messages */}
          {error && (
            <div className="mb-4 p-3 text-sm text-red-700 bg-red-100 dark:text-red-200 dark:bg-red-900/30 rounded-md">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 p-3 text-sm text-green-700 bg-green-100 dark:text-green-200 dark:bg-green-900/30 rounded-md">
              {success}
            </div>
          )}

          {/* Login Form */}
          {isLoginMode ? (
            <form onSubmit={loginForm.handleSubmit(handleLogin)} className="space-y-4">
              <div>
                <label htmlFor="email" className={labelClass}>
                  Email
                </label>
                <input
                  {...loginForm.register('email')}
                  type="email"
                  id="email"
                  className="mt-1 block w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
                  placeholder="your@email.com"
                />
                {loginForm.formState.errors.email && (
                  <p className="mt-1 text-sm text-red-600">
                    {loginForm.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <PasswordInput
                  {...loginForm.register('password')}
                  id="password"
                  value={loginForm.watch('password')}
                  onChange={(e) => loginForm.setValue('password', e.target.value)}
                  className="px-3 py-2"
                  placeholder="••••••••"
                />
                {loginForm.formState.errors.password && (
                  <p className="mt-1 text-sm text-red-600">
                    {loginForm.formState.errors.password.message}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between">
                <a href="#" className="text-sm text-[#10a37f] hover:text-[#0d8f6c] dark:text-[#10a37f]">
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                disabled={isSigningIn}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium ${primaryButtonClass} ${buttonClass}`}
              >
                {isSigningIn ? 'Signing in...' : 'Sign In'}
              </button>

              <div className="text-center">
                <span className="text-sm text-zinc-600 dark:text-zinc-400">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={switchMode}
                    className="text-[#10a37f] hover:text-[#0d8f6c] dark:text-[#10a37f] font-medium"
                  >
                    Sign up
                  </button>
                </span>
              </div>
            </form>
          ) : (
            /* Register Form */
            <RegistrationForm
              onSubmit={async (data) => {
                await handleRegister({ ...data, background: data });
              }}
              onCancel={switchMode}
              isLoading={isLoading}
              error={error || undefined}
            />
          )}
        </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className={`${primaryButtonClass} ${buttonClass} ${className}`}
      >
        {children || 'Login'}
      </button>

      {/* Use createPortal to render modal at the document body level */}
      {mounted && createPortal(
        modalContent,
        document.body
      )}
    </>
  );
};

// Compact version for navigation
export const CompactLoginButton: React.FC<LoginButtonProps> = ({
  className = ''
}) => {
  const isDarkTheme = typeof window !== 'undefined' && document.documentElement.classList.contains('dark');

  return (
    <LoginButton
      className={`${
        isDarkTheme
          ? 'text-gray-200 hover:text-white hover:bg-gray-700'
          : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
      } px-3 py-2 rounded-md text-sm font-medium transition-colors ${className}`}
    >
      Sign In
    </LoginButton>
  );
};