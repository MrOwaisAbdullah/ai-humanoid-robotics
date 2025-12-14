import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Volume2, VolumeX, Pause, Play } from 'lucide-react';

interface TextToSpeechProps {
  content?: string;
  className?: string;
}

export default function TextToSpeech({ content, className = '' }: TextToSpeechProps) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const speechRef = useRef<SpeechSynthesisUtterance | null>(null);
  const [speechSupported, setSpeechSupported] = useState(true);

  // Check if speech synthesis is supported
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setSpeechSupported(false);
    }
  }, []);

  // Extract readable content from the page
  const extractReadableContent = useCallback((): string => {
    // Get the main content area
    const articleElement = document.querySelector('article');
    if (!articleElement) return '';

    // Clone the element to avoid modifying the DOM
    const clonedElement = articleElement.cloneNode(true) as HTMLElement;

    // Remove elements that should not be read
    const elementsToRemove = [
      'nav', 'footer', 'header', 'aside',
      'button', 'input', 'select', 'textarea',
      '.pagination', '.breadcrumbs', '.navbar',
      '.theme-doc-footer', '.toolbar', '.toc',
      'table of contents', 'table-of-contents',
      '[role="navigation"]', '[role="banner"]',
      '[role="contentinfo"]', '[role="complementary"]',
      'pre', 'code', '.code-block', 'syntax-highlighter',
      '.math-equation', '.formula', '.citation',
      '.reference', '.footnote', '.endnote',
      '.sidebar', '.menu', '.dropdown'
    ];

    elementsToRemove.forEach(selector => {
      const elements = clonedElement.querySelectorAll(selector);
      elements.forEach(el => el.remove());
    });

    // Also remove elements with specific text content
    const allElements = clonedElement.querySelectorAll('*');
    allElements.forEach(el => {
      const text = el.textContent?.toLowerCase() || '';
      if (text.includes('table of contents') ||
          text.includes('edit this page') ||
          text.includes('last updated') ||
          text.includes('previous') ||
          text.includes('next') ||
          text.includes('skip to') ||
          text.includes('navigation') ||
          text.includes('share') ||
          text.includes('copy') ||
          text.includes('download')) {
        el.remove();
      }
    });

    // Get clean text content
    let textContent = clonedElement.textContent || '';

    // Clean up the text
    textContent = textContent
      .replace(/\s+/g, ' ') // Replace multiple whitespace with single space
      .replace(/\n\s*\n/g, '\n') // Replace multiple newlines with single newline
      .replace(/\[\d+\]/g, '') // Remove citation numbers like [1], [2]
      .replace(/\([^)]*\d+[^)]*\)/g, '') // Remove parentheses containing numbers
      .replace(/^\d+\.?\s*/gm, '') // Remove numbered list prefixes
      .replace(/^[a-zA-Z]\.?\s*/gm, '') // Remove lettered list prefixes
      .replace(/['"]\s*$/gm, '') // Remove trailing quotes
      .replace(/^[»«]\s*/gm, '') // Remove guillemets
      .trim();

    // Split into sentences and filter out very short ones
    const sentences = textContent.split(/[.!?]+/).filter(sentence => {
      const trimmed = sentence.trim();
      return trimmed.length > 10; // Only sentences with more than 10 characters
    });

    return sentences.join('. ') + '.';
  }, []);

  const speak = useCallback(() => {
    if (!speechSupported) {
      showToast('Text-to-speech is not supported in your browser');
      return;
    }

    const textToRead = content || extractReadableContent();

    if (!textToRead || textToRead.length < 50) {
      showToast('Not enough content to read');
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    setIsLoading(true);

    // Create utterance
    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;

    // Get voices and select a good one
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice =>
      voice.lang.includes('en') &&
      (voice.name.includes('Google') || voice.name.includes('Microsoft') || voice.name.includes('Amazon'))
    ) || voices.find(voice => voice.lang.includes('en')) || voices[0];

    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    // Event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
      setIsLoading(false);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      setIsLoading(false);
    };

    utterance.onerror = (event) => {
      console.error('Speech error:', event);
      setIsSpeaking(false);
      setIsPaused(false);
      setIsLoading(false);
      showToast('Failed to start text-to-speech');
    };

    utterance.onpause = () => {
      setIsPaused(true);
    };

    utterance.onresume = () => {
      setIsPaused(false);
    };

    // Save reference
    speechRef.current = utterance;

    // Start speaking
    window.speechSynthesis.speak(utterance);
  }, [content, extractReadableContent, speechSupported]);

  const stop = useCallback(() => {
    if (!speechSupported) return;

    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setIsLoading(false);
  }, [speechSupported]);

  const pauseResume = useCallback(() => {
    if (!speechSupported) return;

    if (isPaused) {
      window.speechSynthesis.resume();
    } else {
      window.speechSynthesis.pause();
    }
  }, [isPaused, speechSupported]);

  // Load voices when component mounts
  useEffect(() => {
    if (speechSupported) {
      window.speechSynthesis.getVoices();
      const handleVoicesChanged = () => {
        window.speechSynthesis.getVoices();
      };
      window.speechSynthesis.addEventListener('voiceschanged', handleVoicesChanged);
      return () => {
        window.speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged);
      };
    }
  }, [speechSupported]);

  if (!speechSupported) {
    return null;
  }

  return (
    <div className={`text-to-speech ${className}`}>
      {!isSpeaking ? (
        <button
          className="tts-button button button--secondary button--sm"
          onClick={speak}
          disabled={isLoading}
          title="Read content aloud"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          {isLoading ? (
            <div className="animate-spin" style={{ width: '16px', height: '16px' }}>
              <div
                style={{
                  border: '2px solid transparent',
                  borderTop: '2px solid currentColor',
                  borderRadius: '50%',
                  width: '100%',
                  height: '100%'
                }}
              />
            </div>
          ) : (
            <Volume2 size={16} />
          )}
          <span className="button-text-desktop">Read Aloud</span>
        </button>
      ) : (
        <div className="tts-controls" style={{
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          width: '100%',
          justifyContent: 'center',
          flexWrap: 'nowrap'
        }}>
          <button
            className="tts-button button button--secondary button--sm"
            onClick={pauseResume}
            title={isPaused ? "Resume reading" : "Pause reading"}
            style={{ flex: 0, padding: '8px', minWidth: 'auto', justifyContent: 'center' }}
          >
            {isPaused ? <Play size={16} /> : <Pause size={16} />}
          </button>
          <button
            className="tts-button button button--secondary button--sm"
            onClick={stop}
            title="Stop reading"
            style={{ flex: 0, padding: '8px', minWidth: 'auto', justifyContent: 'center' }}
          >
            <VolumeX size={16} />
          </button>
          <span className="tts-reading-indicator" style={{
            fontSize: '12px',
            color: 'var(--ifm-color-emphasis-600)',
            whiteSpace: 'nowrap',
            marginLeft: '8px'
          }}>
            Reading...
          </span>
        </div>
      )}
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