/**
 * Client module for configuring API base URL
 * This runs on the client side before the app initializes
 */

// Set up API base URL
// For local development, this connects to localhost:7860
// For production (GitHub Pages), update the URL below to your deployed backend
function setupAPIConfig() {
  const API_BASE_URL = 'http://localhost:7860';

  // Inject into window object for access from auth-api.ts
  (window as any).__API_BASE_URL__ = API_BASE_URL;
}

// Run the setup immediately
setupAPIConfig();

// Export empty object as required by Docusaurus client modules
export default {};
