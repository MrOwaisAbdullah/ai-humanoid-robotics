import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../../contexts/AuthContext';
import { apiRequest } from '../../../services/api';
import styles from '../styles/ChatWidget.module.css';

interface MessageEditProps {
  messageId: string;
  initialContent: string;
  onSave: (newContent: string) => void;
  onCancel: () => void;
  createdAt: string;
}

interface EditHistory {
  version: number;
  content: string;
  created_at: string;
  is_current: boolean;
}

export const MessageEdit: React.FC<MessageEditProps> = ({
  messageId,
  initialContent,
  onSave,
  onCancel,
  createdAt
}) => {
  const [content, setContent] = useState(initialContent);
  const [editReason, setEditReason] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [editHistory, setEditHistory] = useState<EditHistory[]>([]);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { isAuthenticated } = useAuth();

  // Check if message is editable (within 15 minutes)
  const isEditable = () => {
    const created = new Date(createdAt);
    const now = new Date();
    const diffInMinutes = (now.getTime() - created.getTime()) / (1000 * 60);
    return diffInMinutes < 15;
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [content]);

  // Load edit history
  const loadEditHistory = async () => {
    if (!isAuthenticated) return;

    try {
      const response = await apiRequest.get(`/api/chat/messages/${messageId}/versions`);
      if (response.versions) {
        setEditHistory(response.versions);
      }
    } catch (error) {
      console.error('Failed to load edit history:', error);
    }
  };

  // Handle save
  const handleSave = async () => {
    if (!content.trim()) {
      setError('Message cannot be empty');
      return;
    }

    if (!isEditable()) {
      setError('Messages can only be edited within 15 minutes of sending');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const response = await apiRequest.put(`/api/chat/messages/${messageId}/edit`, {
        content: content.trim(),
        reason: editReason.trim() || undefined
      });

      if (response.success) {
        onSave(content.trim());
      } else {
        setError(response.error || 'Failed to save edit');
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save edit');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle key press
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel();
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSave();
    }
  };

  // Restore version
  const restoreVersion = (version: EditHistory) => {
    setContent(version.content);
  };

  // Calculate time remaining for editing
  const getTimeRemaining = () => {
    const created = new Date(createdAt);
    const now = new Date();
    const diffInMinutes = 15 - (now.getTime() - created.getTime()) / (1000 * 60);

    if (diffInMinutes <= 0) return 'Expired';

    const minutes = Math.floor(diffInMinutes);
    const seconds = Math.floor((diffInMinutes - minutes) * 60);

    if (minutes > 0) {
      return `${minutes}m ${seconds}s remaining`;
    }
    return `${seconds}s remaining`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={styles.messageEdit}
    >
      {/* Edit Time Warning */}
      <div className={styles.editTimeWarning}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        <span>{getTimeRemaining()}</span>
      </div>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={styles.errorMessage}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Edit Area */}
      <div className={styles.editMain}>
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Edit your message..."
          className={styles.editTextarea}
          disabled={!isEditable() || isSaving}
        />

        {/* Edit Reason */}
        <input
          type="text"
          value={editReason}
          onChange={(e) => setEditReason(e.target.value)}
          placeholder="Reason for editing (optional)"
          className={styles.editReason}
          disabled={!isEditable() || isSaving}
        />
      </div>

      {/* Action Buttons */}
      <div className={styles.editActions}>
        <button
          onClick={onCancel}
          disabled={isSaving}
          className={styles.cancelButton}
        >
          Cancel
        </button>

        <div className={styles.rightActions}>
          {isAuthenticated && editHistory.length > 0 && (
            <button
              onClick={() => {
                if (showHistory) {
                  setShowHistory(false);
                } else {
                  loadEditHistory();
                  setShowHistory(true);
                }
              }}
              className={styles.historyButton}
              disabled={isSaving}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="1 4 1 10 7 7"/>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                <path d="M20.49 9A9 9 0 0 0 9.35 1.37L13 7"/>
              </svg>
              History
            </button>
          )}

          <button
            onClick={handleSave}
            disabled={!isEditable() || isSaving || !content.trim()}
            className={styles.saveButton}
          >
            {isSaving ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={styles.spinner}>
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                Saving...
              </>
            ) : (
              <>
                Save (Ctrl+Enter)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Edit History */}
      <AnimatePresence>
        {showHistory && editHistory.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className={styles.editHistory}
          >
            <h4>Edit History</h4>
            <div className={styles.versionList}>
              {editHistory.map((version) => (
                <div
                  key={version.version}
                  className={`${styles.versionItem} ${
                    version.is_current ? styles.currentVersion : ''
                  }`}
                  onClick={() => !version.is_current && restoreVersion(version)}
                >
                  <div className={styles.versionInfo}>
                    <span className={styles.versionNumber}>
                      Version {version.version}
                      {version.is_current && ' (Current)'}
                    </span>
                    <span className={styles.versionDate}>
                      {new Date(version.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className={styles.versionContent}>
                    {version.content.length > 100
                      ? version.content.substring(0, 100) + '...'
                      : version.content}
                  </div>
                  {version.edit_reason && (
                    <div className={styles.versionReason}>
                      Reason: {version.edit_reason}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};