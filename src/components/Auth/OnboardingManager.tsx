import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { OnboardingModal } from './OnboardingModal';

export const OnboardingManager: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const checkPreferences = async () => {
      if (!isAuthenticated || checked) return;

      try {
        const response = await axios.get('/auth/preferences');
        const chatSettings = response.data.chat_settings || {};
        
        // Check if background info is missing
        if (!chatSettings.software_background || !chatSettings.hardware_background) {
          setShowModal(true);
        }
      } catch (error) {
        console.error('Failed to check preferences:', error);
        // Optionally show modal on error or just skip
      } finally {
        setChecked(true);
      }
    };

    checkPreferences();
  }, [isAuthenticated, checked]);

  return (
    <OnboardingModal 
      isOpen={showModal} 
      onComplete={() => setShowModal(false)} 
    />
  );
};
