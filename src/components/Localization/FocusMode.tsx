import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ThumbsUp, ThumbsDown, Send, Loader2, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useLocalization } from '../../contexts/LocalizationContext';
import { useFocusMode } from '../../contexts/FocusModeContext';
import { TranslationFeedback } from './TranslationFeedback';
import styles from '../ChatWidget/styles/ChatWidget.module.css';
// CSS for syntax highlighting is imported via the oneDark style object

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
  const [showFeedback, setShowFeedback] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const autoScrollEnabled = useRef(true);

  // Process content with transliteration (moved up to be used in useEffect)
  const processedContent = useMemo(() => {
    const content = translatedContent || originalContent;
    return transliterateTechnicalTerms(content);
  }, [translatedContent, originalContent]);

  // Enable full screen mode
  useEffect(() => {
    if (isVisible) {
      document.body.style.overflow = 'hidden';
      document.documentElement.classList.add('focus-mode-active');
      autoScrollEnabled.current = true; // Reset auto-scroll on open
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
  }, [isVisible]);

  // Auto-scroll logic
  useEffect(() => {
    if (contentRef.current && autoScrollEnabled.current && translatedContent) {
      const { scrollHeight, clientHeight } = contentRef.current;
      // Only auto-scroll if content is scrollable
      if (scrollHeight > clientHeight) {
        contentRef.current.scrollTop = scrollHeight;
      }
    }
  }, [processedContent, translatedContent]);

  const handleScroll = () => {
    if (contentRef.current) {
      const { scrollHeight, scrollTop, clientHeight } = contentRef.current;
      // Check if user is near the bottom (within 50px)
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      autoScrollEnabled.current = isAtBottom;
    }
  };

  
  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isVisible) return;

      switch (e.key) {
        case 'Escape':
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, onClose]);

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

  // Render markdown content with syntax highlighting
  const renderMarkdown = (text: string, isOriginal: boolean = false) => {
    const components = {
      // Custom component for headings to add proper classes
      h1: ({children, ...props}: any) => (
        <h1 {...props} className="markdown-heading heading-1">
          {children}
        </h1>
      ),
      h2: ({children, ...props}: any) => (
        <h2 {...props} className="markdown-heading heading-2">
          {children}
        </h2>
      ),
      h3: ({children, ...props}: any) => (
        <h3 {...props} className="markdown-heading heading-3">
          {children}
        </h3>
      ),
      h4: ({children, ...props}: any) => (
        <h4 {...props} className="markdown-heading heading-4">
          {children}
        </h4>
      ),
      h5: ({children, ...props}: any) => (
        <h5 {...props} className="markdown-heading heading-5">
          {children}
        </h5>
      ),
      h6: ({children, ...props}: any) => (
        <h6 {...props} className="markdown-heading heading-6">
          {children}
        </h6>
      ),
      // Custom paragraph component
      p: ({children, ...props}: any) => (
        <p {...props} className={`markdown-paragraph ${isOriginal ? 'english-text' : 'urdu-text'}`}>
          {children}
        </p>
      ),
      // Custom list components
      ul: ({children, ...props}: any) => (
        <ul {...props} className={`markdown-list ${isOriginal ? 'english-list' : 'urdu-list'}`}>
          {children}
        </ul>
      ),
      ol: ({children, ...props}: any) => (
        <ol {...props} className={`markdown-list ${isOriginal ? 'english-list' : 'urdu-list'}`}>
          {children}
        </ol>
      ),
      li: ({children, ...props}: any) => (
        <li {...props} className={`markdown-list-item ${isOriginal ? 'english-text' : 'urdu-text'}`}>
          {children}
        </li>
      ),
      // Code block component with syntax highlighting
      code: ({node, inline, className, children, ...props}: any) => {
        const match = /language-(\w+)/.exec(className || '');
        // Use inline prop if available, otherwise fallback to heuristics
        // Note: react-markdown v8+ passes 'inline' prop, v6/7 might not
        const isInlineCode = inline !== undefined 
          ? inline 
          : !match && !String(children).includes('\n');

        if (isInlineCode) {
          return (
            <code
              {...props}
              className="inline-code"
              dir="ltr"
            >
              {children}
            </code>
          );
        }

        return (
          <div
            className="code-block-wrapper"
            dir="ltr"
          >
            <SyntaxHighlighter
              language={match ? match[1] : 'text'}
              style={oneDark}
              PreTag="div"
              className="code-block-force-ltr"
              customStyle={{
                textAlign: 'left',
                direction: 'ltr',
                background: '#2d2d2d',
                padding: '16px',
                borderRadius: '8px',
                margin: '0',
                fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace"
              }}
              codeTagProps={{
                style: {
                  fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace",
                  direction: 'ltr',
                  textAlign: 'left'
                }
              }}
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          </div>
        );
      },
      // Custom blockquote
      blockquote: ({children, ...props}: any) => (
        <blockquote {...props} className={`markdown-blockquote ${isOriginal ? '' : 'urdu-blockquote'}`}>
          {children}
        </blockquote>
      ),
      // Custom table components
      table: ({children, ...props}: any) => (
        <table {...props} className={`markdown-table ${isOriginal ? 'english-table' : 'urdu-table'}`}>
          {children}
        </table>
      ),
      thead: ({children, ...props}: any) => (
        <thead {...props} className="table-header">
          {children}
        </thead>
      ),
      tbody: ({ children, ...props }: any) => (
        <tbody {...props} className="table-body">
          {children}
        </tbody>
      ),
      tr: ({ children, ...props }: any) => (
        <tr {...props} className="table-row">
          {children}
        </tr>
      ),
      th: ({ children, ...props }: any) => (
        <th {...props} className={`table-header-cell ${isOriginal ? '' : ''}`}>
          {children}
        </th>
      ),
      td: ({ children, ...props }: any) => (
        <td {...props} className={`table-cell ${isOriginal ? '' : ''}`}>
          {children}
        </td>
      ),
    };

    return (
      <div className={`markdown-content ${isOriginal ? 'english-markdown' : 'urdu-markdown'}`}>
        <ReactMarkdown
          remarkPlugins={[]}
          components={components}
        >
          {text}
        </ReactMarkdown>
      </div>
    );
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
          className="focus-mode-container"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          {/* Header Controls */}
          <div className="focus-mode-header">
            <div className="focus-mode-info">
              <span className="language-indicator">
                اردو (Urdu)
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
                className="focus-mode-control-btn close"
                onClick={onClose}
                title="Close focus mode"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Content Area */}
          <motion.div
              className="focus-mode-content"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.3 }}
              ref={contentRef}
              onScroll={handleScroll}
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
                  <div className="translated-text urdu-text" dir="rtl">
                    {renderMarkdown(processedContent, false)}
                  </div>
                </div>
              )}
            </motion.div>

          
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

        .focus-mode-control-btn.feedback-btn {
          background: var(--ifm-color-warning);
          color: white;
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
        
        /* English/Original Text Container */
        .english-text-container {
          direction: ltr;
          text-align: left;
          font-family: var(--ifm-font-family-base);
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
        
        .english-text {
          text-align: left;
          direction: ltr;
        }

        
        /* Markdown content styles */
        .markdown-content {
          line-height: 1.8;
          font-size: 18px;
        }
        
        .english-markdown {
          direction: ltr;
          text-align: left;
        }

        .markdown-content urdu-paragraph {
          text-align: right;
          direction: rtl;
          font-family: 'Noto Nastaliq Urdu', 'Noto Sans Arabic', sans-serif;
          font-size: 20px;
        }

        /* Headings */
        .markdown-heading {
          font-weight: 700;
          margin: 24px 0 16px 0;
          color: var(--ifm-color-content);
          line-height: 1.3;
        }
        
        /* Ensure English headings are left aligned */
        .english-text-container .markdown-heading {
          text-align: left;
          direction: ltr;
        }

        .markdown-heading:h1 {
          font-size: 2.5em;
          margin-top: 0;
        }

        .markdown-heading:h2 {
          font-size: 2em;
          border-bottom: 2px solid var(--ifm-color-emphasis-200);
          padding-bottom: 8px;
        }

        .markdown-heading:h3 {
          font-size: 1.5em;
        }

        .markdown-heading:h4 {
          font-size: 1.25em;
        }

        .markdown-heading:h5 {
          font-size: 1.125em;
        }

        .markdown-heading:h6 {
          font-size: 1em;
          color: var(--ifm-color-emphasis-700);
        }

        /* Paragraphs */
        .markdown-paragraph {
          margin-bottom: 16px;
          color: var(--ifm-color-content);
        }

        /* Lists */
        .markdown-list {
          margin: 16px 0;
          padding-left: 32px;
          color: var(--ifm-color-content);
        }
        
        /* English specific list styling */
        .english-list {
          padding-left: 2rem;
          padding-right: 0;
          text-align: left;
          direction: ltr;
          list-style-position: outside;
        }

        .markdown-list.urdu-list {
          padding-left: 0;
          padding-right: 32px;
          direction: rtl;
          text-align: right;
        }

        .markdown-list-item {
          margin-bottom: 8px;
          line-height: 1.7;
        }

        .markdown-list-item > p {
          margin: 0;
        }

        /* Unordered lists */
        .markdown-ul {
          list-style-type: disc;
        }

        .markdown-ul .markdown-list-item::marker {
          color: var(--ifm-color-primary);
        }

        /* Ordered lists */
        .markdown-ol {
          list-style-type: decimal;
        }

        .markdown-ol .markdown-list-item::marker {
          color: var(--ifm-color-primary);
          font-weight: 600;
        }

        /* Nested lists */
        .markdown-list .markdown-list {
          margin: 8px 0;
        }

        /* Code blocks - always left aligned */
        .code-block-wrapper {
          text-align: left !important;
          direction: ltr !important;
          display: block !important;
          margin: 16px 0 !important;
        }

        .code-block-force-ltr {
          background: #2d2d2d !important;
          border-radius: 8px !important;
          padding: 16px !important;
          margin: 0 !important;
          overflow-x: auto !important;
          position: relative !important;
          text-align: left !important;
          direction: ltr !important;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
        }

        .code-block-force-ltr code {
          background: none !important;
          padding: 0 !important;
          font-size: 14px !important;
          line-height: 1.5 !important;
          color: #fff !important;
          text-align: left !important;
          direction: ltr !important;
          display: block !important;
          font-family: inherit !important;
        }

        .code-block-force-ltr pre {
          text-align: left !important;
          direction: ltr !important;
          margin: 0 !important;
          padding: 0 !important;
        }

        .code-block-force-ltr * {
          text-align: left !important;
          direction: ltr !important;
        }

        /* Inline code */
        .inline-code {
          background: var(--ifm-color-emphasis-200);
          padding: 2px 6px;
          border-radius: 4px;
          font-family: 'Courier New', Courier, monospace;
          font-size: 0.9em;
          color: var(--ifm-color-primary);
        }

        /* Blockquotes */
        .markdown-blockquote {
          margin: 16px 0;
          padding: 8px 16px;
          border-left: 4px solid var(--ifm-color-primary);
          background: var(--ifm-color-emphasis-100);
          color: var(--ifm-color-emphasis-800);
          font-style: italic;
        }

        .markdown-blockquote.urdu-blockquote {
          border-left: none;
          border-right: 4px solid var(--ifm-color-primary);
          text-align: right;
          direction: rtl;
        }

        /* Tables */
        .markdown-table {
          width: 100%;
          border-collapse: collapse;
          margin: 16px 0;
          font-size: 15px;
        }

        .markdown-table th,
        .markdown-table td {
          border: 1px solid var(--ifm-color-emphasis-300);
          padding: 8px 12px;
          text-align: left;
        }

        .markdown-table th {
          background: var(--ifm-color-emphasis-200);
          font-weight: 600;
        }

        .markdown-table.urdu-table th,
        .markdown-table.urdu-table td {
          text-align: right;
        }

        /* Horizontal rule */
        .markdown-hr {
          border: none;
          height: 2px;
          background: var(--ifm-color-emphasis-200);
          margin: 24px 0;
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
        }
      `}</style>
    </AnimatePresence>
  );
}