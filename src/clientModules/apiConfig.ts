/**
 * Client module for configuring API base URL
 * This runs on the client side before the app initializes
 */

// Set up API base URL
// Detects environment and uses appropriate backend URL
function setupAPIConfig() {
  let API_BASE_URL = 'http://localhost:7860'; // Default for local development

  // Check if running on GitHub Pages
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    if (hostname.includes('github.io')) {
      // Production: GitHub Pages -> HuggingFace Spaces
      API_BASE_URL = 'https://mrowaisabdullah-ai-humanoid-robotics.hf.space';
    } else if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // Local development
      API_BASE_URL = 'http://localhost:7860';
    }
  }

  // Inject into window object for access from auth-api.ts
  (window as any).__API_BASE_URL__ = API_BASE_URL;

  // Debug: Log the configured API URL (remove in production)
  if (typeof window !== 'undefined') {
    console.log('🔧 API Base URL configured:', API_BASE_URL);
  }
}

// Only run on client side (browser), not during SSR build
if (typeof window !== 'undefined') {
  setupAPIConfig();
}

// Export empty object as required by Docusaurus client modules
export default {};
