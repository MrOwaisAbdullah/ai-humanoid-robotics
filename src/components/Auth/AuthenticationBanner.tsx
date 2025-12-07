import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LoginButton } from './LoginButton';

export const AuthenticationBanner: React.FC = () => {
  const { isAuthenticated, login } = useAuth();

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-blue-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm text-blue-700">
            <strong>Sign in to save your chat history</strong> - As a guest, you have 3 messages remaining.
            Sign in with Google to get unlimited access and save your conversations.
          </p>
          <div className="mt-2">
            <LoginButton className="text-sm bg-blue-600 text-white hover:bg-blue-700" />
          </div>
        </div>
      </div>
    </div>
  );
};

export const AnonymousLimitBanner: React.FC<{ onUpgrade: () => void }> = ({ onUpgrade }) => {
  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-yellow-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm text-yellow-700">
            <strong>Message limit reached</strong> - You've used your 3 free messages as a guest.
            Sign in to continue chatting and save your conversation history.
          </p>
          <div className="mt-2">
            <button
              onClick={onUpgrade}
              className="text-sm bg-yellow-600 text-white hover:bg-yellow-700 px-3 py-1 rounded"
            >
              Sign in now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};