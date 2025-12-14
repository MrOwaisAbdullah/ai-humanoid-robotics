/**
 * Session storage utility for managing anonymous sessions
 * with localStorage and fingerprint fallback
 */

export class SessionStorage {
  private readonly STORAGE_KEY = 'anonymous_session_id';

  /**
   * Store session ID in localStorage
   */
  setSessionId(id: string): boolean {
    try {
      localStorage.setItem(this.STORAGE_KEY, id);
      return true;
    } catch (error) {
      console.warn('Failed to store session ID in localStorage:', error);
      return false;
    }
  }

  /**
   * Get session ID from localStorage
   */
  getSessionId(): string | null {
    try {
      return localStorage.getItem(this.STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to retrieve session ID from localStorage:', error);
      return null;
    }
  }

  /**
   * Remove session ID from localStorage
   */
  clearSessionId(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to clear session ID from localStorage:', error);
    }
  }

  /**
   * Generate a fingerprint based on browser characteristics
   * Used as fallback when localStorage is unavailable
   */
  getFingerprint(): string {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      // Basic browser fingerprint
      const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        new Date().getTimezoneOffset(),
        navigator.hardwareConcurrency || 'unknown',
        navigator.platform
      ].join('|');

      // Add canvas fingerprint if available
      if (ctx) {
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('fingerprint', 2, 2);
        const canvasFingerprint = canvas.toDataURL().slice(-50);
        return btoa(fingerprint + '|' + canvasFingerprint)
          .replace(/[^a-zA-Z0-9]/g, '')
          .substring(0, 32);
      }

      return btoa(fingerprint)
        .replace(/[^a-zA-Z0-9]/g, '')
        .substring(0, 32);
    } catch (error) {
      console.warn('Failed to generate fingerprint:', error);
      // Fallback to simple random ID
      return Math.random().toString(36).substring(7) + Date.now().toString(36);
    }
  }

  /**
   * Create a new anonymous session ID
   */
  createSessionId(): string {
    return 'anon_' + Math.random().toString(36).substring(7) + Date.now().toString(36);
  }

  /**
   * Get or create a session ID with fallback logic
   */
  getOrCreateSessionId(): { id: string; isNew: boolean; source: 'localStorage' | 'fingerprint' | 'created' } {
    // Try localStorage first
    let sessionId = this.getSessionId();
    if (sessionId) {
      return { id: sessionId, isNew: false, source: 'localStorage' };
    }

    // Try to recover using fingerprint
    const fingerprint = this.getFingerprint();

    // In a real implementation, you might query the backend
    // with the fingerprint to find existing sessions
    // For now, create a new session

    sessionId = this.createSessionId();

    // Try to store in localStorage for next time
    const stored = this.setSessionId(sessionId);

    return {
      id: sessionId,
      isNew: true,
      source: stored ? 'localStorage' : 'fingerprint'
    };
  }
}

// Export singleton instance
export const sessionStorage = new SessionStorage();