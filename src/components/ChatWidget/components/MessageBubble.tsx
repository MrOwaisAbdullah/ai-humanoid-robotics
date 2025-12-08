import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage } from '../types';
import MessageRenderer from './MessageRenderer';
import StreamingCursor from './StreamingCursor';
import { MessageEdit } from './MessageEdit';
import { getOptimizedMotionProps, messageEntryVariants } from '../utils/animations';
import { useAuth } from '../../../contexts/AuthContext';
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
  onUpdateMessage?: (messageId: string, newContent: string) => void;
}

function MessageBubble({ message, isStreaming = false, onUpdateMessage }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const showAvatar = true; // Could be made configurable
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(message.content);
  const [editCount, setEditCount] = useState(message.edit_count || 0);
  const { isAuthenticated } = useAuth();

  // Check if message is editable (user message, not streaming, within time limit)
  const isEditable = () => {
    if (!isUser || isStreaming || !isAuthenticated) return false;

    const created = new Date(message.created_at);
    const now = new Date();
    const diffInMinutes = (now.getTime() - created.getTime()) / (1000 * 60);
    return diffInMinutes < 15;
  };

  // Handle edit save
  const handleEditSave = (newContent: string) => {
    setEditedContent(newContent);
    setEditCount(prev => prev + 1);
    setIsEditing(false);
    if (onUpdateMessage) {
      onUpdateMessage(message.id, newContent);
    }
  };

  // Update content when message changes
  useEffect(() => {
    if (!isEditing) {
      setEditedContent(message.content);
    }
  }, [message.content, isEditing]);

  // Check time remaining
  const getTimeRemaining = () => {
    const created = new Date(message.created_at);
    const now = new Date();
    const diffInMinutes = 15 - (now.getTime() - created.getTime()) / (1000 * 60);
    return diffInMinutes > 0 ? Math.floor(diffInMinutes) : 0;
  };

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
            // User avatar - default icon
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          ) : (
            // AI avatar - using project logo
            <img 
              src="/ai-humanoid-robotics/img/logo.png" 
              alt="AI" 
              className={styles.avatarImage}
              onError={(e) => {
                // Fallback to SVG if image fails to load
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement!.innerHTML = `
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                `;
              }}
            />
          )}
        </div>
      )}

      <div className={styles.messageContent}>
        {/* Message bubble with distinct styling for user vs AI */}
        <div
          className={`${styles.messageBubble} ${isUser ? styles.userMessageBubble : styles.aiMessageBubble}`}
        >
          <AnimatePresence mode="wait">
            {isEditing ? (
              <MessageEdit
                messageId={message.id}
                initialContent={editedContent}
                onSave={handleEditSave}
                onCancel={() => setIsEditing(false)}
                createdAt={message.created_at}
              />
            ) : (
              <div className={styles.messageText}>
                {isUser ? (
                  // User messages - plain text with edit controls
                  <>
                    <div className={styles.messageTextWrapper}>
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3, ease: "easeOut" }}
                      >
                        {formatMessageContent(editedContent)}
                      </motion.span>
                      {isStreaming && (
                        <StreamingCursor enabled={true} />
                      )}
                    </div>

                    {/* Edit indicator */}
                    {editCount > 0 && (
                      <div className={styles.editIndicator}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4-5.5z"/>
                        </svg>
                        <span>Edited {editCount} time{editCount > 1 ? 's' : ''}</span>
                      </div>
                    )}

                    {/* Edit button */}
                    {isEditable() && (
                      <motion.button
                        className={styles.editButton}
                        onClick={() => setIsEditing(true)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        title={`Edit (${getTimeRemaining()}m remaining)`}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4-5.5z"/>
                        </svg>
                      </motion.button>
                    )}
                  </>
                ) : (
                  // AI messages - rich markdown rendering with streaming support
                  <>
                    <MessageRenderer
                      content={formatMessageContent(editedContent)}
                      sources={message.sources}
                      isStreaming={isStreaming}
                    />
                    {isStreaming && (
                      <StreamingCursor enabled={true} />
                    )}
                  </>
                )}
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

export default React.memo(MessageBubble);