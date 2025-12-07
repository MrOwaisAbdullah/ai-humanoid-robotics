import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LoginButton } from './LoginButton';
import { UserProfile } from './UserProfile';

export const NavbarAuth: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [container, setContainer] = useState<Element | null>(null);

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
        <UserProfile />
      ) : (
        <LoginButton />
      )}
    </div>,
    container
  );
};
