import React from 'react';
import type { RootProps } from '@docusaurus/types';
import CustomChatKitWidget from '../components/ChatWidget/CustomChatKitWidget';

export default function Root({children}: RootProps): React.JSX.Element {
  // Get the ChatKit endpoint from environment variables
  // Use local development URL for localhost, deployed URL for production
  const getChatkitEndpoint = () => {
    // Check for environment variable first
    if (typeof process !== 'undefined' && process.env?.REACT_APP_CHAT_API_URL) {
      return process.env.REACT_APP_CHAT_API_URL;
    }

    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:7860/chat';
    }

    // For production, use the HuggingFace Spaces URL from environment or default
    // This should be configured during build/deployment
    return 'https://mrowaisabdullah-ai-humanoid-robotics.hf.space/chat';
  };

  return (
    <>
      {children}
      <CustomChatKitWidget
        apiEndpoint={getChatkitEndpoint()}
        title="Physical AI & Robotics Assistant"
      />
    </>
  );
}