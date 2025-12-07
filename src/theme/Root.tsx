import React from 'react';
import type { RootProps } from '@docusaurus/types';
import CustomChatKitWidget from '../components/ChatWidget/CustomChatKitWidget';
import ChatWidgetContainer from '../components/ChatWidget/ChatWidgetContainer';

export default function Root({children}: RootProps): React.JSX.Element {
  // Get the ChatKit endpoint from environment variables
  // Use local development URL for localhost, deployed URL for production
  const getChatkitEndpoint = () => {
    // In Docusaurus, we use window location detection instead of process.env for client-side code
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:7860/api/chat';
    }

    // For production, use the HuggingFace Spaces URL
    // Environment variables can be configured during build/deployment
    return 'https://mrowaisabdullah-ai-humanoid-robotics.hf.space/api/chat';
  };

  // Default to new ChatGPT-style widget, fallback to CustomChatKitWidget
  const useNewChatWidget = true; // Can be made configurable via build-time env vars

  return (
    <>
      {children}
      {useNewChatWidget ? (
        <ChatWidgetContainer
          apiUrl={getChatkitEndpoint()}
          maxTextSelectionLength={2000}
          fallbackTextLength={5000}
        />
      ) : (
        <CustomChatKitWidget
          apiEndpoint={getChatkitEndpoint()}
          title="Physical AI & Robotics Assistant"
        />
      )}
    </>
  );
}