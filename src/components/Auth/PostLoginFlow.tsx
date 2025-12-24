import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { EmailVerificationBanner } from './EmailVerificationBanner';
import { LinkAnonymousChats } from '../Chat/LinkAnonymousChats';
import { OnboardingModal } from './OnboardingModal';

interface PostLoginFlowProps {
  onboardingRequired?: boolean;
  className?: string;
}

export const PostLoginFlow: React.FC<PostLoginFlowProps> = ({
  onboardingRequired = true,
  className = '',
}) => {
  const { user, isAuthenticated } = useAuth();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [hasLinkedChats, setHasLinkedChats] = useState(false);

  useEffect(() => {
    if (isAuthenticated && user) {
      // Check if onboarding is needed
      if (onboardingRequired) {
        // You can add logic here to check if user has completed onboarding
        // For now, we'll assume it's needed for new users
        const hasCompletedOnboarding = localStorage.getItem('onboarding_completed');
        if (!hasCompletedOnboarding) {
          setShowOnboarding(true);
        }
      }

      // Check if there are anonymous sessions to link
      const anonymousSessions = localStorage.getItem('anonymous_sessions');
      if (anonymousSessions) {
        try {
          const sessions = JSON.parse(anonymousSessions);
          if (Array.isArray(sessions) && sessions.length > 0) {
            setHasLinkedChats(true);
          }
        } catch (err) {
          // Invalid format, remove it
          localStorage.removeItem('anonymous_sessions');
        }
      }
    }
  }, [isAuthenticated, user, onboardingRequired]);

  const handleOnboardingComplete = () => {
    setShowOnboarding(false);
    localStorage.setItem('onboarding_completed', 'true');
  };

  const handleChatLinkSuccess = () => {
    setHasLinkedChats(false);
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Email Verification Banner */}
      <EmailVerificationBanner />

      {/* Link Anonymous Chats - Only show once per login */}
      {hasLinkedChats && (
        <LinkAnonymousChats
          onLinkSuccess={handleChatLinkSuccess}
          className="animate-fade-in"
        />
      )}

      {/* Onboarding Modal */}
      {showOnboarding && (
        <OnboardingModal
          isOpen={showOnboarding}
          onClose={handleOnboardingComplete}
          onComplete={handleOnboardingComplete}
        />
      )}
    </div>
  );
};