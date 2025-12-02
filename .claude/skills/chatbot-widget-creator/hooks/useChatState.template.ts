import { useState, useCallback } from 'react';
import { sendChatRequest, sendSelectionChatRequest } from '../utils/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

/**
 * Chat state management hook
 * Handles message history, loading, errors, and streaming
 */
export function useChatState(apiBaseUrl: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (
    userMessage: string,
    selectedText?: string
  ) => {
    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      let responseText = '';
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };

      // Add empty assistant message
      setMessages(prev => [...prev, assistantMsg]);

      // Choose endpoint
      const stream = selectedText
        ? sendSelectionChatRequest(userMessage, selectedText)
        : sendChatRequest(userMessage);

      // Stream response
      for await (const token of stream) {
        responseText += token;
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1].content = responseText;
          return updated;
        });
      }

    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to get response. Please try again.');
      setMessages(prev => prev.slice(0, -1)); // Remove empty assistant message
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl]);

  const clearError = useCallback(() => setError(null), []);

  return { messages, isLoading, error, sendMessage, clearError };
}