/**
 * API Configuration
 * Central configuration for API endpoints and base URL
 */

// Determine API base URL based on environment
const getApiBaseUrl = (): string => {
  // Check if we're in the browser
  if (typeof window !== 'undefined') {
    // For local development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:7860';
    }
    // For production/preview deployments
    return process.env.REACT_APP_API_URL || window.location.origin;
  }

  // For server-side rendering (if applicable)
  return process.env.REACT_APP_API_URL || 'http://localhost:7860';
};

export const API_BASE_URL = getApiBaseUrl();

// Export the function as well for any components that need to determine it dynamically
export { getApiBaseUrl };