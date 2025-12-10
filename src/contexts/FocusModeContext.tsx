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
    sourceLanguage?: string;
    targetLanguage?: string;
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
      sourceLanguage?: string;
      targetLanguage?: string;
    }
  ) => {
    const {
      pretranslatedText,
      sourceLanguage = 'en',
      targetLanguage = language
    } = options || {};

    // Set initial state
    setFocusMode({
      isVisible: true,
      originalContent: originalText,
      translatedContent: pretranslatedText || '',
      isLoading: !pretranslatedText,
      error: null,
      progress: 0
    });

    document.body.classList.add('focus-mode-active');

    // If we don't have pretranslated text, translate it
    if (!pretranslatedText) {
      try {
        let accumulatedTranslation = '';
        let totalChars = originalText.length;

        await translateTextStream(
          originalText,
          sourceLanguage,
          targetLanguage,
          (chunk) => {
            if (chunk.type === 'start') {
              setFocusMode(prev => ({ ...prev, progress: 0 }));
            } else if (chunk.type === 'chunk' && chunk.content) {
              accumulatedTranslation += chunk.content;
              const progress = Math.min((accumulatedTranslation.length / totalChars) * 100, 95);
              setFocusMode(prev => ({
                ...prev,
                translatedContent: accumulatedTranslation,
                progress
              }));
            } else if (chunk.type === 'end') {
              setFocusMode(prev => ({
                ...prev,
                translatedContent: accumulatedTranslation,
                isLoading: false,
                progress: 100,
                translationId: chunk.translationId
              }));
            } else if (chunk.type === 'error') {
              setFocusMode(prev => ({
                ...prev,
                isLoading: false,
                error: chunk.error || 'Translation failed',
                progress: 0
              }));
            }
          }
        );
      } catch (error: any) {
        setFocusMode(prev => ({
          ...prev,
          isLoading: false,
          error: error.message || 'Translation failed',
          progress: 0
        }));
      }
    } else {
      // We have pretranslated text, mark as complete
      setFocusMode(prev => ({
        ...prev,
        isLoading: false,
        progress: 100
      }));
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

      await translationAPI.submitFeedback(request);
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

      await showTranslation(focusMode.originalContent, {
        sourceLanguage: 'en',
        targetLanguage: language
      });
    } catch (error: any) {
      setFocusMode(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Translation failed',
        progress: 0
      }));
    }
  }, [focusMode.originalContent, language, showTranslation]);

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