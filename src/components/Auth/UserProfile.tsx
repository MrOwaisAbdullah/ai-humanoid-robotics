import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface UserProfileProps {
  className?: string;
}

export const UserProfile: React.FC<UserProfileProps> = ({ className = '' }) => {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    setIsDropdownOpen(false);
  };

  if (!user) return null;

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center gap-2 text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 transition-colors"
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
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50">
          <div className="px-4 py-2 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-900">{user.name}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
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
        className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
        title="Sign out"
      >
        Sign out
      </button>
    </div>
  );
};