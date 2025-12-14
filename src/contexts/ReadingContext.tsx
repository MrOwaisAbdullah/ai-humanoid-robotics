import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { useUser } from './UserContext';

interface SectionProgress {
  sectionId: string;
  position: number; // 0-100 percentage
  completed: boolean;
  timeSpent: number; // minutes
  lastAccessed: string;
}

interface ReadingState {
  currentChapter: string | null;
  currentSection: string | null;
  progress: Record<string, SectionProgress[]>;
  isTracking: boolean;
  startTime: number | null;
  totalReadingTime: number;
}

type ReadingAction =
  | { type: 'SET_CHAPTER'; payload: string }
  | { type: 'SET_SECTION'; payload: string }
  | { type: 'SET_PROGRESS'; payload: Record<string, SectionProgress[]> }
  | { type: 'UPDATE_SECTION_PROGRESS'; payload: { chapterId: string; sectionId: string; position: number } }
  | { type: 'MARK_SECTION_COMPLETE'; payload: { chapterId: string; sectionId: string } }
  | { type: 'START_TRACKING' }
  | { type: 'STOP_TRACKING' }
  | { type: 'UPDATE_READING_TIME'; payload: number };

const initialState: ReadingState = {
  currentChapter: null,
  currentSection: null,
  progress: {},
  isTracking: false,
  startTime: null,
  totalReadingTime: 0,
};

const readingReducer = (state: ReadingState, action: ReadingAction): ReadingState => {
  switch (action.type) {
    case 'SET_CHAPTER':
      return {
        ...state,
        currentChapter: action.payload,
      };
    case 'SET_SECTION':
      return {
        ...state,
        currentSection: action.payload,
      };
    case 'SET_PROGRESS':
      return {
        ...state,
        progress: action.payload,
      };
    case 'UPDATE_SECTION_PROGRESS':
      const { chapterId, sectionId, position } = action.payload;
      const chapterProgress = state.progress[chapterId] || [];
      const sectionIndex = chapterProgress.findIndex(s => s.sectionId === sectionId);

      let updatedChapterProgress: SectionProgress[];
      if (sectionIndex >= 0) {
        updatedChapterProgress = [...chapterProgress];
        updatedChapterProgress[sectionIndex] = {
          ...updatedChapterProgress[sectionIndex],
          position,
          lastAccessed: new Date().toISOString(),
        };
      } else {
        updatedChapterProgress = [
          ...chapterProgress,
          {
            sectionId,
            position,
            completed: false,
            timeSpent: 0,
            lastAccessed: new Date().toISOString(),
          },
        ];
      }

      return {
        ...state,
        progress: {
          ...state.progress,
          [chapterId]: updatedChapterProgress,
        },
      };
    case 'MARK_SECTION_COMPLETE':
      const { chapterId: chId, sectionId: secId } = action.payload;
      const chProgress = state.progress[chId] || [];
      const secIndex = chProgress.findIndex(s => s.sectionId === secId);

      if (secIndex >= 0) {
        const updatedChProgress = [...chProgress];
        updatedChProgress[secIndex] = {
          ...updatedChProgress[secIndex],
          completed: true,
          position: 100,
          lastAccessed: new Date().toISOString(),
        };

        return {
          ...state,
          progress: {
            ...state.progress,
            [chId]: updatedChProgress,
          },
        };
      }
      return state;
    case 'START_TRACKING':
      return {
        ...state,
        isTracking: true,
        startTime: Date.now(),
      };
    case 'STOP_TRACKING':
      if (state.isTracking && state.startTime) {
        const sessionTime = Math.round((Date.now() - state.startTime) / 1000 / 60); // minutes
        return {
          ...state,
          isTracking: false,
          startTime: null,
          totalReadingTime: state.totalReadingTime + sessionTime,
        };
      }
      return {
        ...state,
        isTracking: false,
        startTime: null,
      };
    case 'UPDATE_READING_TIME':
      return {
        ...state,
        totalReadingTime: state.totalReadingTime + action.payload,
      };
    default:
      return state;
  }
};

interface ReadingContextType extends ReadingState {
  navigateToChapter: (chapterId: string) => void;
  navigateToSection: (chapterId: string, sectionId: string) => void;
  updateProgress: (position: number) => void;
  completeSection: () => void;
  startReading: () => void;
  stopReading: () => void;
  getChapterProgress: (chapterId: string) => number;
  isSectionCompleted: (chapterId: string, sectionId: string) => boolean;
}

const ReadingContext = createContext<ReadingContextType | undefined>(undefined);

export const useReading = () => {
  const context = useContext(ReadingContext);
  if (!context) {
    throw new Error('useReading must be used within a ReadingProvider');
  }
  return context;
};

interface ReadingProviderProps {
  children: ReactNode;
}

export const ReadingProvider: React.FC<ReadingProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(readingReducer, initialState);
  const { user, isAuthenticated } = useUser();

  // Load user progress when authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      // TODO: Load user's reading progress from API
      // const loadProgress = async () => {
      //   try {
      //     const progress = await progressService.getUserProgress();
      //     dispatch({ type: 'SET_PROGRESS', payload: progress });
      //   } catch (error) {
      //     console.error('Failed to load progress:', error);
      //   }
      // };
      // loadProgress();
    }
  }, [isAuthenticated, user]);

  // Auto-save progress when it changes
  useEffect(() => {
    if (isAuthenticated && state.currentChapter && state.progress[state.currentChapter]) {
      // TODO: Save progress to API
      // const saveProgress = async () => {
      //   try {
      //     await progressService.updateProgress(state.currentChapter, state.progress[state.currentChapter]);
      //   } catch (error) {
      //     console.error('Failed to save progress:', error);
      //   }
      // };
      //
      // const timeoutId = setTimeout(saveProgress, 2000); // Debounce saves
      // return () => clearTimeout(timeoutId);
    }
  }, [state.progress, state.currentChapter, isAuthenticated]);

  const navigateToChapter = (chapterId: string) => {
    dispatch({ type: 'SET_CHAPTER', payload: chapterId });
  };

  const navigateToSection = (chapterId: string, sectionId: string) => {
    dispatch({ type: 'SET_CHAPTER', payload: chapterId });
    dispatch({ type: 'SET_SECTION', payload: sectionId });
  };

  const updateProgress = (position: number) => {
    if (state.currentChapter && state.currentSection) {
      dispatch({
        type: 'UPDATE_SECTION_PROGRESS',
        payload: {
          chapterId: state.currentChapter,
          sectionId: state.currentSection,
          position,
        },
      });
    }
  };

  const completeSection = () => {
    if (state.currentChapter && state.currentSection) {
      dispatch({
        type: 'MARK_SECTION_COMPLETE',
        payload: {
          chapterId: state.currentChapter,
          sectionId: state.currentSection,
        },
      });
    }
  };

  const startReading = () => {
    dispatch({ type: 'START_TRACKING' });
  };

  const stopReading = () => {
    dispatch({ type: 'STOP_TRACKING' });
  };

  const getChapterProgress = (chapterId: string): number => {
    const chapterProgress = state.progress[chapterId] || [];
    if (chapterProgress.length === 0) return 0;

    const totalProgress = chapterProgress.reduce((sum, section) => sum + section.position, 0);
    return Math.round(totalProgress / chapterProgress.length);
  };

  const isSectionCompleted = (chapterId: string, sectionId: string): boolean => {
    const chapterProgress = state.progress[chapterId] || [];
    const section = chapterProgress.find(s => s.sectionId === sectionId);
    return section?.completed || false;
  };

  const value: ReadingContextType = {
    ...state,
    navigateToChapter,
    navigateToSection,
    updateProgress,
    completeSection,
    startReading,
    stopReading,
    getChapterProgress,
    isSectionCompleted,
  };

  return <ReadingContext.Provider value={value}>{children}</ReadingContext.Provider>;
};