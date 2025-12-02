import React, { useState } from 'react';
import ChatButton from './ChatButton';
import ChatPanel from './ChatPanel';
import { useChatState } from './hooks/useChatState';
import { useTextSelection } from './hooks/useTextSelection';

/**
 * Main ChatWidget component
 * Drop-in chatbot widget for Docusaurus sites
 *
 * Usage:
 *   <ChatWidget
 *     apiBaseUrl="https://your-api.com"
 *   />
 *
 * Customization:
 *   - Update API_BASE_URL in utils/api.ts
 *   - Adjust position prop
 *   - Customize Tailwind classes in child components
 */
export default function ChatWidget({
  apiBaseUrl = 'http://localhost:8000',
  position = 'bottom-right'
}: {
  apiBaseUrl?: string;
  position?: 'bottom-right' | 'bottom-left';
}) {
  const [isOpen, setIsOpen] = useState(false);
  const { messages, isLoading, error, sendMessage, clearError } = useChatState(apiBaseUrl);
  const { selectedText, clearSelection } = useTextSelection();

  const handleSendMessage = async (message: string) => {
    if (selectedText) {
      await sendMessage(message, selectedText);
      clearSelection();
    } else {
      await sendMessage(message);
    }
  };

  return (
    <>
      {!isOpen && (
        <ChatButton
          onClick={() => setIsOpen(true)}
          hasSelection={!!selectedText}
          position={position}
        />
      )}

      {isOpen && (
        <ChatPanel
          messages={messages}
          isLoading={isLoading}
          error={error}
          selectedText={selectedText}
          onClose={() => setIsOpen(false)}
          onSendMessage={handleSendMessage}
          onClearError={clearError}
          onClearSelection={clearSelection}
        />
      )}
    </>
  );
}