import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { LoginButton } from './LoginButton';

export const AuthenticationBanner: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="bg-[#10a37f]/10 dark:bg-[#10a37f]/20 border-l-4 border-[#10a37f] p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-[#10a37f]"
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
          <p className="text-sm text-zinc-900 dark:text-[#5eead4]">
            <strong>Sign in to save your chat history</strong> - As a guest, you have 3 messages remaining.
            Sign in to get unlimited access and save your conversations.
          </p>
          <div className="mt-2">
            <LoginButton className="text-sm px-4 py-2 rounded-lg shadow-sm">
              Sign in
            </LoginButton>
          </div>
        </div>
      </div>
    </div>
  );
};

interface AnonymousLimitBannerProps {
  messageCount?: number;
}

export const AnonymousLimitBanner: React.FC<AnonymousLimitBannerProps> = ({ messageCount = 3 }) => {
  const remainingMessages = Math.max(0, 3 - messageCount);
  const isLimitReached = messageCount >= 3;

  return (
    <div className="bg-[#10a37f]/10 dark:bg-[#10a37f]/20 border-l-4 border-[#10a37f] p-4 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-[#10a37f]"
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
          <p className="text-sm text-zinc-900 dark:text-[#5eead4]">
            <strong>
              {isLimitReached
                ? "Message limit reached"
                : `You have ${remainingMessages} message${remainingMessages === 1 ? '' : 's'} remaining`
              }
            </strong> -
            {isLimitReached
              ? " You've used your 3 free messages as a guest. Sign in to continue chatting and save your conversation history."
              : " Sign in to get unlimited access and save your conversations."
            }
          </p>
          <div className="mt-2">
            <LoginButton className="text-sm bg-[#10a37f] hover:bg-[#0d8f6c] text-white px-3 py-1 rounded">
              {isLimitReached ? "Sign in now" : "Sign in"}
            </LoginButton>
          </div>
        </div>
      </div>
    </div>
  );
};