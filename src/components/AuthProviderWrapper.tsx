import React from 'react';
import { AuthProvider } from '../context/AuthContext';

interface AuthProviderWrapperProps {
  children: React.ReactNode;
}

export const AuthProviderWrapper: React.FC<AuthProviderWrapperProps> = ({ children }) => {
  return <AuthProvider>{children}</AuthProvider>;
};