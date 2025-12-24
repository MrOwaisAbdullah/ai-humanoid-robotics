// Authentication types matching the Better Auth v1.4.x implementation

export interface User {
  id: string;
  email: string;
  name: string;
  emailVerified: boolean;
  emailVerifiedAt?: string;
  image?: string;
  role: 'user' | 'admin';
  createdAt: string;
  updatedAt: string;
  preferences?: UserPreferences;
  profileDescription?: string;
}

export interface UserPreferences {
  id: string;
  userId: string;
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  profileDescription?: string;
  notificationPreferences: {
    emailNotifications: boolean;
    chatReminders: boolean;
    featureUpdates: boolean;
    securityAlerts: boolean;
  };
  chatSettings: {
    modelPreference: string;
    temperature: number;
    maxTokens: number;
    saveHistory: boolean;
    showSources: boolean;
  };
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  success: boolean;
  user?: User;
  token?: string;
  refreshToken?: string;
  expiresAt?: string;
  error?: string;
  message?: string;
  data?: any;
}

export interface CreateUserData {
  email: string;
  name: string;
  password: string;
  confirmPassword: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface UpdateProfileData {
  name?: string;
  timezone?: string;
  language?: string;
  profileDescription?: string;
  preferences?: Partial<UserPreferences['notificationPreferences']> &
                     Partial<UserPreferences['chatSettings']>;
}

export interface PasswordResetData {
  email: string;
}

export interface ConfirmPasswordResetData {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface Session {
  id: string;
  userId: string;
  token: string;
  expiresAt: string;
  createdAt: string;
  userAgent?: string;
  ipAddress?: string;
  active: boolean;
}

export interface VerificationToken {
  id: string;
  identifier: string;
  token: string;
  expiresAt: string;
  createdAt: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<AuthResponse>;
  register: (data: CreateUserData) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  refreshAuthToken: () => Promise<void>;
  updateProfile: (data: UpdateProfileData) => Promise<AuthResponse>;
  requestPasswordReset: (data: PasswordResetData) => Promise<AuthResponse>;
  confirmPasswordReset: (data: ConfirmPasswordResetData) => Promise<AuthResponse>;
  verifyEmail: (token: string) => Promise<AuthResponse>;
  resendVerificationEmail: (email: string) => Promise<AuthResponse>;
}

// Legacy compatibility exports
export type LoginRequest = LoginData;
export type RegisterRequest = CreateUserData;