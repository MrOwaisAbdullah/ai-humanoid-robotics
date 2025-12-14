import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { OnboardingModal } from './OnboardingModal';
import { apiRequest } from '../../services/api';

export const OnboardingManager: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const checkOnboardingStatus = async () => {
      if (!isAuthenticated || checked) return;

      try {
        // Check if user has completed onboarding by checking background data
        const response = await apiRequest.get('/users/background');
        const background = response.data;

        // Show onboarding if user hasn't completed it
        // We check if the background was created recently (within 5 minutes)
        // or if it's still showing default values
        const now = new Date();
        const createdTime = new Date(background.created_at);
        const timeDiff = (now.getTime() - createdTime.getTime()) / (1000 * 60); // minutes

        if (!background || !background.id || timeDiff < 5) {
          setShowModal(true);
        }
      } catch (error) {
        console.error('Failed to check onboarding status:', error);
        // Show modal for new users if we can't check
        if (user && new Date().getTime() - new Date(user.created_at).getTime() < 10 * 60 * 1000) {
          setShowModal(true);
        }
      } finally {
        setChecked(true);
      }
    };

    checkOnboardingStatus();
  }, [isAuthenticated, checked, user]);

  const handleOnboardingComplete = () => {
    setShowModal(false);
    // Optionally reload user data or update state
  };

  return (
    <OnboardingModal
      isOpen={showModal}
      onComplete={handleOnboardingComplete}
    />
  );
};
