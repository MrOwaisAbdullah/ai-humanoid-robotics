/**
 * Unit tests for sessionStorage utility
 */

import { SessionStorage } from '../../../src/utils/sessionStorage';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

// Mock navigator properties
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock fingerprint generation
jest.mock('../../../src/utils/sessionStorage', () => {
  const originalModule = jest.requireActual('../../../src/utils/sessionStorage');
  return {
    ...originalModule,
    // Override fingerprint generation for predictable tests
    SessionStorage: class extends originalModule.SessionStorage {
      private mockFingerprint = 'test-fingerprint-123';

      protected getFingerprint(): string {
        return this.mockFingerprint;
      }

      protected createSessionId(): string {
        return 'test-session-' + Date.now();
      }
    },
  };
});

describe('SessionStorage', () => {
  let sessionStorage: SessionStorage;
  const SESSION_KEY = 'anonymous_session_id';

  beforeEach(() => {
    sessionStorage = new SessionStorage();
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('getOrCreateSessionId', () => {
    it('should return existing session ID from localStorage', () => {
      const existingSessionId = 'existing-session-123';
      localStorageMock.setItem(SESSION_KEY, existingSessionId);

      const result = sessionStorage.getOrCreateSessionId();

      expect(result.id).toBe(existingSessionId);
      expect(result.isNew).toBe(false);
      expect(result.source).toBe('localStorage');
      expect(localStorageMock.getItem).toHaveBeenCalledWith(SESSION_KEY);
    });

    it('should create new session ID when none exists', () => {
      const result = sessionStorage.getOrCreateSessionId();

      expect(result.id).toMatch(/^test-session-\d+$/);
      expect(result.isNew).toBe(true);
      expect(result.source).toBe('localStorage');
      expect(localStorageMock.setItem).toHaveBeenCalledWith(SESSION_KEY, result.id);
    });

    it('should use fingerprint fallback when localStorage fails', () => {
      // Mock localStorage.setItem to throw an error
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error('localStorage is full');
      });

      const result = sessionStorage.getOrCreateSessionId();

      expect(result.id).toMatch(/^test-session-\d+$/);
      expect(result.isNew).toBe(true);
      expect(result.source).toBe('fingerprint');
    });

    it('should return same session ID on subsequent calls', () => {
      const firstResult = sessionStorage.getOrCreateSessionId();
      const secondResult = sessionStorage.getOrCreateSessionId();

      expect(firstResult.id).toBe(secondResult.id);
      expect(firstResult.isNew).toBe(true);
      expect(secondResult.isNew).toBe(false);
    });
  });

  describe('getSessionId', () => {
    it('should return null when no session exists', () => {
      const sessionId = sessionStorage.getSessionId();
      expect(sessionId).toBeNull();
    });

    it('should return existing session ID', () => {
      const existingSessionId = 'existing-session-123';
      localStorageMock.setItem(SESSION_KEY, existingSessionId);

      const sessionId = sessionStorage.getSessionId();
      expect(sessionId).toBe(existingSessionId);
    });
  });

  describe('setSessionId', () => {
    it('should set session ID in localStorage', () => {
      const sessionId = 'new-session-123';
      const result = sessionStorage.setSessionId(sessionId);

      expect(result).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalledWith(SESSION_KEY, sessionId);
    });

    it('should return false when localStorage fails', () => {
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error('localStorage error');
      });

      const result = sessionStorage.setSessionId('session-123');
      expect(result).toBe(false);
    });
  });

  describe('removeSessionId', () => {
    it('should remove session ID from localStorage', () => {
      const sessionId = 'test-session-123';
      localStorageMock.setItem(SESSION_KEY, sessionId);

      sessionStorage.removeSessionId();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith(SESSION_KEY);
    });
  });

  describe('clear', () => {
    it('should clear all session storage data', () => {
      localStorageMock.setItem(SESSION_KEY, 'test-session');
      localStorageMock.setItem('another-key', 'another-value');

      sessionStorage.clear();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith(SESSION_KEY);
    });
  });

  describe('edge cases', () => {
    it('should handle empty localStorage gracefully', () => {
      localStorageMock.getItem.mockReturnValueOnce(null);

      const result = sessionStorage.getOrCreateSessionId();

      expect(result.id).toBeDefined();
      expect(result.isNew).toBe(true);
    });

    it('should handle invalid session ID in localStorage', () => {
      localStorageMock.setItem(SESSION_KEY, '');

      const result = sessionStorage.getOrCreateSessionId();

      expect(result.id).not.toBe('');
      expect(result.isNew).toBe(true);
    });

    it('should generate unique session IDs', () => {
      const session1 = new SessionStorage();
      const session2 = new SessionStorage();

      const id1 = session1.getOrCreateSessionId();
      const id2 = session2.getOrCreateSessionId();

      // IDs should be different due to different timestamps
      expect(id1.id).not.toBe(id2.id);
    });
  });
});