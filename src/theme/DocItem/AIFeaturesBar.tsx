import React, { useState, useEffect } from 'react';
import { useFocusMode } from '../../contexts/FocusModeContext';
import { useLocalization } from '../../contexts/LocalizationContext';
import { useAuth } from '../../context/AuthContext';
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
  const [isPersonalizing, setIsPersonalizing] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [pendingPersonalization, setPendingPersonalization] = useState(false);
  const [showPersonalizationModal, setShowPersonalizationModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<'personalize' | 'translate'>('personalize');
  const [personalizationContent, setPersonalizationContent] = useState('');
  const [personalizationContentType, setPersonalizationContentType] = useState<'selected' | 'page'>('page');
  const [personalizationWordCount, setPersonalizationWordCount] = useState(0);
  const location = useLocation();

  // Listen for authentication state changes
  useEffect(() => {
    console.log('Auth state changed in AIFeaturesBar:', { isAuthenticated, user });

    // If user just became authenticated, check for pending actions
    if (isAuthenticated && user) {
      if (pendingAction === 'translate' && showLoginModal) {
        console.log('Processing pending translation after authentication');
        setShowLoginModal(false);
        setPendingAction('personalize'); // Reset to default
        // Trigger translation after a brief delay to avoid infinite loop
        setTimeout(() => {
          handleTranslate();
        }, 100);
      } else if (pendingPersonalization) {
        console.log('Processing pending personalization after authentication');
        setPendingPersonalization(false);
        setShowLoginModal(false);

        // Extract content and open personalization modal
        try {
          const selectedText = extractSelectedText();

          if (selectedText && selectedText.length > 0) {
            // No minimum content requirement for selected text
            setPersonalizationContent(selectedText);
            setPersonalizationContentType('selected');
            setPersonalizationWordCount(selectedText.split(' ').length);
            setShowPersonalizationModal(true);
            return;
          }

          // Use the same extractContent function for consistency
          const fallbackContent = extractContent();
          if (fallbackContent && fallbackContent.length > 0) {
            const wordCount = fallbackContent.split(' ').length;
            setPersonalizationContent(fallbackContent);
            setPersonalizationContentType('page');
            setPersonalizationWordCount(wordCount);
            setShowPersonalizationModal(true);
            return;
          }

          // Check if the page has mostly code
          const hasCode = fallbackContent && fallbackContent.includes('```');
          if (hasCode) {
            showToast('This page contains mainly code examples. Please select some explanatory text along with the code for better personalization.');
          } else {
            showToast('This page has limited content. Try selecting specific text or choosing a page with more detailed descriptions.');
          }
        } catch (error) {
          console.error('Content extraction failed:', error);
          showToast('Failed to extract content for personalization. Please try again.');
        }
      }
    }
  }, [isAuthenticated, user, pendingPersonalization, pendingAction, showLoginModal, translationEnabled]);

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

    // Check if user is authenticated
    if (!isAuthenticated) {
      setPendingAction('translate');
      setShowLoginModal(true);
      return;
    }

    if (!translationEnabled) {
            showToast('Translation is disabled. Please enable it in settings.');
      return;
    }

    // Extract content from the page
    const originalText = extractContent();
    console.log('Extracted text length:', originalText?.length);
    console.log('Extracted text preview:', originalText?.substring(0, 200));

    if (!originalText || originalText.trim().length === 0) {
      showToast('No content found to translate.');
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

  const handlePersonalize = async () => {
    // Check if user is authenticated using AuthContext
    if (!isAuthenticated) {
      setPendingAction('personalize');
      setPendingPersonalization(true);
      setShowLoginModal(true);
      return;
    }

    // Clear any previous login errors and pending state
    setLoginError(null);
    setPendingPersonalization(false);

    // Set loading state
    setIsPersonalizing(true);

    try {
      // Use the proper content extraction with filtering
      const extractedContent = extractContent();
      console.log('[DEBUG] handlePersonalize top-level extraction:', extractedContent?.length);

      if (extractedContent && extractedContent.length > 0) {
        // No minimum content score required - even a single word is fine
        const words = extractedContent.trim().split(/\s+/).filter(w => w.length > 0);
        console.log('[DEBUG] Using extractContent() method, cleaned length:', extractedContent.length, 'words:', words.length);
        setPersonalizationContent(extractedContent);
        setPersonalizationContentType('page');
        setPersonalizationWordCount(words.length);
        setShowPersonalizationModal(true);
        return;
      }

      // Extract content for personalization
      // First try to get selected text
      const selectedText = extractSelectedText();

      if (selectedText && selectedText.length > 0) {
        // No minimum content requirement for selected text
        setPersonalizationContent(selectedText);
        setPersonalizationContentType('selected');
        setPersonalizationWordCount(selectedText.split(' ').length);
        setShowPersonalizationModal(true);
        return;
      }

      // Use the same extractContent function for consistency
      const fallbackContent = extractContent();

      if (fallbackContent && fallbackContent.length > 0) {
        const wordCount = fallbackContent.split(' ').length;
        setPersonalizationContent(fallbackContent);
        setPersonalizationContentType('page');
        setPersonalizationWordCount(wordCount);
        setShowPersonalizationModal(true);
        return;
      }
      } catch (error) {
      console.error('Error in personalization:', error);
      showToast('Unable to extract content for personalization. Please select text manually.');
    } finally {
      // Always reset loading state
      setIsPersonalizing(false);
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
            disabled={isTranslating || isPersonalizing}
            title="Personalize this content for you"
          >
            {isPersonalizing ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span className={styles.btnText}>Personalizing...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span className={styles.btnText}>Personalize</span>
              </>
            )}
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
                {pendingAction === 'translate'
                  ? 'Translation is available only to authenticated users. Please login to translate content.'
                  : pendingPersonalization || pendingAction === 'personalize'
                    ? 'Content personalization is available only to authenticated users. Please login to access this feature.'
                    : 'This feature is available only to authenticated users. Please login to continue.'
                }
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

                    showToast(
                      pendingAction === 'translate'
                        ? 'Successfully logged in! You can now translate content.'
                        : 'Successfully logged in! You can now personalize content.'
                    );

                    // The useEffect will handle the pending personalization
                    // when the auth state updates
                  }}
                  onError={(error: string) => {
                    setLoginError(error);
                    showToast(`Login failed: ${error}`);
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
  toast.textContent = message;

  // Check if dark mode is active
  const isDarkTheme = document.documentElement.classList.contains('dark');

  // Use contrasting colors for better visibility
  if (isDarkTheme) {
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #1e293b;
      color: #f1f5f9;
      padding: 14px 20px;
      border-radius: 10px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
      z-index: 9999;
      animation: slideInUp 0.3s ease-out;
      border: 1px solid #334155;
      border-left: 4px solid #3b82f6;
      font-size: 14px;
      font-weight: 500;
      max-width: 400px;
      word-wrap: break-word;
    `;
  } else {
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #1e293b;
      color: #f1f5f9;
      padding: 14px 20px;
      border-radius: 10px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
      z-index: 9999;
      animation: slideInUp 0.3s ease-out;
      border: 1px solid #475569;
      border-left: 4px solid #3b82f6;
      font-size: 14px;
      font-weight: 500;
      max-width: 400px;
      word-wrap: break-word;
    `;
  }

  document.body.appendChild(toast);

  // Auto-remove after 5 seconds (increased from 3 seconds)
  setTimeout(() => {
    toast.style.animation = 'slideOutDown 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}