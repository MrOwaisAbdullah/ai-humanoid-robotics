import React from 'react';
import { motion } from 'framer-motion';
import { getOptimizedMotionProps, thinkingIndicatorVariants } from '../utils/animations';
import styles from '../styles/ChatWidget.module.css';

interface ThinkingIndicatorProps {
  message?: string;
  className?: string;
}

export default function ThinkingIndicator({
  message = "",
  className = ""
}: ThinkingIndicatorProps) {
  return (
    <motion.div
      className={`${styles.thinkingIndicator} ${className}`}
      role="status"
      aria-live="polite"
      aria-label="AI is thinking..."
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
    >
      <div className={styles.thinkingContent}>
        {/* Simple AI avatar */}
        <div className={styles.thinkingAvatar}>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="currentColor"
            className={styles.thinkingIcon}
          >
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
          </svg>
        </div>

        {/* Just the animated dots */}
        <div className={styles.thinkingDots}>
          {[0, 1, 2].map((index) => (
            <motion.div
              key={index}
              className={styles.thinkingDot}
              animate={{
                opacity: [0.3, 1, 0.3],
                y: [0, -3, 0],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: index * 0.15,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}