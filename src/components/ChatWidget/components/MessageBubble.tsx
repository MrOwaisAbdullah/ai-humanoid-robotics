import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage } from '../types';
import MessageRenderer from './MessageRenderer';
import StreamingCursor from './StreamingCursor';
import { getOptimizedMotionProps, messageEntryVariants } from '../utils/animations';
import styles from '../styles/ChatWidget.module.css';

// Helper function to safely format message content
function formatMessageContent(content: any): string {
  if (typeof content === 'string') {
    // Check if it's the literal "[object Object]"
    if (content === '[object Object]') {
      return 'Error: Invalid message format';
    }
    return content;
  }

  if (typeof content === 'object' && content !== null) {
    return JSON.stringify(content, null, 2);
  }

  return String(content || '');
}

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const showAvatar = true; // Could be made configurable

  return (
    <motion.div
      {...getOptimizedMotionProps(messageEntryVariants, undefined)}
      className={`${styles.message} ${isUser ? styles.userMessage : styles.aiMessage}`}
      role="article"
      aria-label={`${isUser ? 'Your message' : 'AI response'}: ${String(message.content || '').slice(0, 50)}...`}
    >
      {showAvatar && (
        <div className={`${styles.avatar} ${isUser ? styles.userAvatar : styles.aiAvatar}`}>
          {isUser ? (
            // User avatar - could be user's profile picture/initials
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          ) : (
            // AI avatar - could be custom AI icon
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          )}
        </div>
      )}

      <div className={styles.messageContent}>
        {/* Message bubble with distinct styling for user vs AI */}
        <div
          className={`${styles.messageBubble} ${isUser ? styles.userMessageBubble : styles.aiMessageBubble}`}
        >
          {isUser ? (
            // User messages - plain text with streaming cursor
            <div className={styles.messageText}>
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              >
                {formatMessageContent(message.content)}
              </motion.span>
              {isStreaming && (
                <StreamingCursor enabled={true} />
              )}
            </div>
          ) : (
            // AI messages - rich markdown rendering with streaming support
            <div className={styles.messageText}>
              <MessageRenderer
                content={formatMessageContent(message.content)}
                sources={message.sources}
                isStreaming={isStreaming}
              />
              {isStreaming && (
                <StreamingCursor enabled={true} />
              )}
            </div>
          )}

          {/* Read receipt or status indicator for user messages */}
          {isUser && (
            <div className={styles.messageStatus} aria-hidden="true">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
              </svg>
            </div>
          )}
        </div>

        {/* Timestamp with relative time display */}
        <div className={styles.timestamp}>
          <time
            dateTime={message.timestamp.toISOString()}
            title={message.timestamp.toLocaleString()}
          >
            {formatRelativeTime(message.timestamp)}
          </time>
        </div>
      </div>
    </motion.div>
  );
}

// Helper function to format relative time (e.g., "2 minutes ago")
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes === 1 ? '' : 's'} ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours === 1 ? '' : 's'} ago`;
  }

  // For older messages, show the actual time
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });
}

export default React.memo(MessageBubble);