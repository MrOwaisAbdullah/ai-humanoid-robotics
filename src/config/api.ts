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
      return 'http://localhost:7860'; // Backend runs on port 7860
    }
    // For production/preview deployments on GitHub Pages
    if (window.location.hostname.includes('github.io')) {
      // Use the deployed backend URL
      return 'https://mrowaisabdullah-ai-humanoid-robotics.hf.space';
    }
    // For other environments (HuggingFace Spaces, etc.)
    return window.location.origin;
  }

  // Default for server-side rendering (if applicable)
  // Note: This won't be used in browser builds
  return 'http://localhost:7860'; // Backend runs on port 7860
};

export const API_BASE_URL = getApiBaseUrl();

// Export the function as well for any components that need to determine it dynamically
export { getApiBaseUrl };