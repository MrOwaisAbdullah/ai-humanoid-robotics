import React from 'react';
import { motion } from 'framer-motion';
import styles from '../styles/ChatWidget.module.css';

interface WelcomeScreenProps {
  onSuggestionClick?: (suggestion: string) => void;
}

// Static suggestions matching the reference design
const suggestions = [
  {
    text: "What is ChatKit?",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    )
  },
  {
    text: "Show me an example widget",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="9" y1="9" x2="15" y2="9"/>
        <line x1="9" y1="15" x2="15" y2="15"/>
      </svg>
    )
  },
  {
    text: "What can I customize?",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
    )
  },
  {
    text: "How do I use client side tools?",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
      </svg>
    )
  },
  {
    text: "Server side tools",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
        <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
        <line x1="6" y1="6" x2="6.01" y2="6"/>
        <line x1="6" y1="18" x2="6.01" y2="18"/>
      </svg>
    )
  }
];

export default function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  const handleSuggestionClick = (suggestion: string) => {
    if (onSuggestionClick) {
      onSuggestionClick(suggestion);
    }
  };

  return (
    <div className={styles.welcomeScreen}>
      <motion.h4
        className={styles.welcomeTitle}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        What can I help with today?
      </motion.h4>

      {/* Suggestion buttons with icons matching reference design */}
      <motion.div
        className={styles.suggestions}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.3 }}
      >
        {suggestions.map((suggestion, index) => (
          <motion.button
            key={index}
            className={styles.suggestion}
            onClick={() => handleSuggestionClick(suggestion.text)}
            aria-label={`Ask: ${suggestion.text}`}
            title={`Ask: ${suggestion.text}`}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 + index * 0.05, duration: 0.2 }}
            whileHover={{
              scale: 1.02,
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              transition: { duration: 0.15 }
            }}
            whileTap={{ scale: 0.98 }}
          >
            <span className={styles.suggestionIcon} style={{ opacity: 0.7 }}>
              {suggestion.icon}
            </span>
            <span className={styles.suggestionText}>{suggestion.text}</span>
          </motion.button>
        ))}
      </motion.div>
    </div>
  );
}