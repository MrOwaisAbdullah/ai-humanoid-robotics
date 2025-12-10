/**
 * Cache service with localStorage fallback and backend integration.

This service provides a unified caching interface that:
- Uses localStorage as primary storage
- Supports TTL (Time To Live) for cache entries
- Provides cache key management and namespacing
- Handles size limits and LRU eviction
- Integrates with backend cache service when online
- Includes compression for large objects
- Provides cache statistics and monitoring
*/

import { apiRequest } from './api';
import { storageService } from './storage';

// Type definitions
export interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  compress?: boolean; // Enable compression for large objects
  priority?: 'low' | 'normal' | 'high'; // Priority for eviction
  namespace?: string; // Namespace for key isolation
  version?: string; // Version for cache invalidation
}

export interface CacheEntry<T = any> {
  value: T;
  expires: number; // Timestamp in milliseconds
  created: number; // Timestamp when created
  accessed: number; // Last access time
  hitCount: number;
  size: number; // Size in bytes
  compressed: boolean;
  priority: 'low' | 'normal' | 'high';
  version: string;
}

export interface CacheStats {
  totalEntries: number;
  totalSize: string;
  hitRate: number;
  totalHits: number;
  totalMisses: number;
  oldestEntry: number | null;
  newestEntry: number | null;
  namespaceStats: Record<string, { entries: number; size: string }>;
}

export interface CacheMetadata {
  maxSize: number; // Maximum cache size in bytes
  maxEntries: number; // Maximum number of entries
  cleanupInterval: number; // Cleanup interval in milliseconds
  compressionThreshold: number; // Size threshold for compression in bytes
}

class CacheService {
  private static instance: CacheService;
  private storage: Storage;
  private memoryCache: Map<string, CacheEntry> = new Map();
  private listeners: Map<string, Set<(key: string, value: any) => void>> = new Map();
  private cleanupTimer: NodeJS.Timeout | null = null;

  private stats = {
    hits: 0,
    misses: 0,
    evictions: 0,
    errors: 0,
  };

  private readonly metadata: CacheMetadata = {
    maxSize: 50 * 1024 * 1024, // 50MB
    maxEntries: 1000,
    cleanupInterval: 5 * 60 * 1000, // 5 minutes
    compressionThreshold: 1024, // 1KB
  };

  private readonly DEFAULT_TTL = 24 * 60 * 60 * 1000; // 24 hours
  private readonly VERSION = '1.0.0';
  private readonly PREFIX = 'app_cache';
  private readonly METADATA_KEY = `${this.PREFIX}_metadata`;

  private constructor() {
    // Check if we're in a browser environment
    if (typeof window !== 'undefined') {
      this.storage = window.localStorage;
      this.initializeCache();
      this.startCleanupTimer();
    } else {
      // Server-side fallback - use in-memory storage
      this.storage = {
        length: 0,
        clear: () => {},
        getItem: () => null,
        key: () => null,
        removeItem: () => {},
        setItem: () => {},
      };
    }
  }

  public static getInstance(): CacheService {
    if (!CacheService.instance) {
      CacheService.instance = new CacheService();
    }
    return CacheService.instance;
  }

  private initializeCache(): void {
    try {
      // Load metadata
      const metadataStr = this.storage.getItem(this.METADATA_KEY);
      if (metadataStr) {
        const metadata = JSON.parse(metadataStr);
        Object.assign(this.metadata, metadata);
      }

      // Load frequently accessed entries into memory
      this.loadHighPriorityEntries();
    } catch (error) {
      console.error('Failed to initialize cache:', error);
    }
  }

  private startCleanupTimer(): void {
    if (typeof window === 'undefined') return; // Don't run timers on server

    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    this.cleanupTimer = setInterval(() => {
      this.cleanupExpired();
    }, this.metadata.cleanupInterval);
  }

  private generateKey(
    key: string,
    options: CacheOptions = {}
  ): string {
    const namespace = options.namespace || 'default';
    const version = options.version || this.VERSION;
    return `${this.PREFIX}:${namespace}:${version}:${key}`;
  }

  private async compress(data: string): Promise<string> {
    if (typeof window !== 'undefined' && 'CompressionStream' in window) {
      try {
        const stream = new CompressionStream('gzip');
        const writer = stream.writable.getWriter();
        const reader = stream.readable.getReader();

        writer.write(new TextEncoder().encode(data));
        writer.close();

        const chunks: Uint8Array[] = [];
        let done = false;

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) chunks.push(value);
        }

        const compressed = new Uint8Array(chunks.reduce((acc, chunk) => acc + chunk.length, 0));
        let offset = 0;
        for (const chunk of chunks) {
          compressed.set(chunk, offset);
          offset += chunk.length;
        }

        return btoa(String.fromCharCode(...compressed));
      } catch (error) {
        console.warn('Compression failed:', error);
      }
    }
    return data;
  }

  private async decompress(compressedData: string): Promise<string> {
    if (typeof window !== 'undefined' && 'DecompressionStream' in window) {
      try {
        const compressed = Uint8Array.from(atob(compressedData), c => c.charCodeAt(0));
        const stream = new DecompressionStream('gzip');
        const writer = stream.writable.getWriter();
        const reader = stream.readable.getReader();

        writer.write(compressed);
        writer.close();

        const chunks: Uint8Array[] = [];
        let done = false;

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) chunks.push(value);
        }

        const decompressed = new Uint8Array(chunks.reduce((acc, chunk) => acc + chunk.length, 0));
        let offset = 0;
        for (const chunk of chunks) {
          decompressed.set(chunk, offset);
          offset += chunk.length;
        }

        return new TextDecoder().decode(decompressed);
      } catch (error) {
        console.warn('Decompression failed:', error);
      }
    }
    return compressedData;
  }

  private calculateSize(value: any): number {
    if (typeof window !== 'undefined' && typeof Blob !== 'undefined') {
      return new Blob([JSON.stringify(value)]).size;
    }
    // Fallback for SSR - rough estimate
    return JSON.stringify(value).length * 2; // Assume 2 bytes per character
  }

  private shouldCompress(size: number, options: CacheOptions): boolean {
    return (options.compress !== false) && (size > this.metadata.compressionThreshold);
  }

  private async serializeEntry(entry: CacheEntry): Promise<string> {
    const data = JSON.stringify(entry);

    if (entry.compressed) {
      return await this.compress(data);
    }

    return data;
  }

  private async deserializeEntry(data: string, compressed: boolean): Promise<CacheEntry> {
    try {
      const parsedData = compressed ? await this.decompress(data) : data;
      return JSON.parse(parsedData);
    } catch (error) {
      throw new Error(`Failed to deserialize cache entry: ${error}`);
    }
  }

  private async checkBackendCache(key: string): Promise<any | null> {
    try {
      // Check if online and in browser environment
      if (typeof window === 'undefined' || !navigator.onLine) return null;

      const response = await apiRequest.get('/api/v1/cache', {
        params: { key },
      });

      if (response.data?.value) {
        // Cache in localStorage for faster access
        await this.set(key, response.data.value, {
          ttl: response.data.ttl,
          namespace: 'backend',
        });
        return response.data.value;
      }

      return null;
    } catch (error) {
      // Silently fail and use local cache
      return null;
    }
  }

  private async syncToBackend(key: string, value: any, ttl: number): Promise<void> {
    try {
      // Check if online and in browser environment
      if (typeof window === 'undefined' || !navigator.onLine) return;

      await apiRequest.post('/api/v1/cache', {
        key,
        value,
        ttl: Math.ceil(ttl / 1000), // Convert to seconds
      });
    } catch (error) {
      // Silently fail - cache is still available locally
      console.warn('Failed to sync to backend:', error);
    }
  }

  private loadHighPriorityEntries(): void {
    try {
      for (let i = 0; i < this.storage.length; i++) {
        const key = this.storage.key(i);
        if (key?.startsWith(this.PREFIX)) {
          try {
            const entryStr = this.storage.getItem(key);
            if (entryStr) {
              const entry = JSON.parse(entryStr) as CacheEntry;

              // Load high priority entries into memory
              if (entry.priority === 'high' && !this.isExpired(entry)) {
                this.memoryCache.set(key, entry);
              }
            }
          } catch (error) {
            // Remove invalid entry
            this.storage.removeItem(key);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load high priority entries:', error);
    }
  }

  private isExpired(entry: CacheEntry): boolean {
    return Date.now() > entry.expires;
  }

  private enforceEvictionPolicy(): void {
    // Check size limit
    let currentSize = this.getCurrentSize();
    if (currentSize > this.metadata.maxSize) {
      this.evictByLRU(currentSize - this.metadata.maxSize);
    }

    // Check entry count limit
    if (this.memoryCache.size > this.metadata.maxEntries) {
      const toEvict = this.memoryCache.size - this.metadata.maxEntries;
      this.evictLeastRecentlyUsed(toEvict);
    }
  }

  private evictByLRU(bytesToFree: number): void {
    const entries = Array.from(this.memoryCache.entries())
      .sort(([, a], [, b]) => a.accessed - b.accessed);

    let freed = 0;
    for (const [key, entry] of entries) {
      this.delete(key);
      freed += entry.size;
      this.stats.evictions++;

      if (freed >= bytesToFree) break;
    }
  }

  private evictLeastRecentlyUsed(count: number): void {
    const entries = Array.from(this.memoryCache.entries())
      .sort(([, a], [, b]) => a.accessed - b.accessed);

    for (let i = 0; i < Math.min(count, entries.length); i++) {
      const [key] = entries[i];
      this.delete(key);
      this.stats.evictions++;
    }
  }

  private getCurrentSize(): number {
    let size = 0;
    for (const entry of this.memoryCache.values()) {
      size += entry.size;
    }
    return size;
  }

  private cleanupExpired(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    // Check memory cache
    for (const [key, entry] of this.memoryCache.entries()) {
      if (now > entry.expires) {
        expiredKeys.push(key);
      }
    }

    // Remove expired entries
    for (const key of expiredKeys) {
      this.delete(key);
    }

    // Also clean localStorage
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i);
      if (key?.startsWith(this.PREFIX)) {
        try {
          const entryStr = this.storage.getItem(key);
          if (entryStr) {
            const entry = JSON.parse(entryStr) as CacheEntry;
            if (now > entry.expires) {
              this.storage.removeItem(key);
            }
          }
        } catch (error) {
          // Remove invalid entry
          this.storage.removeItem(key);
        }
      }
    }
  }

  /**
   * Get value from cache
   */
  public async get<T = any>(
    key: string,
    options: CacheOptions = {}
  ): Promise<T | null> {
    const cacheKey = this.generateKey(key, options);

    try {
      // Check memory cache first
      let entry = this.memoryCache.get(cacheKey);

      if (entry) {
        if (this.isExpired(entry)) {
          this.memoryCache.delete(cacheKey);
          this.storage.removeItem(cacheKey);
        } else {
          // Update access statistics
          entry.accessed = Date.now();
          entry.hitCount++;
          this.stats.hits++;
          return entry.value;
        }
      }

      // Check localStorage
      const entryStr = this.storage.getItem(cacheKey);
      if (entryStr) {
        entry = await this.deserializeEntry(entryStr, false);

        if (this.isExpired(entry)) {
          this.storage.removeItem(cacheKey);
        } else {
          // Update access statistics
          entry.accessed = Date.now();
          entry.hitCount++;
          this.stats.hits++;

          // Move to memory if high priority
          if (entry.priority === 'high') {
            this.memoryCache.set(cacheKey, entry);
          }

          return entry.value;
        }
      }

      // Check backend cache
      if (options.namespace !== 'backend') {
        const backendValue = await this.checkBackendCache(cacheKey);
        if (backendValue !== null) {
          this.stats.hits++;
          return backendValue;
        }
      }

      this.stats.misses++;
      return null;
    } catch (error) {
      this.stats.errors++;
      console.error('Cache get error:', error);
      return null;
    }
  }

  /**
   * Set value in cache
   */
  public async set<T = any>(
    key: string,
    value: T,
    options: CacheOptions = {}
  ): Promise<void> {
    const cacheKey = this.generateKey(key, options);
    const now = Date.now();
    const ttl = options.ttl || this.DEFAULT_TTL;
    const size = this.calculateSize(value);
    const compress = this.shouldCompress(size, options);

    const entry: CacheEntry<T> = {
      value,
      expires: now + ttl,
      created: now,
      accessed: now,
      hitCount: 0,
      size,
      compressed: compress,
      priority: options.priority || 'normal',
      version: options.version || this.VERSION,
    };

    try {
      // Store in localStorage
      const serialized = await this.serializeEntry(entry);
      this.storage.setItem(cacheKey, serialized);

      // Store in memory if high priority
      if (entry.priority === 'high') {
        this.memoryCache.set(cacheKey, entry);
      }

      // Enforce eviction policy
      this.enforceEvictionPolicy();

      // Sync to backend if online and in browser environment
      if (options.namespace !== 'backend' && typeof window !== 'undefined' && navigator.onLine) {
        await this.syncToBackend(cacheKey, value, ttl);
      }

      // Notify listeners
      this.notifyListeners(key, value);
    } catch (error) {
      this.stats.errors++;
      console.error('Cache set error:', error);
      throw error;
    }
  }

  /**
   * Delete value from cache
   */
  public delete(key: string, options: CacheOptions = {}): boolean {
    const cacheKey = this.generateKey(key, options);

    try {
      this.memoryCache.delete(cacheKey);
      this.storage.removeItem(cacheKey);
      this.notifyListeners(key, null);
      return true;
    } catch (error) {
      this.stats.errors++;
      console.error('Cache delete error:', error);
      return false;
    }
  }

  /**
   * Clear cache entries matching a pattern
   */
  public clear(pattern?: string, namespace?: string): number {
    let cleared = 0;

    try {
      const prefix = pattern ? `${this.PREFIX}:${namespace || 'default'}:${this.VERSION}:${pattern}` :
                     namespace ? `${this.PREFIX}:${namespace}:` :
                     `${this.PREFIX}:`;

      // Clear from memory cache
      for (const key of this.memoryCache.keys()) {
        if (key.startsWith(prefix)) {
          this.memoryCache.delete(key);
          cleared++;
        }
      }

      // Clear from localStorage
      const keysToRemove: string[] = [];
      for (let i = 0; i < this.storage.length; i++) {
        const key = this.storage.key(i);
        if (key?.startsWith(prefix)) {
          keysToRemove.push(key);
        }
      }

      for (const key of keysToRemove) {
        this.storage.removeItem(key);
        cleared++;
      }

      return cleared;
    } catch (error) {
      this.stats.errors++;
      console.error('Cache clear error:', error);
      return 0;
    }
  }

  /**
   * Check if key exists in cache
   */
  public async has(key: string, options: CacheOptions = {}): Promise<boolean> {
    const cacheKey = this.generateKey(key, options);

    // Check memory cache
    if (this.memoryCache.has(cacheKey)) {
      const entry = this.memoryCache.get(cacheKey)!;
      if (this.isExpired(entry)) {
        this.memoryCache.delete(cacheKey);
        return false;
      }
      return true;
    }

    // Check localStorage
    const entryStr = this.storage.getItem(cacheKey);
    if (entryStr) {
      try {
        const entry = JSON.parse(entryStr) as CacheEntry;
        if (this.isExpired(entry)) {
          this.storage.removeItem(cacheKey);
          return false;
        }
        return true;
      } catch {
        this.storage.removeItem(cacheKey);
      }
    }

    return false;
  }

  /**
   * Get cache statistics
   */
  public getStats(): CacheStats {
    const namespaceStats: Record<string, { entries: number; size: string }> = {};

    // Calculate stats
    for (const [key, entry] of this.memoryCache.entries()) {
      const namespace = key.split(':')[1] || 'default';
      if (!namespaceStats[namespace]) {
        namespaceStats[namespace] = { entries: 0, size: '0' };
      }
      namespaceStats[namespace].entries++;
    }

    const totalRequests = this.stats.hits + this.stats.misses;
    const hitRate = totalRequests > 0 ? (this.stats.hits / totalRequests) * 100 : 0;

    return {
      totalEntries: this.memoryCache.size,
      totalSize: this.formatBytes(this.getCurrentSize()),
      hitRate: Math.round(hitRate * 100) / 100,
      totalHits: this.stats.hits,
      totalMisses: this.stats.misses,
      oldestEntry: this.memoryCache.size > 0 ?
        Math.min(...Array.from(this.memoryCache.values()).map(e => e.created)) : null,
      newestEntry: this.memoryCache.size > 0 ?
        Math.max(...Array.from(this.memoryCache.values()).map(e => e.created)) : null,
      namespaceStats,
    };
  }

  /**
   * Subscribe to cache changes
   */
  public subscribe(
    key: string,
    callback: (key: string, value: any) => void
  ): () => void {
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

  private notifyListeners(key: string, value: any): void {
    const listeners = this.listeners.get(key);
    if (listeners) {
      for (const callback of listeners) {
        try {
          callback(key, value);
        } catch (error) {
          console.error('Cache listener error:', error);
        }
      }
    }
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Cleanup expired entries and free memory
   */
  public cleanup(): number {
    return this.cleanupExpired();
  }

  /**
   * Destroy cache service
   */
  public destroy(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }

    this.memoryCache.clear();
    this.listeners.clear();
  }
}

// Export singleton instance with SSR protection
let cacheServiceInstance: CacheService | null = null;

export const getCacheService = (): CacheService => {
  if (!cacheServiceInstance && typeof window !== 'undefined') {
    cacheServiceInstance = CacheService.getInstance();
  }
  return cacheServiceInstance!;
};

// Export a safe version that works on both client and server
export const cacheService: CacheService | null = typeof window !== 'undefined' ? getCacheService() : null;

// Export types
export type {
  CacheOptions,
  CacheEntry,
  CacheStats,
  CacheMetadata,
};