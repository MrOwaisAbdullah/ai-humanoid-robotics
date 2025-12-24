import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

interface EmailVerificationBannerProps {
  className?: string;
}

export const EmailVerificationBanner: React.FC<EmailVerificationBannerProps> = ({
  className = '',
}) => {
  const { user, verifyEmail, resendVerificationEmail, isLoading } = useAuth();
  const [showResendSuccess, setShowResendSuccess] = useState(false);

  // Don't show if user is not logged in or email is already verified
  if (!user || user.emailVerified) {
    return null;
  }

  const handleResendVerification = async () => {
    try {
      const response = await resendVerificationEmail(user.email);
      if (response.success) {
        setShowResendSuccess(true);
        setTimeout(() => setShowResendSuccess(false), 5000);
      }
    } catch (err) {
      console.error('Resend verification failed:', err);
    }
  };

  // Check if URL has verification token
  const handleVerifyFromUrl = () => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('token');
      if (token) {
        verifyEmail(token);
        // Clean URL
        const url = new URL(window.location.href);
        url.searchParams.delete('token');
        window.history.replaceState({}, '', url.toString());
      }
    }
  };

  // Auto-check for verification token on mount
  React.useEffect(() => {
    handleVerifyFromUrl();
  }, []);

  return (
    <div className={`bg-yellow-50 border-l-4 border-yellow-400 p-4 ${className}`}>
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-yellow-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm text-yellow-700">
            <span className="font-medium">Email verification required</span>
            <br />
            Please verify your email address to access all features. Check your inbox for the verification link.
          </p>
        </div>
      </div>
      <div className="mt-3 flex space-x-3">
        <button
          onClick={handleResendVerification}
          disabled={isLoading || showResendSuccess}
          className="text-sm font-medium text-yellow-700 hover:text-yellow-600 underline disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Sending...' : showResendSuccess ? 'Email sent!' : 'Resend verification email'}
        </button>
      </div>
    </div>
  );
};