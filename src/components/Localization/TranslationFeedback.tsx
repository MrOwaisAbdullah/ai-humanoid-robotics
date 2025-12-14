import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ThumbsUp, ThumbsDown, Send, MessageSquare, CheckCircle } from 'lucide-react';

interface TranslationFeedbackProps {
  onClose: () => void;
  onSubmit: (rating: 1 | -1, comment?: string) => Promise<void>;
}

export function TranslationFeedback({ onClose, onSubmit }: TranslationFeedbackProps) {
  const [rating, setRating] = useState<1 | -1 | null>(null);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Focus on textarea when rating is selected
  useEffect(() => {
    if (rating && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [rating]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!rating) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(rating, comment.trim() || undefined);
      setIsSubmitted(true);

      // Auto close after success
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      setIsSubmitting(false);
    }
  };

  const handleQuickFeedback = async (quickRating: 1 | -1) => {
    setRating(quickRating);
    setIsSubmitting(true);

    try {
      await onSubmit(quickRating);
      setIsSubmitted(true);

      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <motion.div
        className="feedback-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="feedback-modal success-modal"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
        >
          <div className="success-content">
            <CheckCircle size={48} className="success-icon" />
            <h3>Thank You!</h3>
            <p>Your feedback helps us improve translation quality</p>
          </div>
        </motion.div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="feedback-modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <motion.div
        className="feedback-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
      >
        <div className="feedback-header">
          <h3>Translation Feedback</h3>
          <button
            className="close-btn"
            onClick={onClose}
            aria-label="Close feedback"
          >
            <X size={20} />
          </button>
        </div>

        <div className="feedback-content">
          <p className="feedback-question">
            How is this translation?
          </p>

          <div className="rating-buttons">
            <button
              className={`rating-btn positive ${rating === 1 ? 'selected' : ''}`}
              onClick={() => setRating(1)}
              disabled={isSubmitting}
              aria-pressed={rating === 1}
            >
              <ThumbsUp size={20} />
              <span>Good</span>
            </button>

            <button
              className={`rating-btn negative ${rating === -1 ? 'selected' : ''}`}
              onClick={() => setRating(-1)}
              disabled={isSubmitting}
              aria-pressed={rating === -1}
            >
              <ThumbsDown size={20} />
              <span>Needs Improvement</span>
            </button>
          </div>

          {rating && (
            <motion.div
              className="comment-section"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <div className="comment-header">
                <MessageSquare size={16} />
                <label htmlFor="feedback-comment">
                  Add a comment (optional)
                </label>
              </div>

              <form onSubmit={handleSubmit}>
                <textarea
                  id="feedback-comment"
                  ref={textareaRef}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder={
                    rating === 1
                      ? "What did you like about this translation?"
                      : "What could be improved?"
                  }
                  rows={4}
                  maxLength={500}
                  disabled={isSubmitting}
                />

                <div className="comment-actions">
                  <span className="char-count">
                    {comment.length}/500
                  </span>

                  <div className="action-buttons">
                    <button
                      type="button"
                      className="quick-submit-btn"
                      onClick={() => handleQuickFeedback(rating)}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? (
                        <>
                          <div className="spinner" size={16} />
                          Submitting...
                        </>
                      ) : (
                        'Submit without comment'
                      )}
                    </button>

                    <button
                      type="submit"
                      className="submit-btn primary"
                      disabled={isSubmitting || !comment.trim()}
                    >
                      {isSubmitting ? (
                        <>
                          <div className="spinner" size={16} />
                          Submitting...
                        </>
                      ) : (
                        <>
                          Submit with comment
                          <Send size={16} />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            </motion.div>
          )}

          {!rating && (
            <div className="quick-feedback-hint">
              <p>Click an option to submit quick feedback or add a comment</p>
            </div>
          )}
        </div>
      </motion.div>

      <style jsx>{`
        .feedback-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
          padding: 20px;
        }

        .feedback-modal {
          background: var(--ifm-background-color);
          border-radius: 12px;
          width: 100%;
          max-width: 480px;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
          overflow: hidden;
        }

        .success-modal {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px;
          text-align: center;
        }

        .success-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .success-icon {
          color: var(--ifm-color-success);
        }

        .success-content h3 {
          margin: 0;
          font-size: 24px;
          color: var(--ifm-color-content);
        }

        .success-content p {
          margin: 0;
          color: var(--ifm-color-emphasis-700);
          line-height: 1.5;
        }

        .feedback-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid var(--ifm-color-emphasis-200);
        }

        .feedback-header h3 {
          margin: 0;
          font-size: 20px;
          color: var(--ifm-color-content);
        }

        .close-btn {
          background: none;
          border: none;
          padding: 8px;
          border-radius: 6px;
          cursor: pointer;
          color: var(--ifm-color-emphasis-600);
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .close-btn:hover {
          background: var(--ifm-color-emphasis-100);
          color: var(--ifm-color-content);
        }

        .feedback-content {
          padding: 24px 20px;
        }

        .feedback-question {
          font-size: 16px;
          font-weight: 600;
          color: var(--ifm-color-content);
          margin: 0 0 20px;
          text-align: center;
        }

        .rating-buttons {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
        }

        .rating-btn {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          border: 2px solid var(--ifm-color-emphasis-200);
          background: var(--ifm-background-color);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          color: var(--ifm-color-emphasis-700);
        }

        .rating-btn:hover:not(:disabled) {
          border-color: var(--ifm-color-emphasis-300);
          background: var(--ifm-color-emphasis-100);
          transform: translateY(-2px);
        }

        .rating-btn.selected {
          border-color: var(--ifm-color-primary);
          background: var(--ifm-color-primary-lightest);
          color: var(--ifm-color-primary);
        }

        .rating-btn.positive.selected {
          border-color: var(--ifm-color-success);
          background: var(--ifm-color-success-lightest);
          color: var(--ifm-color-success);
        }

        .rating-btn.negative.selected {
          border-color: var(--ifm-color-danger);
          background: var(--ifm-color-danger-lightest);
          color: var(--ifm-color-danger);
        }

        .rating-btn span {
          font-size: 14px;
          font-weight: 500;
        }

        .comment-section {
          border-top: 1px solid var(--ifm-color-emphasis-200);
          padding-top: 20px;
        }

        .comment-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }

        .comment-header label {
          font-size: 14px;
          font-weight: 500;
          color: var(--ifm-color-content);
        }

        .comment-header svg {
          color: var(--ifm-color-emphasis-600);
        }

        textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid var(--ifm-color-emphasis-200);
          border-radius: 6px;
          font-family: inherit;
          font-size: 14px;
          line-height: 1.5;
          resize: vertical;
          background: var(--ifm-background-color);
          color: var(--ifm-color-content);
          transition: border-color 0.2s;
        }

        textarea:focus {
          outline: none;
          border-color: var(--ifm-color-primary);
        }

        textarea:disabled {
          background: var(--ifm-color-emphasis-100);
          cursor: not-allowed;
        }

        .comment-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 12px;
        }

        .char-count {
          font-size: 12px;
          color: var(--ifm-color-emphasis-600);
        }

        .action-buttons {
          display: flex;
          gap: 12px;
        }

        .quick-submit-btn {
          padding: 8px 16px;
          background: none;
          border: 1px solid var(--ifm-color-emphasis-300);
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
          color: var(--ifm-color-emphasis-700);
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .quick-submit-btn:hover:not(:disabled) {
          border-color: var(--ifm-color-emphasis-400);
          background: var(--ifm-color-emphasis-100);
        }

        .submit-btn {
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .submit-btn.primary {
          background: var(--ifm-color-primary);
          color: white;
        }

        .submit-btn.primary:hover:not(:disabled) {
          background: var(--ifm-color-primary-dark);
        }

        .submit-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        .quick-feedback-hint {
          text-align: center;
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid var(--ifm-color-emphasis-100);
        }

        .quick-feedback-hint p {
          font-size: 13px;
          color: var(--ifm-color-emphasis-600);
          margin: 0;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 480px) {
          .feedback-modal {
            max-width: 100%;
            margin: 0 10px;
          }

          .rating-buttons {
            flex-direction: column;
          }

          .action-buttons {
            flex-direction: column;
            width: 100%;
          }

          .quick-submit-btn,
          .submit-btn {
            width: 100%;
            justify-content: center;
          }
        }
      `}</style>
    </motion.div>
  );
}