import React from 'react';
import type { RootProps } from '@docusaurus/types';
import CustomChatKitWidget from '../components/ChatWidget/CustomChatKitWidget';
import ChatWidgetContainer from '../components/ChatWidget/ChatWidgetContainer';
import FocusMode from '../components/Localization/FocusMode';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { UserProvider } from '../contexts/UserContext';
import { ReadingProvider } from '../contexts/ReadingContext';
import { LocalizationProvider } from '../contexts/LocalizationContext';
import { FocusModeProvider, useFocusMode } from '../contexts/FocusModeContext';
import { LoginButton } from '../components/Auth/LoginButton';
import { UserProfile } from '../components/Auth/UserProfile';
import { OAuthCallbackHandler } from '../components/Auth/OAuthCallbackHandler';
import { OnboardingManager } from '../components/Auth/OnboardingManager';
import { NavbarAuth } from '../components/Auth/NavbarAuth';

// Authentication-aware wrapper for the main content
function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const { isVisible, originalContent, translatedContent, closeFocusMode } = useFocusMode();

  // Handle OAuth callback
  if (typeof window !== 'undefined' && window.location.pathname === '/auth/callback') {
    return <OAuthCallbackHandler />;
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#10a37f]"></div>
      </div>
    );
  }

  return (
    <>
      {/* Inject Auth buttons into the Navbar */}
      <NavbarAuth />

      {/* Onboarding check for authenticated users */}
      {isAuthenticated && <OnboardingManager />}

      {children}

      {/* Focus Mode */}
      <FocusMode
        isVisible={isVisible}
        onClose={closeFocusMode}
        originalContent={originalContent}
        translatedContent={translatedContent}
        isLoading={false}
      />
    </>
  );
}

export default function Root({children}: RootProps): React.JSX.Element {
  // Get the ChatKit endpoint from environment variables
  const getChatkitEndpoint = () => {
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:7860/api/chat';
    }
    return 'https://mrowaisabdullah-ai-humanoid-robotics.hf.space/api/chat';
  };

  const useNewChatWidget = true;

  return (
    <AuthProvider>
      <UserProvider>
        <ReadingProvider>
          <LocalizationProvider>
            <FocusModeProvider>
              <AuthenticatedLayout>
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
              </AuthenticatedLayout>
            </FocusModeProvider>
          </LocalizationProvider>
        </ReadingProvider>
      </UserProvider>
    </AuthProvider>
  );
}