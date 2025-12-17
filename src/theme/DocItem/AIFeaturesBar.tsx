import React, { useState, useEffect } from 'react';
import { useFocusMode } from '../../contexts/FocusModeContext';
import { useLocalization } from '../../contexts/LocalizationContext';
import { useAuth } from '../../contexts/AuthContext';
import { Loader2, Globe, Sparkles, Lock } from 'lucide-react';
import { useLocation } from '@docusaurus/router';
import TextToSpeech from '../../components/TTS/TextToSpeech';
import { LoginButton } from '../../components/Auth/LoginButton';
import { canPersonalize, getPersonalizationStatus } from '../../services/personalizationApi';
import { extractCurrentPageContent, extractSelectedText } from '../../utils/contentExtractor';
import { PersonalizationModal } from '../../components/Personalization/PersonalizationModal';
import styles from './AIFeaturesBar.module.css';

export default function AIFeaturesBar() {
  const { showTranslation } = useFocusMode();
  const { translationEnabled, language } = useLocalization();
  const { isAuthenticated, user } = useAuth();
  const [isTranslating, setIsTranslating] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [pendingPersonalization, setPendingPersonalization] = useState(false);
  const [showPersonalizationModal, setShowPersonalizationModal] = useState(false);
  const [personalizationContent, setPersonalizationContent] = useState('');
  const [personalizationContentType, setPersonalizationContentType] = useState<'selected' | 'page'>('page');
  const [personalizationWordCount, setPersonalizationWordCount] = useState(0);
  const location = useLocation();

  // Listen for authentication state changes
  useEffect(() => {
    console.log('Auth state changed in AIFeaturesBar:', { isAuthenticated, user });

    // If we have a pending personalization and user just became authenticated
    if (pendingPersonalization && isAuthenticated && user) {
      console.log('Processing pending personalization after authentication');
      setPendingPersonalization(false);
      setShowLoginModal(false);

      // Extract content and open personalization modal
      try {
        const selectedText = extractSelectedText();

        if (selectedText && selectedText.length > 50) {
          setPersonalizationContent(selectedText);
          setPersonalizationContentType('selected');
          setPersonalizationWordCount(selectedText.split(' ').length);
          setShowPersonalizationModal(true);
        } else {
          // Use the same extractContent function for consistency
          const fallbackContent = extractContent();
          if (fallbackContent && fallbackContent.length >= 100) {
            const wordCount = fallbackContent.split(' ').length;
            setPersonalizationContent(fallbackContent);
            setPersonalizationContentType('page');
            setPersonalizationWordCount(wordCount);
            setShowPersonalizationModal(true);
          } else {
            showToast('Not enough content to personalize. Please select more text or choose a page with more content.');
          }
        }
      } catch (error) {
        console.error('Content extraction failed:', error);
        showToast('Failed to extract content for personalization. Please try again.');
      }
    }
  }, [isAuthenticated, user, pendingPersonalization]);

  // Only show on docs pages, not on other pages like blog, authentication, etc.
  if (!location.pathname.includes('/docs/') ||
      location.pathname.includes('assessments') ||
      location.pathname.includes('congratulations')) {
    return null;
  }

  const extractContent = (): string => {
    // Try to find the main content element more specifically
    const contentSelectors = [
      '.theme-doc-markdown',
      'article',
      '[role="main"]',
      'main',
      '.markdown',
      '.theme-doc-content-container'
    ];

    let bestContent = '';
    let bestSelector = '';

    // Try each content selector
    for (const selector of contentSelectors) {
      const element = document.querySelector(selector);
      if (element) {
        const textContent = getCleanTextFromElement(element);
        console.log(`[DEBUG] Selector "${selector}" found element with ${textContent?.length || 0} chars`);
        if (textContent && textContent.length > bestContent.length) {
          bestContent = textContent;
          bestSelector = selector;
        }
      }
    }

    console.log(`[DEBUG] Best selector: ${bestSelector}, content length: ${bestContent.length}`);
    console.log(`[DEBUG] First 500 chars of extracted content:`, bestContent.substring(0, 500));

    // If still no substantial content, try extracting specific elements
    if (!bestContent || bestContent.length < 50) {
      console.log('[DEBUG] Primary extraction failed or too short, using fallback elements');
      // Extract headings and paragraphs specifically
      const contentElements = document.querySelectorAll('.theme-doc-markdown h1, .theme-doc-markdown h2, .theme-doc-markdown h3, .theme-doc-markdown p, .theme-doc-markdown li');
      const texts: string[] = [];

      contentElements.forEach(el => {
        const text = el.textContent?.trim();
        if (text && text.length > 10) {
          texts.push(text);
        }
      });

      const combinedText = texts.join('\n');
      if (combinedText.length > bestContent.length) {
        bestContent = combinedText;
      }
    }

    console.log('[DEBUG] Final extracted content length:', bestContent.length);
    console.log('[DEBUG] Content preview:', bestContent.substring(0, 100));

    // Final aggressive cleaning
    if (bestContent) {
      const lines = bestContent.split('\n');
      const filteredLines = lines.filter(line => {
        const trimmedLine = line.trim();
        if (!trimmedLine || trimmedLine.length < 3) return false;

        const lowerLine = trimmedLine.toLowerCase();

        // Expanded list of UI patterns to skip
        const uiPatterns = [
          'personalize', 'translate to', 'read aloud', 'min read', 'minute read',
          'edit this page', 'last updated', 'previous', 'next',
          'welcome on this page', 'ai features', 'share', 'copy link',
          'table of contents', 'on this page', 'breadcrumbs',
          'skip to main content',
          'facebook', 'twitter', 'linkedin', 'github',
          'light mode', 'dark mode'
        ];

        // Skip if any UI pattern is found
        if (uiPatterns.some(pattern => lowerLine.includes(pattern))) {
          return false;
        }

        // Skip if it looks like navigation or UI element
        if (/^\d+ of \d+$/.test(trimmedLine) || // "1 of 10"
            /^\d+:\d+$/.test(trimmedLine) || // Time stamps
            /^[\d\s\-\/]+$/.test(trimmedLine) || // Dates
            trimmedLine.startsWith('/') || // Paths
            trimmedLine.includes(' → ') || // Breadcrumbs
            /^[a-z]+(\s[a-z]+)?\s*$/i.test(trimmedLine) && trimmedLine.length < 15) { // Single words
          return false;
        }

        return true;
      });

      bestContent = filteredLines.join('\n');
    }

    return bestContent;
  };

  // Helper function to detect UI-like text
  const looksLikeUIText = (text: string): boolean => {
    const lower = text.toLowerCase();
    const uiPatterns = [
      'personalize', 'translate', 'read', 'edit', 'share', 'copy',
      'min read', 'last updated', 'previous', 'next', 'menu',
      'home', 'search', 'theme', 'toggle', 'navigation'
    ];
    return uiPatterns.some(pattern => lower.includes(pattern));
  };

  const getCleanTextFromElement = (element: Element): string => {
    console.log('[DEBUG] Cleaning element:', element.tagName, element.className);
    // Remove script tags and other unwanted elements
    const clonedElement = element.cloneNode(true) as Element;

    // Comprehensive list of unwanted selectors
    const unwantedSelectors = [
      'script', 'style', 'noscript',
      'nav', '.navbar', '.navigation', '.menu', '.sidebar',
      '.pagination', '.theme-doc-footer', '.toolbar', '.footer',
      'button', '.btn', '.button',
      '.breadcrumbs', '.breadcrumb',
      '.ai-features-bar', '.ai-feature-btn',
      '.header', '.menu__link', '.navbar__item',
      '.theme-edit-this-page', '.last-updated',
      '.toc', '.table-of-contents',
      '.social-icons', '.share-buttons',
      '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]',
      '.theme-doc-version-badge', '.theme-doc-breadcrumbs',
      '.doc-sidebar-container', '.menu_SIkG',
      '.footer', '.col', '.row'
    ];

    // Remove unwanted elements
    unwantedSelectors.forEach(selector => {
      const elements = clonedElement.querySelectorAll(selector);
      elements.forEach(el => el.remove());
    });

    // TEMPORARILY DISABLED AGGRESSIVE TEXT-BASED REMOVAL FOR DEBUGGING
    /*
    // Also remove elements with specific text patterns
    const allElements = clonedElement.querySelectorAll('*');
    allElements.forEach(el => {
      // Skip checking large containers to avoid removing main content
      if (el.textContent && el.textContent.length > 200) {
        return;
      }

      const text = el.textContent?.trim().toLowerCase() || '';
      if (
        text.includes('edit this page') ||
        text.includes('last updated') ||
        text.includes('previous') ||
        text.includes('next') ||
        text.includes('personalize') ||
        text.includes('translate') ||
        text.includes('read aloud') ||
        text.includes('min read') ||
        text.includes('ai features') ||
        text.includes('welcome on this page') ||
        (text.length < 3 && el.tagName !== 'CODE' && el.tagName !== 'IMG') // Remove very short text
      ) {
        // Check if this element is likely a UI element
        const tagName = el.tagName.toLowerCase();
        const elClassName = typeof el.className === 'string' ? el.className : '';
        const hasClass = elClassName && (
          elClassName.includes('btn') ||
          elClassName.includes('button') ||
          elClassName.includes('nav') ||
          elClassName.includes('menu') ||
          elClassName.includes('header') ||
          elClassName.includes('footer') ||
          elClassName.includes('sidebar') ||
          elClassName.includes('toolbar') ||
          elClassName.includes('ai-feature')
        );

        if (['BUTTON', 'NAV', 'FOOTER', 'HEADER', 'ASIDE'].includes(tagName) || hasClass) {
          el.remove();
        }
      }
    });
    */

    // Get clean text content
    let textContent = clonedElement.textContent || '';
    console.log('[DEBUG] Raw text content length:', textContent.length);

    // Clean up whitespace and remove unwanted patterns
    textContent = textContent
      .replace(/\s+/g, ' ')
      .replace(/\n\s*\n/g, '\n')
      .replace(/\b(min read|minute read|reading time)\b/gi, '')
      .replace(/\b(edit this page|last updated|previous|next)\b/gi, '')
      .replace(/\b(personalize|translate|read aloud|ai features)\b/gi, '')
      .replace(/\b(welcome on this page)\b/gi, '')
      .trim();
    
    console.log('[DEBUG] Cleaned text content length:', textContent.length);
    return textContent;
  };

  const handleTranslate = async () => {
    console.log('Translate button clicked, translationEnabled:', translationEnabled);

    if (!translationEnabled) {
            showToast('Translation is disabled. Please enable it in settings.');
      return;
    }

    // Extract content from the page
    const originalText = extractContent();
    console.log('Extracted text length:', originalText?.length);
    console.log('Extracted text preview:', originalText?.substring(0, 200));

    if (!originalText || originalText.trim().length < 20) {
      showToast('Not enough content to translate. Please select a page with more text.');
      return;
    }

    // Limit text length to avoid API limits
    const maxLength = 5000;
    const truncatedText = originalText.length > maxLength
      ? originalText.substring(0, maxLength) + '...'
      : originalText;

    console.log('Text to translate length:', truncatedText.length);

    setIsTranslating(true);

    try {
      // Show translation in focus mode
      // The FocusModeContext will handle the actual translation
      console.log('Calling showTranslation...');
      await showTranslation(truncatedText, {});
      console.log('showTranslation completed');
    } catch (error) {
      console.error('Translation failed:', error);
      showToast('Translation failed. Please try again.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handlePersonalize = () => {
    // Check if user is authenticated using AuthContext
    if (!isAuthenticated) {
      setPendingPersonalization(true);
      setShowLoginModal(true);
      return;
    }

    // Clear any previous login errors and pending state
    setLoginError(null);
    setPendingPersonalization(false);

    // Use the proper content extraction with filtering
    const extractedContent = extractContent();
    console.log('[DEBUG] handlePersonalize top-level extraction:', extractedContent?.length);

    if (extractedContent && extractedContent.length > 200) {
      const words = extractedContent.trim().split(/\s+/).filter(w => w.length > 0);
      console.log('[DEBUG] handlePersonalize word count:', words.length);
      
      if (words.length >= 50) {
        console.log('[DEBUG] Using extractContent() method, cleaned length:', extractedContent.length);
        setPersonalizationContent(extractedContent);
        setPersonalizationContentType('page');
        setPersonalizationWordCount(words.length);
        setShowPersonalizationModal(true);
        return;
      }
    }

    // Extract content for personalization
    try {
      // First try to get selected text
      const selectedText = extractSelectedText();

      if (selectedText && selectedText.length > 50) {
        // Personalize selected text
        setPersonalizationContent(selectedText);
        setPersonalizationContentType('selected');
        setPersonalizationWordCount(selectedText.split(' ').length);
        setShowPersonalizationModal(true);
      } else {
        // Use the same extractContent function for consistency
        const fallbackContent = extractContent();

        if (fallbackContent && fallbackContent.length >= 50) {
          const wordCount = fallbackContent.split(' ').length;
          console.log('[DEBUG] Using fallback content, length:', fallbackContent.length);
          setPersonalizationContent(fallbackContent);
          setPersonalizationContentType('page');
          setPersonalizationWordCount(wordCount);
          setShowPersonalizationModal(true);
        } else {
          showToast('Not enough content to personalize. Please select more text or choose a page with more content.');
        }
      }
    } catch (error) {
      // Try a simpler fallback extraction
      const fallbackContent = document.querySelector('.markdown')?.textContent ||
                              document.querySelector('article')?.textContent ||
                              document.querySelector('main')?.textContent ||
                              document.body.textContent;

      if (fallbackContent && fallbackContent.length > 100) {
        const words = fallbackContent.split(' ').filter(w => w.length > 0);
        if (words.length >= 50) {
          setPersonalizationContent(fallbackContent.substring(0, 2000)); // Limit to first 2000 chars
          setPersonalizationContentType('page');
          setPersonalizationWordCount(words.length);
          setShowPersonalizationModal(true);
          return;
        }
      }

      showToast('Failed to extract enough content for personalization. Please try selecting text instead.');
    }
  };

  
  return (
    <div className={`ai-features-bar glass-bar ${styles.aiFeaturesBar}`}>
      <div className={styles.header}>
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
        </svg>
        AI Features
      </div>
      
      <div className={styles.actionsWrapper}>
        <div className={styles.topButtons}>
          <button
            className={`button button--primary button--sm ${styles.featureBtn}`}
            onClick={handlePersonalize}
            disabled={isTranslating}
            title="Personalize this content for you"
          >
            <Sparkles size={16} />
            <span className={styles.btnText}>Personalize</span>
          </button>
          
          <button
            className={`button button--sm button--outline ${styles.featureBtn}`}
            onClick={handleTranslate}
            disabled={isTranslating || !translationEnabled}
          >
            {isTranslating ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span className={styles.btnText}>Translating...</span>
              </>
            ) : (
              <>
                <Globe size={16} />
                <span className={styles.btnText}>Translate to Urdu</span>
              </>
            )}
          </button>
        </div>

        <TextToSpeech className={styles.voiceBtn} />
        
        {!translationEnabled && (
          <div className={styles.disabledNotice}>
            ⚠️ Translation is disabled
          </div>
        )}
      </div>

      {/* Login Prompt Modal */}
      {showLoginModal && (
        <div className={styles.loginModalOverlay} onClick={() => {
          setShowLoginModal(false);
          setPendingPersonalization(false);
        }}>
          <div className={styles.loginModal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.loginModalHeader}>
              <h3>Login Required</h3>
              <button
                className={styles.closeButton}
                onClick={() => {
                  setShowLoginModal(false);
                  setPendingPersonalization(false);
                }}
              >
                ×
              </button>
            </div>
            <div className={styles.loginModalBody}>
              <div className={styles.loginIcon}>
                <Lock size={48} />
              </div>
              <p>
                Content personalization is available only to authenticated users.
                Please login to access this feature.
              </p>
              <div className={styles.loginModalActions}>
                <LoginButton
                  className="button button--primary"
                  onSuccess={() => {
                    console.log('Login success callback triggered');

                    // Clear any URL parameters that might cause redirects
                    if (window.location.search.includes('redirect') || window.location.search.includes('action')) {
                      const url = new URL(window.location.href);
                      url.searchParams.delete('redirect');
                      url.searchParams.delete('action');
                      window.history.replaceState({}, '', url.toString());
                    }

                    showToast('Successfully logged in! You can now personalize content.');

                    // The useEffect will handle the pending personalization
                    // when the auth state updates
                  }}
                  onError={(error: string) => {
                    setLoginError(error);
                    showToast(`Login failed: ${error}`, 'error');
                  }}
                >
                  Sign In
                </LoginButton>
                <button
                  className="button button--outline"
                  onClick={() => {
                    setShowLoginModal(false);
                    setPendingPersonalization(false);
                  }}
                >
                  Cancel
                </button>
              </div>

              {/* Show login error if any */}
              {loginError && (
                <div className={styles.loginErrorMessage}>
                  {loginError}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Personalization Modal */}
      <PersonalizationModal
        isOpen={showPersonalizationModal}
        onClose={() => {
          setShowPersonalizationModal(false);
          setPersonalizationContent('');
          setPersonalizationContentType('page');
          setPersonalizationWordCount(0);
        }}
        content={personalizationContent}
        contentType={personalizationContentType}
        wordCount={personalizationWordCount}
      />
    </div>
  );
}

// Toast helper function
function showToast(message: string) {
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
}