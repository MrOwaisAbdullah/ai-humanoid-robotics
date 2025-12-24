import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../../context/AuthContext';
import { LoginButton } from './LoginButton';
import { UserProfile } from './UserProfile';
import { PersonalizationLibraryModal } from '../Personalization/PersonalizationLibraryModal';
import { BookOpen } from 'lucide-react';

export const NavbarAuth: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [container, setContainer] = useState<Element | null>(null);
  const [isLibraryOpen, setIsLibraryOpen] = useState(false);

  useEffect(() => {
    // Find the right-side navbar container
    // We use a polling mechanism because the navbar might mount slightly after Root
    const interval = setInterval(() => {
      const target = document.querySelector('.navbar__items--right');
      if (target) {
        setContainer(target);
        clearInterval(interval);
      }
    }, 100);

    // Stop polling after 5 seconds to avoid infinite loops
    const timeout = setTimeout(() => clearInterval(interval), 5000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, []);

  if (!container) return null;

  return createPortal(
    <div className="flex items-center gap-2 pl-4">
      {isAuthenticated ? (
        <>
          <button
            onClick={() => setIsLibraryOpen(true)}
            className="hidden md:flex items-center justify-center p-2 text-gray-500 hover:text-[#10a37f] dark:text-gray-400 dark:hover:text-[#10a37f] transition-colors rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
            title="Saved Library"
          >
            <BookOpen className="w-5 h-5" />
          </button>
          <UserProfile />
          <PersonalizationLibraryModal
            isOpen={isLibraryOpen}
            onClose={() => setIsLibraryOpen(false)}
          />
        </>
      ) : (
        <LoginButton />
      )}
    </div>,
    container
  );
};
