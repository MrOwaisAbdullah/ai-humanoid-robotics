import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { OnboardingModal } from './OnboardingModal';
import { PersonalizationLibraryModal } from '../Personalization/PersonalizationLibraryModal';
import { apiRequest } from '../../services/api';
import { Sparkles, BookOpen } from 'lucide-react';

interface UserProfileProps {
  className?: string;
}

export const UserProfile: React.FC<UserProfileProps> = ({ className = '' }) => {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isLibraryOpen, setIsLibraryOpen] = useState(false);
  const [onboardingData, setOnboardingData] = useState<any>({});
  const [isLoadingOnboarding, setIsLoadingOnboarding] = useState(false);

  const handleLogout = async () => {
    await logout();
    setIsDropdownOpen(false);
  };

  const handleOpenLibrary = () => {
    setIsDropdownOpen(false);
    setIsLibraryOpen(true);
  };

  const handleOpenOnboarding = async () => {
    setIsLoadingOnboarding(true);
    try {
      const response = await apiRequest.get('/api/v1/background');
      if (response.data) {
        // Map backend response to form data
        const data = response.data;
        const formData = {
          experience_level: data.experience_level?.toLowerCase(),
          years_experience: data.years_experience,
          preferred_languages: data.preferred_languages || [],
          cpu_expertise: data.hardware_expertise?.cpu || 'none',
          gpu_expertise: data.hardware_expertise?.gpu || 'none',
          networking_expertise: data.hardware_expertise?.networking || 'none',
        };
        setOnboardingData(formData);
      }
    } catch (error) {
      console.error('Failed to load onboarding data:', error);
    } finally {
      setIsLoadingOnboarding(false);
      setIsDropdownOpen(false);
      setIsOnboardingOpen(true);
    }
  };

  if (!user) return null;

  return (
    <>
      <div className={`relative ${className}`}>
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="flex items-center gap-2 text-gray-700 dark:text-gray-200 hover:text-[#10a37f] dark:hover:text-[#10a37f] px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <img
            src={user.image_url || `https://ui-avatars.com/api/?name=${user.name}&background=random`}
            alt={user.name}
            className="w-6 h-6 rounded-full"
          />
          <span className="hidden md:block">{user.name}</span>
          <svg
            className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {isDropdownOpen && (
          <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-zinc-800 rounded-lg shadow-lg py-1 z-50 border border-gray-100 dark:border-zinc-700">
            <div className="px-4 py-2 border-b border-gray-100 dark:border-zinc-700">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{user.name}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
            </div>
            
            <button
              onClick={handleOpenLibrary}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-[#10a37f] dark:hover:text-[#10a37f] transition-colors flex items-center gap-2"
            >
              <BookOpen className="w-4 h-4" />
              Saved Library
            </button>

            <button
              onClick={handleOpenOnboarding}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-[#10a37f] dark:hover:text-[#10a37f] transition-colors flex items-center gap-2"
              disabled={isLoadingOnboarding}
            >
              <Sparkles className="w-4 h-4" />
              {isLoadingOnboarding ? 'Loading...' : 'Personalization Settings'}
            </button>

            <button
              onClick={handleLogout}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-[#10a37f] dark:hover:text-[#10a37f] transition-colors"
            >
              Sign out
            </button>
          </div>
        )}
      </div>

      <OnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        initialData={onboardingData}
        onComplete={() => {
          setIsOnboardingOpen(false);
          // Optional: Show success toast or refresh data
        }}
      />

      <PersonalizationLibraryModal
        isOpen={isLibraryOpen}
        onClose={() => setIsLibraryOpen(false)}
      />
    </>
  );
};

// Minimal version for mobile/small screens
export const MinimalUserProfile: React.FC<UserProfileProps> = ({ className = '' }) => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <img
        src={user.image_url || `https://ui-avatars.com/api/?name=${user.name}&background=random`}
        alt={user.name}
        className="w-8 h-8 rounded-full"
        title={user.name}
      />
      <button
        onClick={logout}
        className="text-xs text-gray-500 dark:text-gray-400 hover:text-[#10a37f] dark:hover:text-[#10a37f] transition-colors"
        title="Sign out"
      >
        Sign out
      </button>
    </div>
  );
};
