/**
 * Login button component that opens a modal for email/password authentication.
 */

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../../contexts/AuthContext';
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
}

export const LoginButton: React.FC<LoginButtonProps> = ({
  className = "",
  children
}) => {
  const { login, register, isLoading } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

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
      const migrationInfo = await login(data.email, data.password);
      setIsModalOpen(false);
      loginForm.reset();

      // Show migration success message if applicable
      if (migrationInfo && migrationInfo.migratedSessions && migrationInfo.migratedSessions > 0) {
        setSuccess(
          `Welcome back! We've migrated ${migrationInfo.migratedSessions} chat session${migrationInfo.migratedSessions > 1 ? 's' : ''} with ${migrationInfo.migratedMessages} message${migrationInfo.migratedMessages > 1 ? 's' : ''} to your account.`
        );
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Login failed. Please try again.');
    }
  };

  const handleRegister = async (data: RegisterFormData) => {
    try {
      setError(null);
      setSuccess(null);
      const migrationInfo = await register(data.email, data.password, data.name);
      setIsModalOpen(false);
      registerForm.reset();

      // Show migration success message if applicable
      if (migrationInfo && migrationInfo.migratedSessions && migrationInfo.migratedSessions > 0) {
        setSuccess(
          `Welcome! We've saved your ${migrationInfo.migratedSessions} chat session${migrationInfo.migratedSessions > 1 ? 's' : ''} with ${migrationInfo.migratedMessages} message${migrationInfo.migratedMessages > 1 ? 's' : ''} to your new account.`
        );
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
    }
  };

  const switchMode = () => {
    setIsLoginMode(!isLoginMode);
    setError(null);
    setSuccess(null);
    loginForm.reset();
    registerForm.reset();
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setError(null);
    setSuccess(null);
    loginForm.reset();
    registerForm.reset();
  };

  // Modal content with portal
  const modalContent = isModalOpen && mounted ? (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-black opacity-50"
          onClick={closeModal}
        />

        {/* Modal */}
        <div className="relative bg-white dark:bg-zinc-900 rounded-lg max-w-md w-full p-6">
          <button
            onClick={closeModal}
            className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-6">
            {isLoginMode ? 'Sign In' : 'Create Account'}
          </h2>

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
                <label htmlFor="password" className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                  Password
                </label>
                <input
                  {...loginForm.register('password')}
                  type="password"
                  id="password"
                  className="mt-1 block w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
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
                disabled={isLoading}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium ${primaryButtonClass} ${buttonClass}`}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
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
            <form onSubmit={registerForm.handleSubmit(handleRegister)} className="space-y-4">
              <div>
                <label htmlFor="reg-email" className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                  Email
                </label>
                <input
                  {...registerForm.register('email')}
                  type="email"
                  id="reg-email"
                  className="mt-1 block w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
                  placeholder="your@email.com"
                />
                {registerForm.formState.errors.email && (
                  <p className="mt-1 text-sm text-red-600">
                    {registerForm.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="reg-name" className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                  Name (optional)
                </label>
                <input
                  {...registerForm.register('name')}
                  type="text"
                  id="reg-name"
                  className="mt-1 block w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
                  placeholder="Your name"
                />
              </div>

              <div>
                <label htmlFor="reg-password" className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                  Password
                </label>
                <input
                  {...registerForm.register('password')}
                  type="password"
                  id="reg-password"
                  className="mt-1 block w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
                  placeholder="••••••••"
                />
                {registerForm.formState.errors.password && (
                  <p className="mt-1 text-sm text-red-600">
                    {registerForm.formState.errors.password.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="reg-confirm-password" className="block text-sm font-medium text-zinc-700 dark:text-zinc-200">
                  Confirm Password
                </label>
                <input
                  {...registerForm.register('confirmPassword')}
                  type="password"
                  id="reg-confirm-password"
                  className="mt-1 block w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md shadow-sm bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-[#10a37f] focus:border-[#10a37f] transition-colors"
                  placeholder="••••••••"
                />
                {registerForm.formState.errors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-600">
                    {registerForm.formState.errors.confirmPassword.message}
                  </p>
                )}
              </div>

              <div className="text-xs text-zinc-600 dark:text-zinc-400">
                Password must be at least 8 characters with letters and numbers
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium ${primaryButtonClass} ${buttonClass}`}
              >
                {isLoading ? 'Creating account...' : 'Create Account'}
              </button>

              <div className="text-center">
                <span className="text-sm text-zinc-600 dark:text-zinc-400">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={switchMode}
                    className="text-[#10a37f] hover:text-[#0d8f6c] dark:text-[#10a37f] font-medium"
                  >
                    Sign in
                  </button>
                </span>
              </div>
            </form>
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