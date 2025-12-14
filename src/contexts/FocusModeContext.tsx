import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useLocalization } from './LocalizationContext';
import { translationAPI, TranslationFeedbackRequest } from '../services/translationAPI';

interface FocusModeState {
  isVisible: boolean;
  originalContent: string;
  translatedContent: string;
  isLoading: boolean;
  error: string | null;
  translationId?: number;
  progress: number;
}

interface FocusModeContextType extends FocusModeState {
  showTranslation: (originalText: string, options?: {
    pretranslatedText?: string;
  }) => Promise<void>;
  closeFocusMode: () => void;
  submitFeedback: (translationId: number, rating: 1 | -1, comment?: string) => Promise<void>;
  retryTranslation: () => Promise<void>;
}

const FocusModeContext = createContext<FocusModeContextType | undefined>(undefined);

export const useFocusMode = () => {
  const context = useContext(FocusModeContext);
  if (!context) {
    throw new Error('useFocusMode must be used within a FocusModeProvider');
  }
  return context;
};

interface FocusModeProviderProps {
  children: ReactNode;
}

export const FocusModeProvider: React.FC<FocusModeProviderProps> = ({ children }) => {
  const { translateTextStream, language } = useLocalization();
  const [focusMode, setFocusMode] = useState<FocusModeState>({
    isVisible: false,
    originalContent: '',
    translatedContent: '',
    isLoading: false,
    error: null,
    progress: 0
  });

  const resetState = useCallback(() => {
    setFocusMode({
      isVisible: false,
      originalContent: '',
      translatedContent: '',
      isLoading: false,
      error: null,
      progress: 0
    });
    document.body.classList.remove('focus-mode-active');
  }, []);

  const showTranslation = useCallback(async (
    originalText: string,
    options?: {
      pretranslatedText?: string;
    }
  ) => {
    const {
      pretranslatedText
    } = options || {};

    // If we don't have pretranslated text, translate it first
    if (!pretranslatedText) {
      try {
        let accumulatedTranslation = '';
        let totalChars = originalText.length;
        let translationSuccess = false;
        let isFromCache = false;

        await translateTextStream(
          originalText,
          undefined,
          undefined,
          (chunk) => {
            if (chunk.type === 'start') {
              // Show UI with loader
              setFocusMode({
                isVisible: true, // Show UI immediately
                originalContent: originalText,
                translatedContent: '',
                isLoading: true,
                error: null,
                progress: 0
              });
              document.body.classList.add('focus-mode-active');
            } else if (chunk.type === 'chunk' && chunk.content) {
              // If cached, show the full translation immediately
              if (chunk.cached) {
                isFromCache = true;
                accumulatedTranslation = chunk.content;
                setFocusMode({
                  isVisible: true,
                  originalContent: originalText,
                  translatedContent: accumulatedTranslation,
                  isLoading: false,
                  error: null,
                  progress: 100
                });
              } else {
                accumulatedTranslation += chunk.content;
                const progress = Math.min((accumulatedTranslation.length / totalChars) * 100, 95);
                // Update with translated content during streaming
                setFocusMode(prev => ({
                  ...prev,
                  translatedContent: accumulatedTranslation,
                  progress
                }));
              }
            } else if (chunk.type === 'end') {
              if (!isFromCache) {
                translationSuccess = true;
                // Translation successful, show final state
                setFocusMode({
                  isVisible: true,
                  originalContent: originalText,
                  translatedContent: accumulatedTranslation,
                  isLoading: false,
                  error: null,
                  progress: 100,
                  translationId: chunk.translationId
                });
              }
            } else if (chunk.type === 'error') {
              // Translation failed, show error
              setFocusMode({
                isVisible: true,
                originalContent: '',
                translatedContent: '',
                isLoading: false,
                error: chunk.error || 'Translation failed',
                progress: 0
              });
              document.body.classList.remove('focus-mode-active');
            }
          }
        );

        // Translation completed through the stream handler
        // No need for additional fallback logic
      } catch (error: any) {
        // Translation failed, show error
        setFocusMode({
          isVisible: true,
          originalContent: '',
          translatedContent: '',
          isLoading: false,
          error: error.message || 'Translation failed',
          progress: 0
        });
        document.body.classList.add('focus-mode-active');
      }
    } else {
      // We have pretranslated text, show the UI immediately
      setFocusMode({
        isVisible: true,
        originalContent: originalText,
        translatedContent: pretranslatedText,
        isLoading: false,
        error: null,
        progress: 100
      });
      document.body.classList.add('focus-mode-active');
    }
  }, [translateTextStream, language]);

  const closeFocusMode = useCallback(() => {
    resetState();
  }, [resetState]);

  const submitFeedback = useCallback(async (
    translationId: number,
    rating: 1 | -1,
    comment?: string
  ) => {
    try {
      const request: TranslationFeedbackRequest = {
        translationId,
        rating,
        comment
      };

      await translationAPI().submitFeedback(request);
    } catch (error: any) {
      throw new Error(error.message || 'Failed to submit feedback');
    }
  }, []);

  const retryTranslation = useCallback(async () => {
    if (!focusMode.originalContent) return;

    try {
      setFocusMode(prev => ({
        ...prev,
        isLoading: true,
        error: null,
        progress: 0,
        translatedContent: ''
      }));

      await showTranslation(focusMode.originalContent, {});
    } catch (error: any) {
      setFocusMode(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Translation failed',
        progress: 0
      }));
    }
  }, [focusMode.originalContent, showTranslation]);

  const value: FocusModeContextType = {
    ...focusMode,
    showTranslation,
    closeFocusMode,
    submitFeedback,
    retryTranslation
  };

  return (
    <FocusModeContext.Provider value={value}>
      {children}
    </FocusModeContext.Provider>
  );
};