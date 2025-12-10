import React, { useCallback, useEffect, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import ChatButton from './ChatButton';
import SelectionTooltip from './components/SelectionTooltip';
import { useTextSelection } from './hooks/useTextSelection';
import { ChatProvider, useChat, useChatSelector } from './contexts/index';
import { ChatWidgetContainerProps, ChatMessage } from './types';
import { formatChatRequest, APIError } from './utils/api';
import { withPerformanceMonitoring, usePerformanceMonitor } from './utils/performanceMonitor';
import { useAuth } from '../../contexts/AuthContext';
import { sessionStorage } from '../../utils/sessionStorage';

interface ChatWidgetContainerInnerProps extends ChatWidgetContainerProps {
  apiUrl?: string;
  maxTextSelectionLength?: number;
  fallbackTextLength?: number;
}

/**
 * Inner component that uses chat context
 * Separated to allow provider wrapper
 */
function ChatWidgetContainerInner({
  apiUrl = '/api/chat/send',
  maxTextSelectionLength = 2000,
  fallbackTextLength = 5000,
}: ChatWidgetContainerInnerProps) {
  // Use consolidated state management - get all needed methods directly
  const chatContext = useChat();

  // Use auth context to get authentication state
  const { isAuthenticated } = useAuth();

  // Ref for anonymous session ID
  const anonymousSessionIdRef = useRef<string | null>(null);

  // Performance monitoring
  const { renderCount } = usePerformanceMonitor('ChatWidgetContainer');

  // Refs for stable references (prevents re-renders)
  const streamingAbortControllerRef = useRef<AbortController | null>(null);
  const lastMessageRef = useRef<string>('');

  // Selector hooks to prevent unnecessary re-renders
  const isOpen = useChatSelector(s => s.isOpen);
  const messages = useChatSelector(s => s.messages);
  const isThinking = useChatSelector(s => s.isThinking);
  const currentStreamingId = useChatSelector(s => s.currentStreamingId);
  const error = useChatSelector(s => s.error);

  // Transform error to match expected interface
  const errorState = {
    error: error,
    isVisible: !!error,
    canRetry: true,
    retryCount: 0
  };

  // Text selection for "Ask AI" functionality
  const { selection, isTooltipVisible, clearSelection, setIsTooltipVisible } = useTextSelection({
    maxLength: maxTextSelectionLength || 2000,
    enabled: true
  });

  /**
   * Handle streaming data chunk
   * Uses updater function to avoid dependencies on state
   */
  const handleChunk = useCallback((chunk: string) => {
    // Use the action directly from context - no state dependencies needed
    if (chatContext.updateStreaming) {
      chatContext.updateStreaming(chunk);
    } else {
      console.error('updateStreaming is not available in chat context', chatContext);
    }
  }, [chatContext.updateStreaming]);

  /**
   * Handle streaming completion
   */
  const handleComplete = useCallback(() => {
    // Clean up streaming state
    if (chatContext.completeStreaming) {
      chatContext.completeStreaming();
    }

    // Abort any ongoing requests
    if (streamingAbortControllerRef.current) {
      streamingAbortControllerRef.current.abort();
      streamingAbortControllerRef.current = null;
    }
  }, [chatContext.completeStreaming]);

  /**
   * Handle streaming errors
   */
  const handleError = useCallback((error: Error) => {
    console.error('Streaming error:', error);

    // Set streaming error state
    if (chatContext.setStreamingError) {
      chatContext.setStreamingError(error);
    }

    // Clean up
    handleComplete();
  }, [chatContext.setStreamingError, handleComplete]);

  /**
   * Send a message to the AI
   * Consolidates the previous sendStreamingMessage and startStreaming logic
   */
  const handleSendMessage = useCallback(async (content: string) => {
    try {
      // Prevent duplicate messages
      if (content.trim() === lastMessageRef.current.trim()) {
        console.warn('Duplicate message detected:', content);
        return;
      }
      lastMessageRef.current = content;

      // Clear any previous errors
      if (chatContext.clearError) {
        chatContext.clearError();
      }

      // Add user message
      if (!chatContext.addMessage) {
        throw new Error('addMessage is not available');
      }
      chatContext.addMessage({
        content: content.trim(),
        role: 'user'
      });

      // Set thinking state
      if (chatContext.setIsThinking) {
        chatContext.setIsThinking(true);
      }

      // Create AI message placeholder
      if (!chatContext.addMessage || !chatContext.startStreaming) {
        throw new Error('Required chat methods are not available');
      }
      const aiMessageId = chatContext.addMessage({
        content: '',
        role: 'assistant',
        isStreaming: true
      });

      // Start streaming for this message
      chatContext.startStreaming(aiMessageId);

      // Create abort controller for this request
      const abortController = new AbortController();
      streamingAbortControllerRef.current = abortController;

      // Generate or get session ID
      const sessionId = Math.random().toString(36).substring(7) + Date.now().toString(36);

      // Send request to API
      const request = formatChatRequest(content);

      // Add session ID to request
      request.session_id = sessionId;

      // Prepare headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      // Add anonymous session header if not authenticated
      if (!isAuthenticated && anonymousSessionIdRef.current) {
        headers['X-Anonymous-Session-ID'] = anonymousSessionIdRef.current;
      }

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
        signal: abortController.signal,
        credentials: 'include', // Include cookies for auth
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
      }

      // Handle JSON response (our new API returns complete responses, not streams)
      const responseData = await response.json();

      // Extract messages from the response
      if (responseData.messages && Array.isArray(responseData.messages)) {
        // Find the assistant's response
        const assistantMessage = responseData.messages.find((msg: any) => msg.role === 'assistant');
        if (assistantMessage && assistantMessage.content) {
          handleChunk(assistantMessage.content);
        }
      } else if (responseData.answer) {
        // Direct answer format
        handleChunk(responseData.answer);
      } else if (responseData.content) {
        // Alternative content format
        handleChunk(responseData.content);
      } else {
        // Fallback
        handleChunk('I received your message but couldn\'t generate a response.');
      }

      // Complete streaming
      handleComplete();

    } catch (error) {
      // Handle abort specially
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Streaming aborted');
        return;
      }

      handleError(error instanceof Error ? error : new Error('Failed to send message'));
    }
  }, [
    chatContext,
    apiUrl,
    handleChunk,
    handleComplete,
    handleError
  ]);

  /**
   * Retry the last failed message
   */
  const handleRetry = useCallback(() => {
    // Find the last user message and resend
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const lastUserMessage = userMessages[userMessages.length - 1];
      handleSendMessage(lastUserMessage.content);
    }
  }, [messages, handleSendMessage]);

  /**
   * Clear error state
   */
  const handleDismissError = useCallback(() => {
    if (chatContext.clearError) {
      chatContext.clearError();
    }
  }, [chatContext.clearError]);

  /**
   * Close the widget
   */
  const handleClose = useCallback(() => {
    // Abort any ongoing streaming
    if (streamingAbortControllerRef.current) {
      streamingAbortControllerRef.current.abort();
      streamingAbortControllerRef.current = null;
    }

    // Close widget
    if (chatContext.setIsOpen) {
      chatContext.setIsOpen(false);
    }
  }, [chatContext.setIsOpen]);

  /**
   * Toggle the widget open/closed
   */
  const handleToggle = useCallback(() => {
    if (chatContext.setIsOpen) {
      if (isOpen) {
        handleClose();
      } else {
        chatContext.setIsOpen(true);
      }
    }
  }, [isOpen, chatContext.setIsOpen, handleClose]);

  /**
   * Handle "Ask AI" from text selection
   */
  const handleAskAI = useCallback((selectedText: string) => {
    // Open widget if it's closed
    if (!isOpen && chatContext.setIsOpen) {
      chatContext.setIsOpen(true);
    }

    // Create contextual prompt
    const contextualPrompt = `I have a question about this selected text: "${selectedText}"`;

    // Send the message with context (add a small delay to ensure widget is open)
    setTimeout(() => {
      handleSendMessage(contextualPrompt);
    }, 300);
  }, [isOpen, chatContext.setIsOpen, handleSendMessage]);

  
  /**
   * Initialize anonymous session on mount
   */
  useEffect(() => {
    // Only initialize if not authenticated
    if (!isAuthenticated) {
      const initializeAnonymousSession = async () => {
        try {
          // Get or create session ID with fallback
          const sessionResult = sessionStorage.getOrCreateSessionId();

          // Store session ID in ref for use in messages
          anonymousSessionIdRef.current = sessionResult.id;

          // Fetch session data from backend to get current message count
          const response = await fetch(`/api/auth/anonymous-session/${sessionResult.id}`);

          if (response.ok) {
            const sessionData = await response.json();

            // Update chat context with message count if needed
            if (chatContext.setMessageCount && sessionData.message_count > 0) {
              chatContext.setMessageCount(sessionData.message_count);
            }

            console.log('Anonymous session initialized:', {
              sessionId: sessionData.id,
              messageCount: sessionData.message_count,
              existed: sessionData.exists,
              source: sessionResult.source
            });
          } else {
            // Session fetch failed, but we can continue with a new session
            console.warn('Failed to fetch anonymous session data, creating new session');
            // Set default message count for new session
            if (chatContext.setMessageCount) {
              chatContext.setMessageCount(0);
            }
          }
        } catch (error) {
          console.error('Error initializing anonymous session:', error);
          // Continue with default values even if session initialization fails
          if (chatContext.setMessageCount) {
            chatContext.setMessageCount(0);
          }
          // Log additional error details for debugging
          if (error instanceof Error) {
            console.error('Session initialization error details:', {
              name: error.name,
              message: error.message,
              stack: error.stack
            });
          }
        }
      };

      initializeAnonymousSession();
    }
  }, [isAuthenticated, chatContext.setMessageCount]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (streamingAbortControllerRef.current) {
        streamingAbortControllerRef.current.abort();
      }
    };
  }, []);

  // Log render info in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`ChatWidgetContainer render #${renderCount}`, {
      messagesCount: messages.length,
      isOpen,
      isThinking,
      streamingId: currentStreamingId,
      hasError: !!error
    });
  }

  // Always render the button, conditionally render the interface
  return React.createElement(
    React.Fragment,
    null,
    // Floating toggle button
    React.createElement(ChatButton, {
      onClick: handleToggle,
      position: 'bottom-right',
      hasSelection: selection.isValid && selection.text.length > 0
    }),
    // Chat interface wrapper with proper z-index (only when open)
    isOpen && React.createElement(
      'div',
      {
        style: {
          position: 'fixed',
          bottom: '100px',
          right: '20px',
          zIndex: 9999,
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
        }
      },
      React.createElement(ChatInterface, {
        messages: messages,
        onSendMessage: handleSendMessage,
        onClose: handleClose,
        isThinking: isThinking,
        error: errorState,
        onRetry: handleRetry,
        onDismissError: handleDismissError,
        migrationMessage: null // TODO: Pass migration message from auth context
      })
    ),
    // Selection tooltip for "Ask AI" functionality
    React.createElement(
      'span',
      null,
      React.createElement(SelectionTooltip, {
        rect: selection.rect,
        isTooLong: selection.isTooLong,
        truncatedText: selection.truncatedText,
        fullText: selection.text,
        onAskAI: handleAskAI,
        onClose: clearSelection,
        isVisible: isTooltipVisible
      })
    )
  );
}

/**
 * ChatWidgetContainer with provider and performance monitoring
 */
export default function ChatWidgetContainer(props: ChatWidgetContainerProps) {
  return React.createElement(
    ChatProvider,
    null,
    React.createElement(ChatWidgetContainerInner, props)
  );
}

// Export with performance monitoring for development
export const ChatWidgetContainerWithMonitoring = withPerformanceMonitoring(
  ChatWidgetContainer,
  'ChatWidgetContainer'
);