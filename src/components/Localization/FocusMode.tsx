import React, { useEffect, useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Minimize2, Volume2, VolumeX, ThumbsUp, ThumbsDown, Send, Loader2, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { useLocalization } from '../../contexts/LocalizationContext';
import { useFocusMode } from '../../contexts/FocusModeContext';
import { TranslationFeedback } from './TranslationFeedback';
import styles from '../ChatWidget/styles/ChatWidget.module.css';

interface FocusModeProps {
  isVisible: boolean;
  onClose: () => void;
  originalContent: string;
  translatedContent?: string;
  isLoading?: boolean;
  error?: string | null;
  translationId?: number;
  progress?: number;
}

// Technical terms transliteration map
const transliterationMap: Record<string, string> = {
  'artificial intelligence': 'مصنوعی ذہانت',
  'machine learning': 'مشین لرننگ',
  'deep learning': 'ڈیپ لرننگ',
  'robotics': 'روبوٹکس',
  'algorithm': 'الگورتھم',
  'data': 'ڈیٹا',
  'computer': 'کمپیوٹر',
  'software': 'سافٹ ویئر',
  'hardware': 'ہارڈ ویئر',
  'programming': 'پروگرامنگ',
  'database': 'ڈیٹا بیس',
  'network': 'نیٹ ورک',
  'security': 'سیکیورٹی',
  'cloud': 'کلاڈ',
  'technology': 'ٹیکنالوجی',
  'sensor': 'سینسر',
  'actuator': 'ایکچویٹر',
  'controller': 'کنٹرولر',
  'system': 'سسٹم',
  'model': 'ماڈل',
  'simulation': 'سیمولیشن',
  'optimization': 'آپٹیمائزیشن',
  'neural network': 'نیورل نیٹ ورک'
};

// Function to transliterate technical terms in Urdu text
const transliterateTechnicalTerms = (text: string): string => {
  let result = text;

  // Sort keys by length (longest first) to avoid partial replacements
  const sortedTerms = Object.keys(transliterationMap).sort((a, b) => b.length - a.length);

  sortedTerms.forEach(term => {
    const regex = new RegExp(`\\b${term}\\b`, 'gi');
    result = result.replace(regex, transliterationMap[term]);
  });

  return result;
};

export default function FocusMode({
  isVisible,
  onClose,
  originalContent,
  translatedContent,
  isLoading = false,
  error = null,
  translationId,
  progress = 0
}: FocusModeProps) {
  const { isRTL, formatText, language } = useLocalization();
  const { submitFeedback, retryTranslation } = useFocusMode();
  const [isMinimized, setIsMinimized] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);
  const speechRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Enable full screen mode
  useEffect(() => {
    if (isVisible && !isMinimized) {
      document.body.style.overflow = 'hidden';
      document.documentElement.classList.add('focus-mode-active');
    } else {
      document.body.style.overflow = '';
      document.documentElement.classList.remove('focus-mode-active');
    }

    return () => {
      document.body.style.overflow = '';
      document.documentElement.classList.remove('focus-mode-active');
      // Stop speech synthesis when component unmounts
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
      }
    };
  }, [isVisible, isMinimized]);

  // Enhanced text-to-speech for Urdu content
  const speakUrduText = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) {
      showToast('Text-to-speech is not supported in your browser');
      return;
    }

    // Cancel any ongoing speech
    speechSynthesis.cancel();

    // Split text into words for highlighting
    const words = text.split(' ');
    setCurrentWordIndex(0);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ur-PK';
    utterance.rate = 0.85;
    utterance.pitch = 1;
    utterance.volume = 1;

    // Get Urdu voices if available
    const voices = speechSynthesis.getVoices();
    const urduVoice = voices.find(voice =>
      voice.lang.startsWith('ur') ||
      voice.name.includes('Urdu') ||
      voice.name.includes('Pakistan')
    );

    if (urduVoice) {
      utterance.voice = urduVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => {
      setIsSpeaking(false);
      showToast('Failed to start text-to-speech');
    };

    // Word boundary events for highlighting
    utterance.onboundary = (event) => {
      if (event.name === 'word') {
        setCurrentWordIndex(Math.floor(event.charIndex / (text.length / words.length)));
      }
    };

    speechRef.current = utterance;
    speechSynthesis.speak(utterance);
  }, []);

  const stopSpeaking = useCallback(() => {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
      setIsSpeaking(false);
      setCurrentWordIndex(0);
    }
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isVisible || isMinimized) return;

      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          if (showOriginal) {
            setShowOriginal(false);
          }
          break;
        case 'ArrowRight':
          if (!showOriginal && translatedContent) {
            setShowOriginal(true);
          }
          break;
        case ' ':
          if (e.target === document.body) {
            e.preventDefault();
            const textToSpeak = showOriginal ? originalContent : (translatedContent || originalContent);
            if (isSpeaking) {
              stopSpeaking();
            } else {
              speakUrduText(textToSpeak);
            }
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, isMinimized, showOriginal, translatedContent, originalContent, isSpeaking, speakUrduText, stopSpeaking, onClose]);

  // Process content with transliteration
  const processedContent = translatedContent
    ? transliterateTechnicalTerms(translatedContent)
    : transliterateTechnicalTerms(originalContent);

  // Handle feedback submission
  const handleFeedback = async (rating: 1 | -1, comment?: string) => {
    if (!translationId) {
      showToast('Unable to submit feedback: Translation ID not found');
      return;
    }

    try {
      await submitFeedback(translationId, rating, comment);
      showToast(`Thank you for your ${rating === 1 ? 'positive' : 'negative'} feedback!`);
      setShowFeedback(false);
    } catch (error) {
      showToast('Failed to submit feedback. Please try again.');
    }
  };

  // Render words with highlighting for TTS
  const renderTextWithHighlighting = (text: string, isOriginal: boolean = false) => {
    if (!isSpeaking || isOriginal) {
      return text.split('\n').map((paragraph, index) => (
        <p key={index} className="text-paragraph">
          {paragraph}
        </p>
      ));
    }

    const words = text.split(' ');
    return text.split('\n').map((paragraph, pIndex) => (
      <p key={pIndex} className="text-paragraph">
        {paragraph.split(' ').map((word, wIndex) => {
          const globalWordIndex = text.split('\n')
            .slice(0, pIndex)
            .reduce((acc, p) => acc + p.split(' ').length, 0) + wIndex;

          return (
            <span
              key={wIndex}
              className={
                globalWordIndex === currentWordIndex
                  ? 'highlighted-word'
                  : globalWordIndex < currentWordIndex
                  ? 'spoken-word'
                  : ''
              }
            >
              {word}
              {wIndex < paragraph.split(' ').length - 1 && ' '}
            </span>
          );
        })}
      </p>
    ));
  };

  // Toast helper function
  const showToast = (message: string) => {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-5 right-5 bg-zinc-900 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in-up border border-zinc-800';
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #18181b;
      color: white;
      padding: 12px 16px;
      border-radius: 8px;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
      z-index: 9999;
      animation: slideInUp 0.3s ease-out;
      border: 1px solid #27272a;
      font-size: 14px;
    `;

    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'slideOutDown 0.3s ease-out';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  };

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        className={`focus-mode-overlay ${isRTL ? 'rtl' : 'ltr'}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        {/* Focus Mode Container */}
        <motion.div
          className={`focus-mode-container ${isMinimized ? 'minimized' : ''}`}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: isMinimized ? 0.3 : 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          {/* Header Controls */}
          <div className="focus-mode-header">
            <div className="focus-mode-info">
              <span className="language-indicator">
                {showOriginal ? 'English' : 'اردو (Urdu)'}
              </span>
              {progress > 0 && progress < 100 && (
                <div className="translation-progress-bar">
                  <div
                    className="translation-progress-fill"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              )}
            </div>

            <div className="focus-mode-controls">
              {translatedContent && (
                <button
                  className="focus-mode-control-btn language-toggle"
                  onClick={() => setShowOriginal(!showOriginal)}
                  title={showOriginal ? "Show Urdu Translation" : "Show Original"}
                >
                  {showOriginal ? "EN" : "اردو"}
                </button>
              )}

              {language === 'ur' && (
                <button
                  className={`focus-mode-control-btn tts-btn ${isSpeaking ? 'active' : ''}`}
                  onClick={() => {
                    const textToSpeak = showOriginal ? originalContent : (translatedContent || originalContent);
                    if (isSpeaking) {
                      stopSpeaking();
                    } else {
                      speakUrduText(textToSpeak);
                    }
                  }}
                  title={isSpeaking ? "Stop reading" : "Read aloud"}
                >
                  {isSpeaking ? <VolumeX size={16} /> : <Volume2 size={16} />}
                </button>
              )}

              {translationId && (
                <button
                  className="focus-mode-control-btn feedback-btn"
                  onClick={() => setShowFeedback(!showFeedback)}
                  title="Provide feedback"
                >
                  <ThumbsUp size={16} />
                </button>
              )}

              <button
                className="focus-mode-control-btn"
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? "Expand" : "Minimize"}
              >
                <Minimize2 size={16} />
              </button>

              <button
                className="focus-mode-control-btn close"
                onClick={onClose}
                title="Close focus mode"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Content Area */}
          {!isMinimized && (
            <motion.div
              className="focus-mode-content"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.3 }}
              ref={contentRef}
            >
              {error ? (
                <div className="focus-mode-error">
                  <AlertCircle size={48} />
                  <h3>Translation Error</h3>
                  <p>{error}</p>
                  <button
                    className="retry-btn"
                    onClick={retryTranslation}
                  >
                    Try Again
                  </button>
                </div>
              ) : isLoading ? (
                <div className="focus-mode-loading">
                  <Loader2 className="loading-spinner" size={40} />
                  <p>{formatText('Translating to Urdu...')}</p>
                  {progress > 0 && (
                    <div className="loading-progress">
                      <div
                        className="loading-progress-bar"
                        style={{ width: `${progress}%` }}
                      />
                      <span>{progress}%</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="focus-mode-text">
                  {showOriginal ? (
                    <div className="original-text">
                      {renderTextWithHighlighting(originalContent, true)}
                    </div>
                  ) : (
                    <div className="translated-text urdu-text" dir="rtl">
                      {renderTextWithHighlighting(processedContent, false)}
                    </div>
                  )}

                  {/* Navigation hint */}
                  <div className="navigation-hint">
                    <span>
                      Press <kbd>Space</kbd> to read aloud
                      {translatedContent && <>, <kbd>←</kbd>/<kbd>→</kbd> to switch languages</>}
                    </span>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Footer with progress indicator */}
          {!isMinimized && !isLoading && !error && (
            <motion.div
              className="focus-mode-footer"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.3 }}
            >
              <div className="reading-progress">
                <span className="progress-label">
                  {formatText('Reading Mode')}
                </span>
                <div className="progress-indicator">
                  <div className={`progress-dot ${showOriginal ? 'active' : ''}`} />
                  <div className={`progress-dot ${!showOriginal ? 'active' : ''}`} />
                </div>
              </div>
            </motion.div>
          )}

          {/* Feedback Modal */}
          <AnimatePresence>
            {showFeedback && (
              <TranslationFeedback
                onClose={() => setShowFeedback(false)}
                onSubmit={handleFeedback}
              />
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>

      <style jsx>{`
        .focus-mode-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.95);
          backdrop-filter: blur(10px);
          z-index: 9999;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }

        .focus-mode-container {
          background: var(--ifm-background-color);
          border-radius: 12px;
          width: 100%;
          max-width: 900px;
          height: 80vh;
          max-height: 800px;
          display: flex;
          flex-direction: column;
          box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
          position: relative;
        }

        .focus-mode-container.minimized {
          width: 300px;
          height: 60px;
          max-height: 60px;
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 10000;
        }

        .focus-mode-header {
          padding: 15px 20px;
          border-bottom: 1px solid var(--ifm-color-emphasis-200);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: var(--ifm-background-surface-color);
          border-radius: 12px 12px 0 0;
        }

        .focus-mode-info {
          display: flex;
          align-items: center;
          gap: 15px;
          flex: 1;
        }

        .language-indicator {
          font-size: 14px;
          font-weight: 600;
          color: var(--ifm-color-emphasis-700);
          padding: 4px 12px;
          background: var(--ifm-color-emphasis-100);
          border-radius: 20px;
        }

        .translation-progress-bar {
          flex: 1;
          max-width: 200px;
          height: 4px;
          background: var(--ifm-color-emphasis-200);
          border-radius: 2px;
          overflow: hidden;
        }

        .translation-progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--ifm-color-primary), var(--ifm-color-primary-light));
          transition: width 0.3s ease;
        }

        .focus-mode-controls {
          display: flex;
          gap: 10px;
        }

        .focus-mode-control-btn {
          background: var(--ifm-color-emphasis-100);
          border: none;
          border-radius: 6px;
          padding: 8px 12px;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 14px;
          color: var(--ifm-color-emphasis-800);
          position: relative;
        }

        .focus-mode-control-btn:hover {
          background: var(--ifm-color-primary);
          color: white;
          transform: translateY(-1px);
        }

        .focus-mode-control-btn.close {
          background: var(--ifm-color-danger);
          color: white;
        }

        .focus-mode-control-btn.language-toggle {
          background: var(--ifm-color-secondary);
          color: white;
          font-weight: 600;
        }

        .focus-mode-control-btn.tts-btn {
          background: var(--ifm-color-info);
          color: white;
        }

        .focus-mode-control-btn.tts-btn.active {
          background: var(--ifm-color-success);
          animation: pulse 2s infinite;
        }

        .focus-mode-control-btn.feedback-btn {
          background: var(--ifm-color-warning);
          color: white;
        }

        @keyframes pulse {
          0%, 100% {
            box-shadow: 0 0 0 0 rgba(var(--ifm-color-success-rgb), 0.4);
          }
          50% {
            box-shadow: 0 0 0 10px rgba(var(--ifm-color-success-rgb), 0);
          }
        }

        .focus-mode-content {
          flex: 1;
          overflow-y: auto;
          padding: 30px 40px;
          position: relative;
        }

        .focus-mode-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          gap: 20px;
          color: var(--ifm-color-danger);
          text-align: center;
        }

        .focus-mode-error h3 {
          margin: 0;
          font-size: 24px;
        }

        .focus-mode-error p {
          margin: 0;
          max-width: 400px;
          line-height: 1.6;
        }

        .retry-btn {
          padding: 10px 20px;
          background: var(--ifm-color-primary);
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 16px;
          transition: background 0.2s;
        }

        .retry-btn:hover {
          background: var(--ifm-color-primary-dark);
        }

        .focus-mode-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          gap: 20px;
        }

        .loading-spinner {
          animation: spin 1s linear infinite;
        }

        .loading-progress {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 10px;
          width: 200px;
        }

        .loading-progress-bar {
          width: 100%;
          height: 6px;
          background: var(--ifm-color-emphasis-200);
          border-radius: 3px;
          overflow: hidden;
        }

        .loading-progress span {
          font-size: 14px;
          color: var(--ifm-color-emphasis-600);
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .focus-mode-text {
          line-height: 1.8;
          font-size: 18px;
          position: relative;
        }

        .urdu-text {
          font-family: 'Noto Nastaliq Urdu', 'Noto Sans Arabic', sans-serif;
          font-size: 20px;
          text-align: right;
        }

        .text-paragraph {
          margin-bottom: 20px;
          color: var(--ifm-color-content);
        }

        .urdu-paragraph {
          text-align: right;
          direction: rtl;
        }

        .highlighted-word {
          background: rgba(var(--ifm-color-primary-rgb), 0.3);
          padding: 2px 4px;
          border-radius: 3px;
          transition: background 0.2s;
        }

        .spoken-word {
          color: var(--ifm-color-success);
        }

        .navigation-hint {
          position: sticky;
          bottom: 20px;
          background: var(--ifm-background-surface-color);
          border: 1px solid var(--ifm-color-emphasis-200);
          border-radius: 8px;
          padding: 12px 16px;
          margin-top: 30px;
          font-size: 13px;
          color: var(--ifm-color-emphasis-600);
          text-align: center;
        }

        .navigation-hint kbd {
          background: var(--ifm-color-emphasis-200);
          border: 1px solid var(--ifm-color-emphasis-300);
          border-radius: 4px;
          padding: 2px 6px;
          font-family: monospace;
          font-size: 12px;
          margin: 0 2px;
        }

        .focus-mode-footer {
          padding: 20px;
          border-top: 1px solid var(--ifm-color-emphasis-200);
          background: var(--ifm-background-surface-color);
          border-radius: 0 0 12px 12px;
        }

        .reading-progress {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .progress-label {
          font-size: 14px;
          color: var(--ifm-color-emphasis-600);
        }

        .progress-indicator {
          display: flex;
          gap: 8px;
        }

        .progress-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--ifm-color-emphasis-300);
          transition: all 0.3s;
        }

        .progress-dot.active {
          background: var(--ifm-color-primary);
          transform: scale(1.2);
        }

        /* RTL styles */
        .focus-mode-overlay.rtl .focus-mode-text {
          direction: rtl;
        }

        .focus-mode-overlay.rtl .focus-mode-header {
          direction: ltr;
        }

        .focus-mode-overlay.rtl .focus-mode-controls {
          direction: ltr;
        }

        /* Focus mode indicator for body */
        :global(.focus-mode-active) {
          overflow: hidden !important;
        }

        :global(.focus-mode-active) .navbar,
        :global(.focus-mode-active) .sidebar,
        :global(.focus-mode-active) footer {
          opacity: 0.1;
          pointer-events: none;
        }

        /* Responsive */
        @media (max-width: 768px) {
          .focus-mode-container {
            height: 100vh;
            max-height: 100vh;
            border-radius: 0;
          }

          .focus-mode-header {
            padding: 10px 15px;
            flex-wrap: wrap;
          }

          .focus-mode-info {
            order: 2;
            width: 100%;
            margin-top: 10px;
            justify-content: center;
          }

          .focus-mode-controls {
            order: 1;
          }

          .focus-mode-content {
            padding: 20px;
          }

          .focus-mode-text {
            font-size: 16px;
          }

          .urdu-text {
            font-size: 18px;
          }

          .translation-progress-bar {
            max-width: 150px;
          }
        }

        /* High contrast mode support */
        @media (prefers-contrast: high) {
          .focus-mode-container {
            border: 2px solid var(--ifm-color-content);
          }

          .focus-mode-control-btn {
            border: 1px solid var(--ifm-color-content);
          }
        }

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
          .focus-mode-control-btn,
          .progress-dot,
          .translation-progress-fill {
            transition: none;
          }

          .focus-mode-control-btn.tts-btn.active {
            animation: none;
          }
        }
      `}</style>
    </AnimatePresence>
  );
}