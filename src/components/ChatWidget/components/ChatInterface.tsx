import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage as ChatMessageType } from '../types';
import WelcomeScreen from './WelcomeScreen';
import MessageBubble from './MessageBubble';
import InputArea from './InputArea';
import ThinkingIndicator from './ThinkingIndicator';
import { getOptimizedMotionProps, widgetVariants } from '../utils/animations';
import styles from '../styles/ChatWidget.module.css';
import { useAuth } from '../../../context/AuthContext';
import { AuthenticationBanner, AnonymousLimitBanner } from '../../../components/Auth/AuthenticationBanner';
import { useChatActions } from '../contexts/index';

interface ChatInterfaceProps {
  messages: ChatMessageType[];
  onSendMessage: (content: string) => void;
  onClose: () => void;
  isThinking: boolean;
  error: {
    error: Error | null;
    isVisible: boolean;
    canRetry: boolean;
    retryCount: number;
  };
  onRetry?: () => void;
  onDismissError?: () => void;
  migrationMessage?: string | null;
}

// Error display component
function ErrorDisplay({ error, onRetry, onDismiss }: {
  error: Error;
  onRetry?: () => void;
  onDismiss?: () => void;
}) {
  return (
    <motion.div
      className={styles.errorState}
      initial={{ opacity: 0, scale: 0.9, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: -10 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <motion.svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        animate={{ rotate: [0, 10, -10, 0] }}
        transition={{ duration: 0.5, repeat: 2, repeatDelay: 1 }}
      >
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </motion.svg>
      <span>{error.message}</span>
      {onRetry && (
        <motion.button
          className={styles.retryButton}
          onClick={onRetry}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          transition={{ duration: 0.1 }}
        >
          Try Again
        </motion.button>
      )}
      {onDismiss && (
        <motion.button
          className={styles.closeButton}
          onClick={onDismiss}
          whileHover={{ scale: 1.1, rotate: 90 }}
          whileTap={{ scale: 0.9 }}
          transition={{ duration: 0.1 }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </motion.button>
      )}
    </motion.div>
  );
}

// Main ChatInterface component
export default function ChatInterface({
  messages,
  onSendMessage,
  onClose,
  isThinking,
  error,
  onRetry,
  onDismissError,
  migrationMessage,
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isAuthenticated } = useAuth();
  const { updateMessage } = useChatActions();
  const [showLimitBanner, setShowLimitBanner] = useState(false);
  const [messageCount, setMessageCount] = useState(0);
  const [showMigrationMessage, setShowMigrationMessage] = useState(false);

  // Auto-scroll to bottom when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Track message count for anonymous users
  useEffect(() => {
    const userMessages = messages.filter(m => m.role === 'user').length;
    setMessageCount(userMessages);
    setShowLimitBanner(userMessages >= 2); // Show banner at 2 messages (limit is 3)
  }, [messages]);

  // Show migration message when provided
  useEffect(() => {
    if (migrationMessage) {
      setShowMigrationMessage(true);
      // Auto-hide after 5 seconds
      const timer = setTimeout(() => {
        setShowMigrationMessage(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [migrationMessage]);

  return (
    <motion.div
      {...getOptimizedMotionProps(widgetVariants)}
      className={styles.widget}
      initial="hidden"
      animate="visible"
      exit="exit"
    >
      {/* Header */}
      <motion.div
        className={styles.header}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <motion.h2
          className={styles.title}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
        >
          Chat With Book
        </motion.h2>
        {!isAuthenticated && (
          <motion.span
            className="text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded-full"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            {messageCount}/3 messages
          </motion.span>
        )}
        <motion.button
          onClick={onClose}
          className={styles.closeButton}
          aria-label="Close chat dialog (Escape)"
          title="Close chat dialog (Escape)"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
          whileHover={{ scale: 1.1, rotate: 90 }}
          whileTap={{ scale: 0.9 }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </motion.button>
      </motion.div>

      {/* Message Container */}
      <motion.div
        className={styles.messageContainer}
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
        aria-relevant="additions text"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.3 }}
      >
        {messages.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            {/* Show authentication banner for anonymous users */}
            {!isAuthenticated && <AuthenticationBanner />}
            <WelcomeScreen onSuggestionClick={onSendMessage} />
          </motion.div>
        ) : (
          <>
            {messages.map((message, index) => {
              // Hide empty streaming messages (show thinking indicator instead)
              if (message.isStreaming && !message.content) return null;
              
              return (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isStreaming={message.isStreaming}
                  onUpdateMessage={(messageId, newContent) => {
                    // Update message in the chat context
                    updateMessage(messageId, newContent);
                  }}
                />
              );
            })}
          </>
        )}

        {/* Thinking indicator - show when explicitly thinking OR when we have a hidden empty streaming message */}
        <AnimatePresence>
          {(isThinking || messages.some(m => m.isStreaming && !m.content)) && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <ThinkingIndicator />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Migration success message */}
        <AnimatePresence>
          {showMigrationMessage && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -10 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className={styles.successMessage}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 6L9 17l-5-5"/>
              </svg>
              <span>{migrationMessage}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error display */}
        <AnimatePresence>
          {error.isVisible && error.error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
            >
              <ErrorDisplay
                error={error.error}
                onRetry={error.canRetry ? onRetry : undefined}
                onDismiss={onDismissError}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Auto-scroll anchor */}
        <div ref={messagesEndRef} />
      </motion.div>

      {/* Anonymous user limit banner */}
      <AnimatePresence>
        {showLimitBanner && !isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -10 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <AnonymousLimitBanner messageCount={messageCount} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <InputArea
        onSendMessage={onSendMessage}
        disabled={isThinking || (!isAuthenticated && messageCount >= 3)}
      />
    </motion.div>
  );
}