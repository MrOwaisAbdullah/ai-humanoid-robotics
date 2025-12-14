import React, { useState } from 'react';
import { useFocusMode } from '../../contexts/FocusModeContext';
import { useLocalization } from '../../contexts/LocalizationContext';
import { Loader2, Globe } from 'lucide-react';
import { useLocation } from '@docusaurus/router';
import TextToSpeech from '../../components/TTS/TextToSpeech';
import styles from './AIFeaturesBar.module.css';

export default function AIFeaturesBar() {
  const { showTranslation } = useFocusMode();
  const { translationEnabled, language } = useLocalization();
  const [isTranslating, setIsTranslating] = useState(false);
  const location = useLocation();

  // Only show on docs pages, not on other pages like blog, authentication, etc.
  if (!location.pathname.includes('/docs/') ||
      location.pathname.includes('assessments') ||
      location.pathname.includes('congratulations')) {
    return null;
  }

  const extractContent = (): string => {
    // Try multiple selectors to get the main content - more comprehensive list
    const selectors = [
      // Docusaurus specific
      'article',
      '.markdown',
      '.theme-doc-markdown',
      '.theme-doc-content',
      '.theme-doc-markdown-content',
      '[role="main"]',
      'main',
      // General content selectors
      '.content',
      '.page-content',
      '.doc-content',
      '.post-content',
      '#content',
      '.entry-content',
      // Fallbacks
      'body > div',
      '.container',
      '.wrapper',
      // Specific page types
      '.hero__subtitle',
      '.hero__description',
      '.section-title',
      'h1, h2, h3, h4, h5, h6',
      'p',
      'li'
    ];

    let bestContent = '';

    for (const selector of selectors) {
      try {
        const elements = document.querySelectorAll(selector);

        // For single selectors like 'article', 'main', take the whole element
        if (elements.length === 1 && ['article', 'main', '[role="main"]', '.theme-doc-markdown', '.theme-doc-content'].includes(selector)) {
          const element = elements[0];
          const textContent = getCleanTextFromElement(element);
          if (textContent && textContent.length > bestContent.length) {
            bestContent = textContent;
          }
        }
        // For multiple selectors (like 'p', 'h1', etc.), combine them
        else if (elements.length > 0) {
          const texts: string[] = [];
          elements.forEach(el => {
            const text = el.textContent?.trim();
            if (text && text.length > 5) { // Only substantial text
              texts.push(text);
            }
          });
          const combinedText = texts.join('\n');
          if (combinedText.length > bestContent.length) {
            bestContent = combinedText;
          }
        }
      } catch (error) {
        console.warn(`Selector ${selector} failed:`, error);
      }
    }

    // If still no content, try to get all text from body as last resort
    if (!bestContent || bestContent.length < 50) {
      const bodyText = document.body.textContent || '';
      bestContent = bodyText
        .replace(/\s+/g, ' ')
        .replace(/[\r\n]+/g, '\n')
        .trim();
    }

    // Clean up the final content
    if (bestContent) {
      const lines = bestContent.split('\n').filter(line => {
        const lowerLine = line.toLowerCase().trim();
        return !lowerLine.includes('previous') &&
               !lowerLine.includes('next') &&
               !lowerLine.includes('edit this page') &&
               !lowerLine.includes('last updated') &&
               !lowerLine.includes('skip to main content') &&
               !lowerLine.includes('navigation') &&
               line.length > 5; // Reduced minimum length
      });

      return lines.join('\n').trim();
    }

    return bestContent;
  };

  const getCleanTextFromElement = (element: Element): string => {
    // Remove script tags and other unwanted elements
    const clonedElement = element.cloneNode(true) as Element;
    const unwantedTags = clonedElement.querySelectorAll('script, style, nav, .pagination, .theme-doc-footer, .toolbar, .navbar, .footer, menu, button, .breadcrumbs');
    unwantedTags.forEach(tag => tag.remove());

    // Get clean text content
    let textContent = clonedElement.textContent || '';

    // Clean up whitespace
    textContent = textContent
      .replace(/\s+/g, ' ')
      .replace(/\n\s*\n/g, '\n')
      .trim();

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
    showToast('Personalization feature coming soon!');
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
          >
            <span style={{ fontSize: '16px' }}>✨</span>
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