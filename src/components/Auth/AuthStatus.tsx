/**
 * Component that shows either a login button or user information
 * based on authentication status
 */

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LoginButton } from './LoginButton';
import { CompactLoginButton } from './LoginButton';

interface AuthStatusProps {
  className?: string;
  compact?: boolean;
  children?: React.ReactNode;
}

export const AuthStatus: React.FC<AuthStatusProps> = ({
  className = "",
  compact = false,
  children
}) => {
  const { isAuthenticated, user, logout } = useAuth();

  if (!isAuthenticated) {
    return compact ? (
      <CompactLoginButton className={className} />
    ) : (
      <LoginButton className={className}>
        {children}
      </LoginButton>
    );
  }

  const isDarkTheme = typeof window !== 'undefined' && document.documentElement.classList.contains('dark');

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      <div className="flex items-center space-x-2">
        <div className="flex items-center">
          {user?.image_url && (
            <img
              src={user.image_url}
              alt="Profile"
              className="h-8 w-8 rounded-full"
            />
          )}
          <div className={`text-sm ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>
            {user?.name || user?.email}
          </div>
        </div>
      </div>
      <button
        onClick={logout}
        className={`text-sm px-3 py-2 rounded-md transition-colors ${
          isDarkTheme
            ? 'text-gray-300 hover:text-white hover:bg-gray-700'
            : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
        } font-medium`}
      >
        Sign Out
      </button>
    </div>
  );
};