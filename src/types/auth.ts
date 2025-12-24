/**
 * TypeScript type definitions for authentication-related data structures.
 */

// User types
export interface User {
  id: string;
  email: string;
  name?: string;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
}

// Authentication request/response types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// User background types
export interface UserBackground {
  id: string;
  user_id: string;
  experience_level: 'beginner' | 'intermediate' | 'advanced';
  years_experience: number;
  preferred_languages: string[];
  hardware_expertise: {
    cpu: 'none' | 'basic' | 'intermediate' | 'advanced';
    gpu: 'none' | 'basic' | 'intermediate' | 'advanced';
    networking: 'none' | 'basic' | 'intermediate' | 'advanced';
  };
  created_at: string;
  updated_at: string;
}

// Onboarding response types
export interface OnboardingResponse {
  id: string;
  user_id: string;
  question_key: string;
  response_value: any;
  created_at: string;
}

// User preferences types
export interface UserPreferences {
  id: string;
  user_id: string;
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notification_settings: {
    email_responses: boolean;
    browser_notifications: boolean;
    marketing_emails: boolean;
  };
  created_at: string;
  updated_at: string;
}

// Chat session types
export interface ChatSession {
  id: string;
  user_id?: string;
  anonymous_session_id?: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  chat_session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    personalized_for?: string;
    sources?: string[];
    confidence?: number;
  };
  created_at: string;
}

// Form types for onboarding
export interface OnboardingFormData {
  experience_level: 'beginner' | 'intermediate' | 'advanced';
  years_experience: number;
  preferred_languages: string[];
  cpu_expertise: 'none' | 'basic' | 'intermediate' | 'advanced';
  gpu_expertise: 'none' | 'basic' | 'intermediate' | 'advanced';
  networking_expertise: 'none' | 'basic' | 'intermediate' | 'advanced';
}

// API error types
export interface ApiError {
  detail: string;
  error?: string;
  field?: string;
}

// Password reset types
export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
}

// Session types
export interface Session {
  id: string;
  user_id: string;
  expires_at: string;
  created_at: string;
  ip_address?: string;
  user_agent?: string;
}

// Anonymous session types
export interface AnonymousSession {
  id: string;
  message_count: number;
  created_at: string;
  last_activity: string;
}

// Form validation schemas
export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  email: string;
  password: string;
  confirm_password: string;
  name?: string;
}

export interface ForgotPasswordFormData {
  email: string;
}

export interface ResetPasswordFormData {
  new_password: string;
  confirm_password: string;
}

// Settings form data
export interface SettingsFormData {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  email_responses: boolean;
  browser_notifications: boolean;
  marketing_emails: boolean;
  chat_model?: string;
  chat_temperature?: number;
}

// Chat personalization
export interface PersonalizationContext {
  user_background?: UserBackground;
  experience_level?: 'beginner' | 'intermediate' | 'advanced';
  preferred_languages?: string[];
  hardware_familiarity?: {
    cpu: string;
    gpu: string;
    networking: string;
  };
}

// Rate limiting info
export interface RateLimitInfo {
  remaining: number;
  reset: number;
  limit: number;
}

// Authentication context types (re-export from AuthContext)
export type { AuthState, AuthContextValue } from '../context/AuthContext';