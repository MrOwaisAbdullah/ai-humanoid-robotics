/**
 * Local storage service for offline data synchronization.
 *
 * Handles caching of bookmarks and reading progress for offline access.
 */

import { ReadingProgress } from '../types/progress';
import { Bookmark } from '../types/bookmark';

export interface StorageKeys {
  BOOKMARKS: 'offline_bookmarks';
  READING_PROGRESS: 'offline_reading_progress';
  USER_PREFERENCES: 'offline_user_preferences';
  LAST_SYNC: 'last_sync_timestamp';
  PENDING_ACTIONS: 'pending_sync_actions';
}

export interface PendingAction {
  id: string;
  type: 'create' | 'update' | 'delete';
  resource: 'bookmark' | 'progress' | 'preference';
  data: any;
  timestamp: number;
}

export interface SyncStatus {
  isOnline: boolean;
  lastSync: number | null;
  pendingActions: number;
  hasUnsyncedChanges: boolean;
}

const KEYS: StorageKeys = {
  BOOKMARKS: 'offline_bookmarks',
  READING_PROGRESS: 'offline_reading_progress',
  USER_PREFERENCES: 'offline_user_preferences',
  LAST_SYNC: 'last_sync_timestamp',
  PENDING_ACTIONS: 'pending_sync_actions',
} as const;

class StorageService {
  private static instance: StorageService;
  private storage: Storage;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  private constructor() {
    this.storage = window.localStorage;
    this.setupOnlineStatusListener();
  }

  public static getInstance(): StorageService {
    if (!StorageService.instance) {
      StorageService.instance = new StorageService();
    }
    return StorageService.instance;
  }

  private setupOnlineStatusListener(): void {
    window.addEventListener('online', () => {
      this.notifyListeners('onlineStatus', true);
    });

    window.addEventListener('offline', () => {
      this.notifyListeners('onlineStatus', false);
    });
  }

  // Generic storage methods
  public setItem<T>(key: string, data: T): void {
    try {
      const serialized = JSON.stringify({
        data,
        timestamp: Date.now(),
      });
      this.storage.setItem(key, serialized);
      this.notifyListeners(key, data);
    } catch (error) {
      console.error(`Failed to save ${key} to storage:`, error);
      // If quota exceeded, try to clear old data
      this.handleStorageQuotaExceeded(key);
    }
  }

  public getItem<T>(key: string, maxAge?: number): T | null {
    try {
      const item = this.storage.getItem(key);
      if (!item) return null;

      const { data, timestamp } = JSON.parse(item);

      // Check if data is too old
      if (maxAge && Date.now() - timestamp > maxAge) {
        this.removeItem(key);
        return null;
      }

      return data;
    } catch (error) {
      console.error(`Failed to retrieve ${key} from storage:`, error);
      return null;
    }
  }

  public removeItem(key: string): void {
    this.storage.removeItem(key);
    this.notifyListeners(key, null);
  }

  public clear(): void {
    Object.values(KEYS).forEach(key => this.removeItem(key));
  }

  // Bookmark storage methods
  public saveBookmarks(bookmarks: Bookmark[]): void {
    this.setItem(KEYS.BOOKMARKS, bookmarks);
  }

  public getBookmarks(): Bookmark[] {
    return this.getItem<Bookmark[]>(KEYS.BOOKMARKS) || [];
  }

  public addBookmark(bookmark: Bookmark): void {
    const bookmarks = this.getBookmarks();
    const index = bookmarks.findIndex(b => b.id === bookmark.id);

    if (index >= 0) {
      bookmarks[index] = bookmark;
    } else {
      bookmarks.push(bookmark);
    }

    this.saveBookmarks(bookmarks);
  }

  public removeBookmark(bookmarkId: string): void {
    const bookmarks = this.getBookmarks();
    const filtered = bookmarks.filter(b => b.id !== bookmarkId);
    this.saveBookmarks(filtered);
  }

  // Reading progress storage methods
  public saveReadingProgress(progress: Record<string, ReadingProgress[]>): void {
    this.setItem(KEYS.READING_PROGRESS, progress);
  }

  public getReadingProgress(): Record<string, ReadingProgress[]> {
    return this.getItem<Record<string, ReadingProgress[]>>(KEYS.READING_PROGRESS) || {};
  }

  public updateSectionProgress(
    chapterId: string,
    sectionId: string,
    updates: Partial<ReadingProgress>
  ): void {
    const progress = this.getReadingProgress();
    const chapterProgress = progress[chapterId] || [];
    const index = chapterProgress.findIndex(p => p.sectionId === sectionId);

    if (index >= 0) {
      chapterProgress[index] = { ...chapterProgress[index], ...updates };
    } else {
      chapterProgress.push({
        id: `${sectionId}_${Date.now()}`,
        user_id: 'offline',
        chapter_id: chapterId,
        section_id: sectionId,
        position: 0,
        completed: false,
        time_spent: 0,
        last_accessed: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        ...updates,
      } as ReadingProgress);
    }

    progress[chapterId] = chapterProgress;
    this.saveReadingProgress(progress);
  }

  // Pending actions for sync
  public addPendingAction(action: Omit<PendingAction, 'id' | 'timestamp'>): void {
    const actions = this.getPendingActions();
    const newAction: PendingAction = {
      ...action,
      id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
    };

    actions.push(newAction);
    this.setItem(KEYS.PENDING_ACTIONS, actions);
  }

  public getPendingActions(): PendingAction[] {
    return this.getItem<PendingAction[]>(KEYS.PENDING_ACTIONS) || [];
  }

  public removePendingAction(actionId: string): void {
    const actions = this.getPendingActions();
    const filtered = actions.filter(a => a.id !== actionId);
    this.setItem(KEYS.PENDING_ACTIONS, filtered);
  }

  public clearPendingActions(): void {
    this.removeItem(KEYS.PENDING_ACTIONS);
  }

  // Sync status
  public getLastSync(): number | null {
    return this.getItem<number>(KEYS.LAST_SYNC);
  }

  public setLastSync(): void {
    this.setItem(KEYS.LAST_SYNC, Date.now());
  }

  public getSyncStatus(): SyncStatus {
    const pendingActions = this.getPendingActions();
    return {
      isOnline: navigator.onLine,
      lastSync: this.getLastSync(),
      pendingActions: pendingActions.length,
      hasUnsyncedChanges: pendingActions.length > 0,
    };
  }

  // Event listeners
  public subscribe(key: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }

    this.listeners.get(key)!.add(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(key);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.listeners.delete(key);
        }
      }
    };
  }

  private notifyListeners(key: string, data: any): void {
    const listeners = this.listeners.get(key);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in storage listener:', error);
        }
      });
    }
  }

  // Utility methods
  public getStorageSize(): string {
    let totalSize = 0;
    for (let key in this.storage) {
      if (this.storage.hasOwnProperty(key)) {
        totalSize += this.storage[key].length;
      }
    }
    return this.formatBytes(totalSize);
  }

  public isStorageAvailable(): boolean {
    try {
      const test = '__storage_test__';
      this.storage.setItem(test, test);
      this.storage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  private handleStorageQuotaExceeded(key: string): void {
    // Try to clear old data first
    console.warn('Storage quota exceeded, clearing old data...');

    // Clear items older than 30 days
    const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);

    for (let storageKey in this.storage) {
      if (storageKey.startsWith('offline_')) {
        try {
          const { timestamp } = JSON.parse(this.storage.getItem(storageKey) || '{}');
          if (timestamp && timestamp < thirtyDaysAgo) {
            this.storage.removeItem(storageKey);
          }
        } catch {
          // If we can't parse, remove it
          this.storage.removeItem(storageKey);
        }
      }
    }

    // Try to save again
    this.notifyListeners(key, null);
  }
}

// Export singleton instance
export const storageService = StorageService.getInstance();

// Export hooks for React components
import { useEffect, useState } from 'react';

export const useStorageSync = (key: string, initialValue: any = null) => {
  const [value, setValue] = useState(() =>
    storageService.getItem(key) || initialValue
  );

  useEffect(() => {
    const unsubscribe = storageService.subscribe(key, (newValue) => {
      setValue(newValue || initialValue);
    });

    return unsubscribe;
  }, [key, initialValue]);

  const setStoredValue = (newValue: any) => {
    setValue(newValue);
    storageService.setItem(key, newValue);
  };

  const removeStoredValue = () => {
    setValue(initialValue);
    storageService.removeItem(key);
  };

  return [value, setStoredValue, removeStoredValue] as const;
};

export const useSyncStatus = () => {
  const [status, setStatus] = useState(() => storageService.getSyncStatus());

  useEffect(() => {
    const unsubscribeOnline = storageService.subscribe('onlineStatus', (isOnline) => {
      setStatus(prev => ({ ...prev, isOnline }));
    });

    const unsubscribeSync = storageService.subscribe(KEYS.PENDING_ACTIONS, () => {
      setStatus(storageService.getSyncStatus());
    });

    return () => {
      unsubscribeOnline();
      unsubscribeSync();
    };
  }, []);

  return status;
};