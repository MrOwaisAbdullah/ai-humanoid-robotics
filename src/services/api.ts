/**
 * API service with authentication interceptors.

This module configures Axios with request/response interceptors
for handling authentication tokens and error responses.
 */

import axios, { AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../config/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 80000, // 80 seconds timeout
  withCredentials: true, // Important for cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token to headers
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add token if available in cookies or localStorage
    const cookieToken = getCookie('access_token');
    const localToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const token = cookieToken || localToken;

    // Debug logging for specific endpoints
    if (config.url?.includes('/api/v1/background') || config.url?.includes('/auth/me')) {
      console.log('API Request Debug:');
      console.log('  - Cookie token:', cookieToken ? `${cookieToken.substring(0, 20)}...` : 'None');
      console.log('  - LocalStorage token:', localToken ? `${localToken.substring(0, 20)}...` : 'None');
      console.log('  - Using token:', token ? `${token.substring(0, 20)}...` : 'None');
      console.log('  - URL:', config.url);
    }

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig;

    // Handle 401 Unauthorized errors
    if (error.response?.status === 401 && originalRequest) {
      // Clear expired token
      deleteCookie('access_token');
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
      }

      // Don't retry login requests to avoid infinite loops
      if (
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/register')
      ) {
        return Promise.reject(error);
      }

      // You could implement token refresh logic here if needed
      // For now, just log it
      console.log('Authentication required for request:', originalRequest.url);
      
      // Do not redirect automatically, let the app handle the state change
      // window.location.href = '/ai-humanoid-robotics/docs/intro';
    }

    // Handle 403 Forbidden errors
    if (error.response?.status === 403) {
      console.error('Access forbidden:', error.response.data);
    }

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
      // You could implement retry logic here
    }

    return Promise.reject(error);
  }
);

// Helper functions for cookie management
const getCookie = (name: string): string | null => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null;
  }
  return null;
};

const deleteCookie = (name: string): void => {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
};

// API request methods
export const apiRequest = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    api.get<T>(url, config),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    api.post<T>(url, data, config),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    api.put<T>(url, data, config),

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    api.patch<T>(url, data, config),

  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    api.delete<T>(url, config),
};

// Export the configured axios instance
export { api };
export default api;

// Export cookie utilities for other components
export { getCookie, deleteCookie };