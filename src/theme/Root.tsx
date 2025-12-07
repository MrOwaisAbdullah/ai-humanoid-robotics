import React from 'react';
import type { RootProps } from '@docusaurus/types';
import CustomChatKitWidget from '../components/ChatWidget/CustomChatKitWidget';
import ChatWidgetContainer from '../components/ChatWidget/ChatWidgetContainer';
import { AuthProvider } from '../contexts/AuthContext';
import { useAuth } from '../contexts/AuthContext';
import { LoginButton } from '../components/Auth/LoginButton';
import { UserProfile } from '../components/Auth/UserProfile';
import { OAuthCallbackHandler } from '../contexts/AuthContext';

// Authentication-aware wrapper for the main content
function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  // Handle OAuth callback
  if (typeof window !== 'undefined' && window.location.pathname === '/auth/callback') {
    return <OAuthCallbackHandler />;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <>
      {/* Auth buttons in navbar area */}
      <div className="fixed top-4 right-4 z-50 flex items-center gap-2">
        {isAuthenticated ? (
          <UserProfile />
        ) : (
          <LoginButton />
        )}
      </div>
      {children}
    </>
  );
}

export default function Root({children}: RootProps): React.JSX.Element {
  // Get the ChatKit endpoint from environment variables
  // Use local development URL for localhost, deployed URL for production
  const getChatkitEndpoint = () => {
    // In Docusaurus, we use window location detection instead of process.env for client-side code
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:7860/api/chat';
    }

    // For production, use the HuggingFace Spaces URL
    // Environment variables can be configured during build/deployment
    return 'https://mrowaisabdullah-ai-humanoid-robotics.hf.space/api/chat';
  };

  // Default to new ChatGPT-style widget, fallback to CustomChatKitWidget
  const useNewChatWidget = true; // Can be made configurable via build-time env vars

  return (
    <>
      {children}
      {useNewChatWidget ? (
        <ChatWidgetContainer
          apiUrl={getChatkitEndpoint()}
          maxTextSelectionLength={2000}
          fallbackTextLength={5000}
        />
      ) : (
        <CustomChatKitWidget
          apiEndpoint={getChatkitEndpoint()}
          title="Physical AI & Robotics Assistant"
        />
      )}
    </>
  );
}