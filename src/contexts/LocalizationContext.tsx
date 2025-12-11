import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { useUser } from './UserContext';
import { translationAPI, TranslationRequest, TranslationResponse, TranslationStreamChunk, PersonalizationSettings } from '../services/translationAPI';
type Language = 'en' | 'ur' | 'ur-roman';
type Direction = 'ltr' | 'rtl';
type TranslationStatus = 'idle' | 'loading' | 'success' | 'error';

interface LocalizationState {
  language: Language;
  direction: Direction;
  isRTL: boolean;
  // Translation features
  translationEnabled: boolean;
  translationStatus: TranslationStatus;
  translationError: string | null;
  isTranslationCached: boolean;
  cacheHitCount: number;
  cacheMissCount: number;
  // Personalization settings
  personalizationSettings: PersonalizationSettings;
  // Current translation
  currentTranslation: {
    originalText: string;
    translatedText: string;
    sourceLanguage: string;
    targetLanguage: string;
  } | null;
}

type LocalizationAction =
  | { type: 'SET_LANGUAGE'; payload: Language }
  | { type: 'SET_DIRECTION'; payload: Direction }
  | { type: 'TOGGLE_TRANSLATION'; payload?: boolean }
  | { type: 'SET_TRANSLATION_STATUS'; payload: TranslationStatus }
  | { type: 'SET_TRANSLATION_ERROR'; payload: string | null }
  | { type: 'SET_CACHED_TRANSLATION'; payload: boolean }
  | { type: 'INCREMENT_CACHE_HIT' }
  | { type: 'INCREMENT_CACHE_MISS' }
  | { type: 'SET_PERSONALIZATION_SETTINGS'; payload: PersonalizationSettings }
  | { type: 'SET_CURRENT_TRANSLATION'; payload: LocalizationState['currentTranslation'] }
  | { type: 'RESET_TRANSLATION_STATE' };

const languageDirections: Record<Language, Direction> = {
  en: 'ltr',
  ur: 'rtl',
  'ur-roman': 'ltr',
};

const defaultPersonalizationSettings: PersonalizationSettings = {
  preferredLanguage: 'en',
  autoDetectLanguage: true,
  showOriginalText: false,
  saveHistory: true,
  enableCaching: true,
};

const initialState: LocalizationState = {
  language: 'en',
  direction: 'ltr',
  isRTL: false,
  // Translation features
  translationEnabled: true,
  translationStatus: 'idle',
  translationError: null,
  isTranslationCached: false,
  cacheHitCount: 0,
  cacheMissCount: 0,
  personalizationSettings: defaultPersonalizationSettings,
  currentTranslation: null,
};

const localizationReducer = (state: LocalizationState, action: LocalizationAction): LocalizationState => {
  switch (action.type) {
    case 'SET_LANGUAGE':
      const direction = languageDirections[action.payload];
      return {
        ...state,
        language: action.payload,
        direction,
        isRTL: direction === 'rtl',
        // Reset translation when language changes
        translationStatus: 'idle',
        translationError: null,
        currentTranslation: null,
      };
    case 'SET_DIRECTION':
      return {
        ...state,
        direction: action.payload,
        isRTL: action.payload === 'rtl',
      };
    case 'TOGGLE_TRANSLATION':
      return {
        ...state,
        translationEnabled: action.payload !== undefined ? action.payload : !state.translationEnabled,
        translationStatus: action.payload !== undefined && !action.payload ? 'idle' : state.translationStatus,
      };
    case 'SET_TRANSLATION_STATUS':
      return {
        ...state,
        translationStatus: action.payload,
        translationError: action.payload === 'error' ? state.translationError : null,
      };
    case 'SET_TRANSLATION_ERROR':
      return {
        ...state,
        translationError: action.payload,
        translationStatus: action.payload ? 'error' : 'success',
      };
    case 'SET_CACHED_TRANSLATION':
      return {
        ...state,
        isTranslationCached: action.payload,
      };
    case 'INCREMENT_CACHE_HIT':
      return {
        ...state,
        cacheHitCount: state.cacheHitCount + 1,
      };
    case 'INCREMENT_CACHE_MISS':
      return {
        ...state,
        cacheMissCount: state.cacheMissCount + 1,
      };
    case 'SET_PERSONALIZATION_SETTINGS':
      return {
        ...state,
        personalizationSettings: { ...state.personalizationSettings, ...action.payload },
      };
    case 'SET_CURRENT_TRANSLATION':
      return {
        ...state,
        currentTranslation: action.payload,
      };
    case 'RESET_TRANSLATION_STATE':
      return {
        ...state,
        translationStatus: 'idle',
        translationError: null,
        isTranslationCached: false,
        currentTranslation: null,
      };
    default:
      return state;
  }
};

interface LocalizationContextType extends LocalizationState {
  setLanguage: (language: Language) => void;
  setDirection: (direction: Direction) => void;
  t: (key: string, options?: Record<string, string>) => string;
  formatText: (text: string) => string;
  isUrdu: () => boolean;
  // Translation methods
  toggleTranslation: (enabled?: boolean) => void;
  translateText: (text: string, sourceLanguage?: string, targetLanguage?: string) => Promise<TranslationResponse | null>;
  translateTextStream: (
    text: string,
    sourceLanguage?: string,
    targetLanguage?: string,
    onChunk?: (chunk: TranslationStreamChunk) => void
  ) => Promise<void>;
  clearTranslationCache: () => Promise<number>;
  updatePersonalizationSettings: (settings: Partial<PersonalizationSettings>) => Promise<void>;
  getCacheStatistics: () => { hitRate: number; hits: number; misses: number };
}

const LocalizationContext = createContext<LocalizationContextType | undefined>(undefined);

export const useLocalization = () => {
  const context = useContext(LocalizationContext);
  if (!context) {
    throw new Error('useLocalization must be used within a LocalizationProvider');
  }
  return context;
};

interface LocalizationProviderProps {
  children: ReactNode;
}

// Translation cache
const translations: Record<string, Record<string, string>> = {
  en: {
    'nav.home': 'Home',
    'nav.book': 'Book',
    'nav.bookmarks': 'Bookmarks',
    'nav.search': 'Search',
    'nav.dashboard': 'Dashboard',
    'bookmark.save': 'Save Bookmark',
    'bookmark.saved': 'Bookmark Saved',
    'bookmark.remove': 'Remove Bookmark',
    'progress.resume': 'Resume Reading',
    'progress.complete': 'Mark as Complete',
    'search.placeholder': 'Search content...',
    'search.noResults': 'No results found',
    'settings.language': 'Language',
    'settings.theme': 'Theme',
    'settings.fontSize': 'Font Size',
  },
  ur: {
    'nav.home': 'گھر',
    'nav.book': 'کتاب',
    'nav.bookmarks': 'بک مارکس',
    'nav.search': 'تلاش کریں',
    'nav.dashboard': 'ڈیش بورڈ',
    'bookmark.save': 'بک مارک محفوظ کریں',
    'bookmark.saved': 'بک مارک محفوظ ہو گیا',
    'bookmark.remove': 'بک مارک ہٹائیں',
    'progress.resume': 'پڑھنا جاری رکھیں',
    'progress.complete': 'مکمل طور پر نشان زد کریں',
    'search.placeholder': 'مواد تلاش کریں...',
    'search.noResults': 'کوئی نتیجہ نہیں ملا',
    'settings.language': 'زبان',
    'settings.theme': 'تھیم',
    'settings.fontSize': 'فونٹ سائز',
  },
  'ur-roman': {
    'nav.home': 'Ghar',
    'nav.book': 'Kitab',
    'nav.bookmarks': 'Bookmarks',
    'nav.search': 'Talash Karein',
    'nav.dashboard': 'Dashboard',
    'bookmark.save': 'Bookmark Save Karein',
    'bookmark.saved': 'Bookmark Save Ho Gaya',
    'bookmark.remove': 'Bookmark Hatayein',
    'progress.resume': 'Parhna Jari Rakhein',
    'progress.complete': 'Mukammal Tore Par Nishan Lagayein',
    'search.placeholder': 'Mawad Talash Karein...',
    'search.noResults': 'Koi Nateeja Nahi Mila',
    'settings.language': 'Zabaan',
    'settings.theme': 'Theme',
    'settings.fontSize': 'Font Size',
  },
};

export const LocalizationProvider: React.FC<LocalizationProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(localizationReducer, initialState);
  const { user, isAuthenticated } = useUser();

  // Load user's language preference and translation settings
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        // Load language preference
        const savedLanguage = localStorage.getItem('language') as Language;
        if (savedLanguage && ['en', 'ur', 'ur-roman'].includes(savedLanguage)) {
          dispatch({ type: 'SET_LANGUAGE', payload: savedLanguage });
        }

        // Load translation settings - always enable by default
        const savedTranslationEnabled = localStorage.getItem('translationEnabled');
        const translationEnabled = savedTranslationEnabled === 'true' || savedTranslationEnabled === null;
        dispatch({ type: 'TOGGLE_TRANSLATION', payload: true }); // Force enable translation

        // If it was disabled before, update localStorage
        if (!translationEnabled) {
          localStorage.setItem('translationEnabled', 'true');
        }

        // Load personalization settings if authenticated
        if (isAuthenticated && user) {
          const personalizationSettings = await translationAPI().getPersonalizationSettings();
          dispatch({ type: 'SET_PERSONALIZATION_SETTINGS', payload: personalizationSettings });

          // Set preferred language if different from current
          if (personalizationSettings.preferredLanguage !== state.language) {
            dispatch({ type: 'SET_LANGUAGE', payload: personalizationSettings.preferredLanguage as Language });
          }
        }
      } catch (error) {
        console.error('Failed to load preferences:', error);
      }
    };

    loadPreferences();
  }, [isAuthenticated, user, state.language]);

  // Save language preference and update document
  useEffect(() => {
    localStorage.setItem('language', state.language);
    document.documentElement.lang = state.language;
    document.documentElement.dir = state.direction;
  }, [state.language, state.direction]);

  // Save translation settings
  useEffect(() => {
    localStorage.setItem('translationEnabled', state.translationEnabled.toString());
  }, [state.translationEnabled]);

  const setLanguage = (language: Language) => {
    dispatch({ type: 'SET_LANGUAGE', payload: language });

    // Save personalization settings if authenticated
    if (isAuthenticated) {
      updatePersonalizationSettings({ preferredLanguage: language });
    }
  };

  const setDirection = (direction: Direction) => {
    dispatch({ type: 'SET_DIRECTION', payload: direction });
  };

  // Translation methods
  const toggleTranslation = (enabled?: boolean) => {
    dispatch({ type: 'TOGGLE_TRANSLATION', payload: enabled });
  };

  const translateText = async (
    text: string,
    sourceLanguage?: string,
    targetLanguage?: string
  ): Promise<TranslationResponse | null> => {
    if (!state.translationEnabled) {
      return null;
    }

    dispatch({ type: 'SET_TRANSLATION_STATUS', payload: 'loading' });
    dispatch({ type: 'SET_TRANSLATION_ERROR', payload: null });

    try {
      const sourceLang = sourceLanguage || 'en';
      const targetLang = targetLanguage || state.language;

      const request: TranslationRequest = {
        text,
        sourceLanguage: sourceLang,
        targetLanguage: targetLang,
        preferCache: state.personalizationSettings.enableCaching,
        userId: user?.id,
      };

      const response = await translationAPI().translate(request);

      if (response && typeof response !== 'object' || !('id' in response)) {
        // Handle streaming response
        return null;
      }

      // Update state with translation
      dispatch({ type: 'SET_CURRENT_TRANSLATION', payload: {
        originalText: text,
        translatedText: response.translatedText,
        sourceLanguage: response.sourceLanguage,
        targetLanguage: response.targetLanguage,
      } });

      dispatch({ type: 'SET_TRANSLATION_STATUS', payload: 'success' });
      dispatch({ type: 'SET_CACHED_TRANSLATION', payload: response.isCached });

      if (response.isCached) {
        dispatch({ type: 'INCREMENT_CACHE_HIT' });
      } else {
        dispatch({ type: 'INCREMENT_CACHE_MISS' });
      }

      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Translation failed';
      dispatch({ type: 'SET_TRANSLATION_ERROR', payload: errorMessage });
      dispatch({ type: 'SET_TRANSLATION_STATUS', payload: 'error' });
      return null;
    }
  };

  const translateTextStream = async (
    text: string,
    sourceLanguage?: string,
    targetLanguage?: string,
    onChunk?: (chunk: TranslationStreamChunk) => void
  ): Promise<void> => {
    
    if (!state.translationEnabled) {
            return;
    }

    dispatch({ type: 'SET_TRANSLATION_STATUS', payload: 'loading' });
    dispatch({ type: 'SET_TRANSLATION_ERROR', payload: null });

    try {
      const sourceLang = sourceLanguage || 'en';
      const targetLang = targetLanguage || state.language;

      const request: TranslationRequest = {
        text,
        sourceLanguage: sourceLang,
        targetLanguage: targetLang,
        preferCache: false, // Don't use cache for streaming
        stream: true,
        userId: user?.id,
      };

      const streamResponse = await translationAPI().translate(request);

      if (typeof streamResponse === 'object' && 'id' in streamResponse) {
        // Not a streaming response
        return;
      }

      // Process stream
      let fullTranslation = '';
      for await (const chunk of streamResponse as AsyncIterable<TranslationStreamChunk>) {
        if (onChunk) {
          onChunk(chunk);
        }

        if (chunk.type === 'chunk' && chunk.content) {
          fullTranslation += chunk.content;
        } else if (chunk.type === 'end') {
          dispatch({ type: 'SET_TRANSLATION_STATUS', payload: 'success' });
          dispatch({ type: 'SET_CURRENT_TRANSLATION', payload: {
            originalText: text,
            translatedText: fullTranslation,
            sourceLanguage: sourceLang,
            targetLanguage: targetLang,
          } });
          dispatch({ type: 'SET_CACHED_TRANSLATION', payload: chunk.metadata?.cached || false });
        } else if (chunk.type === 'error') {
          dispatch({ type: 'SET_TRANSLATION_ERROR', payload: chunk.error || 'Stream error' });
          dispatch({ type: 'SET_TRANSLATION_STATUS', payload: 'error' });
        }
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Stream translation failed';
      dispatch({ type: 'SET_TRANSLATION_ERROR', payload: errorMessage });
      dispatch({ type: 'SET_TRANSLATION_STATUS', payload: 'error' });
    }
  };

  const clearTranslationCache = async (): Promise<number> => {
    try {
      const cleared = await translationAPI().clearCache();
      return cleared;
    } catch (error) {
      console.error('Failed to clear translation cache:', error);
      return 0;
    }
  };

  const updatePersonalizationSettings = async (settings: Partial<PersonalizationSettings>): Promise<void> => {
    try {
      if (isAuthenticated && user) {
        const updatedSettings = await translationAPI().updatePersonalizationSettings(settings);
        dispatch({ type: 'SET_PERSONALIZATION_SETTINGS', payload: updatedSettings });
      } else {
        // Update local state even if not authenticated
        dispatch({ type: 'SET_PERSONALIZATION_SETTINGS', payload: settings });
      }
    } catch (error) {
      console.error('Failed to update personalization settings:', error);
    }
  };

  const getCacheStatistics = () => {
    const totalRequests = state.cacheHitCount + state.cacheMissCount;
    const hitRate = totalRequests > 0 ? (state.cacheHitCount / totalRequests) * 100 : 0;

    return {
      hitRate: Math.round(hitRate * 100) / 100,
      hits: state.cacheHitCount,
      misses: state.cacheMissCount,
    };
  };

  const t = (key: string, options?: Record<string, string>): string => {
    let translation = translations[state.language][key] || translations['en'][key] || key;

    // Simple interpolation for options
    if (options) {
      Object.entries(options).forEach(([placeholder, value]) => {
        translation = translation.replace(`{{${placeholder}}}`, value);
      });
    }

    return translation;
  };

  // Urdu transliteration map for technical terms
  const transliterationMap: Record<string, string> = {
    'technology': 'ٹیکنالوجی',
    'artificial intelligence': 'مصنوعی ذہانت',
    'robot': 'روبوٹ',
    'algorithm': 'الگورتھم',
    'data': 'ڈیٹا',
    'database': 'ڈیٹا بیس',
    'computer': 'کمپیوٹر',
    'software': 'سافٹ ویئر',
    'hardware': 'ہارڈ ویئر',
    'network': 'نیٹ ورک',
    'security': 'سیکوریٹی',
    'programming': 'پروگرامنگ',
    'code': 'کوڈ',
    'function': 'فنکشن',
    'variable': 'متغیر',
    'array': 'اری',
    'object': 'آبجیکٹ',
    'class': 'کلاس',
    'method': 'میٹڈ',
    'api': 'اے پی آئی',
    'framework': 'فریم ورک',
    'library': 'لائبریری',
    'frontend': 'فرنٹ اینڈ',
    'backend': 'بیک اینڈ',
    'server': 'سرور',
    'client': 'کلائنٹ',
    'response': 'ریسپانس',
    'request': 'ریسپانس',
    'authentication': '_authentication',
    'authorization': 'آٹارائزیشن',
    'token': 'ٹوکن',
    'session': 'سیشن',
    'cookie': 'کوکی',
    'cache': 'کیش',
    'deployment': 'ڈپلائیمنٹ',
    'testing': 'ٹیسٹنگ',
    'debugging': 'ڈیبگنگ',
    'version control': 'ورژن کنٹرول',
    'git': 'گٹ',
    'github': 'گٹ ہب',
    'repository': 'ریپازٹری',
    'branch': 'برانچ',
    'merge': 'مرج',
    'commit': 'کمٹ',
    'pull request': 'پل ریکوئسٹ',
  };

  const formatText = (text: string): string => {
    if (state.language === 'ur') {
      // Transliterate technical terms while keeping Urdu script
      let formattedText = text;
      Object.entries(transliterationMap).forEach(([english, urdu]) => {
        const regex = new RegExp(`\\b${english}\\b`, 'gi');
        formattedText = formattedText.replace(regex, urdu);
      });
      return formattedText;
    }
    return text;
  };

  const isUrdu = (): boolean => {
    return state.language === 'ur';
  };

  const value: LocalizationContextType = {
    ...state,
    setLanguage,
    setDirection,
    t,
    formatText,
    isUrdu,
    // Translation methods
    toggleTranslation,
    translateText,
    translateTextStream,
    clearTranslationCache,
    updatePersonalizationSettings,
    getCacheStatistics,
  };

  return <LocalizationContext.Provider value={value}>{children}</LocalizationContext.Provider>;
};