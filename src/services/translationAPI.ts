/**
 * Translation API service for managing translation requests and responses.

This service handles all translation-related API calls including:
- Content translation requests with streaming support
- Translation feedback submission
- Translation history retrieval
- Personalization settings management
- Caching integration for performance
*/

import { apiRequest } from './api';
import { cacheService } from './cache';
import { getCookie } from '../contexts/AuthContext';

// Type definitions
export interface TranslationRequest {
  text: string;
  sourceLanguage: string;
  targetLanguage: string;
  context?: string;
  preferCache?: boolean;
  stream?: boolean;
  userId?: string;
}

export interface TranslationResponse {
  id: number;
  contentHash: string;
  sourceLanguage: string;
  targetLanguage: string;
  originalText: string;
  translatedText: string;
  model: string;
  characterCount: number;
  createdAt: string;
  updatedAt: string;
  isCached: boolean;
}

export interface TranslationFeedbackRequest {
  translationId: number;
  rating: 1 | -1;
  comment?: string;
}

export interface TranslationFeedback {
  id: number;
  translationId: number;
  userId: string;
  rating: 1 | -1;
  comment?: string;
  createdAt: string;
}

export interface TranslationHistoryEntry {
  id: number;
  sourceLanguage: string;
  targetLanguage: string;
  originalText: string;
  translatedText: string;
  createdAt: string;
  feedback?: TranslationFeedback;
  isBookmarked: boolean;
}

export interface PersonalizationSettings {
  preferredLanguage: string;
  autoDetectLanguage: boolean;
  showOriginalText: boolean;
  saveHistory: boolean;
  enableCaching: boolean;
  defaultModel?: string;
}

export interface TranslationStreamChunk {
  type: 'start' | 'chunk' | 'end' | 'error';
  content?: string;
  translationId?: number;
  error?: string;
  metadata?: {
    model: string;
    cached: boolean;
    processingTime: number;
  };
}

export interface TranslationCacheEntry {
  hash: string;
  sourceLanguage: string;
  targetLanguage: string;
  translation: string;
  model: string;
  cachedAt: string;
  hits: number;
}

class TranslationAPIService {
  private static instance: TranslationAPIService;
  private cacheKeyPrefix = 'translation';
  private historyKeyPrefix = 'translation_history';
  private personalizationKey = 'translation_personalization';

  private constructor() {}

  public static getInstance(): TranslationAPIService {
    if (!TranslationAPIService.instance) {
      TranslationAPIService.instance = new TranslationAPIService();
    }
    return TranslationAPIService.instance;
  }

  /**
   * Generate content hash for caching
   */
  private generateContentHash(text: string, sourceLang: string, targetLang: string): string {
    const content = `${text}:${sourceLang}:${targetLang}`;
    return btoa(content).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
  }

  /**
   * Translate content with optional streaming support
   */
  public async translate(
    request: TranslationRequest
  ): Promise<TranslationResponse | AsyncIterable<TranslationStreamChunk>> {
    const {
      text,
      sourceLanguage,
      targetLanguage,
      context,
      preferCache = true,
      stream = false,
      userId
    } = request;

    // Generate cache key
    const contentHash = this.generateContentHash(text, sourceLanguage, targetLanguage);
    const cacheKey = `${this.cacheKeyPrefix}:${contentHash}`;

    // Check cache first if preferred
    if (preferCache) {
      const cached = await this.getCachedTranslation(cacheKey);
      if (cached) {
        return {
          ...cached,
          isCached: true,
        };
      }
    }

    try {
      if (stream) {
        // Return streaming response
        return this.translateStream(request);
      } else {
        // Return single response
        const response = await apiRequest.post<TranslationResponse>('/api/v1/translate', {
          text,
          source_language: sourceLanguage,
          target_language: targetLanguage,
          context,
          user_id: userId || this.getCurrentUserId(),
        });

        const translation = response.data;

        // Cache the translation if caching is enabled
        if (preferCache) {
          await this.cacheTranslation(cacheKey, translation);
        }

        // Save to history if enabled
        const personalization = await this.getPersonalizationSettings();
        if (personalization.saveHistory) {
          await this.saveToHistory(translation);
        }

        return {
          ...translation,
          isCached: false,
        };
      }
    } catch (error: any) {
      throw new Error(`Translation failed: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Stream translation response
   */
  private async *translateStream(
    request: TranslationRequest
  ): AsyncIterable<TranslationStreamChunk> {
    const { text, sourceLanguage, targetLanguage, context } = request;

    try {
      const response = await fetch('/api/v1/translate/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getCookie('access_token')}`,
        },
        body: JSON.stringify({
          text,
          source_language: sourceLanguage,
          target_language: targetLanguage,
          context,
          user_id: this.getCurrentUserId(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              yield data;
            } catch (e) {
              console.error('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error: any) {
      yield {
        type: 'error',
        error: error.message,
      };
    }
  }

  /**
   * Submit feedback for a translation
   */
  public async submitFeedback(request: TranslationFeedbackRequest): Promise<TranslationFeedback> {
    try {
      const response = await apiRequest.post<TranslationFeedback>('/api/v1/translate/feedback', {
        translation_id: request.translationId,
        rating: request.rating,
        comment: request.comment,
        user_id: this.getCurrentUserId(),
      });

      // Update cached history with feedback
      await this.updateHistoryWithFeedback(response.data);

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to submit feedback: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Get translation history for the current user
   */
  public async getTranslationHistory(
    page: number = 1,
    limit: number = 20,
    filters?: {
      sourceLanguage?: string;
      targetLanguage?: string;
      dateFrom?: string;
      dateTo?: string;
      hasFeedback?: boolean;
    }
  ): Promise<{ entries: TranslationHistoryEntry[]; total: number; page: number; totalPages: number }> {
    try {
      // Check cache first
      const cacheKey = `${this.historyKeyPrefix}:${JSON.stringify({ page, limit, filters })}`;
      const cached = cacheService ? await cacheService.get(cacheKey) : null;
      if (cached) {
        return cached;
      }

      const params: any = { page, limit, user_id: this.getCurrentUserId() };
      if (filters) {
        Object.assign(params, filters);
      }

      const response = await apiRequest.get<{
        entries: TranslationHistoryEntry[];
        total: number;
        page: number;
        totalPages: number;
      }>('/api/v1/translate/history', { params });

      // Cache the result
      if (cacheService) {
        await cacheService.set(cacheKey, response.data, { ttl: 5 * 60 * 1000 }); // 5 minutes
      }

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to fetch translation history: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Get personalization settings for the current user
   */
  public async getPersonalizationSettings(): Promise<PersonalizationSettings> {
    try {
      // Check cache first
      const cached = cacheService ? await cacheService.get(this.personalizationKey) : null;
      if (cached) {
        return cached;
      }

      const response = await apiRequest.get<PersonalizationSettings>('/api/v1/translate/personalization', {
        params: { user_id: this.getCurrentUserId() },
      });

      // Cache the settings
      if (cacheService) {
        await cacheService.set(this.personalizationKey, response.data, { ttl: 30 * 60 * 1000 }); // 30 minutes
      }

      return response.data;
    } catch (error: any) {
      // Return default settings if API fails
      const defaultSettings: PersonalizationSettings = {
        preferredLanguage: 'en',
        autoDetectLanguage: true,
        showOriginalText: false,
        saveHistory: true,
        enableCaching: true,
      };
      return defaultSettings;
    }
  }

  /**
   * Update personalization settings
   */
  public async updatePersonalizationSettings(
    settings: Partial<PersonalizationSettings>
  ): Promise<PersonalizationSettings> {
    try {
      const response = await apiRequest.put<PersonalizationSettings>(
        '/api/v1/translate/personalization',
        {
          ...settings,
          user_id: this.getCurrentUserId(),
        }
      );

      // Update cache
      if (cacheService) {
        await cacheService.set(this.personalizationKey, response.data, { ttl: 30 * 60 * 1000 });
      }

      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to update personalization settings: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Clear translation cache
   */
  public async clearCache(pattern?: string): Promise<number> {
    const cachePattern = pattern ? `${this.cacheKeyPrefix}:${pattern}` : `${this.cacheKeyPrefix}:*`;
    return cacheService ? cacheService.clear(cachePattern) : 0;
  }

  /**
   * Get cache statistics
   */
  public async getCacheStats(): Promise<{
    size: number;
    hits: number;
    misses: number;
    entries: TranslationCacheEntry[];
  }> {
    try {
      const response = await apiRequest.get<{
        size: number;
        hits: number;
        misses: number;
        entries: TranslationCacheEntry[];
      }>('/api/v1/translate/cache/stats', {
        params: { user_id: this.getCurrentUserId() },
      });

      return response.data;
    } catch (error: any) {
      // Return default stats if API fails
      return {
        size: 0,
        hits: 0,
        misses: 0,
        entries: [],
      };
    }
  }

  /**
   * Delete a translation from history
   */
  public async deleteTranslation(translationId: number): Promise<void> {
    try {
      await apiRequest.delete(`/api/v1/translate/history/${translationId}`, {
        params: { user_id: this.getCurrentUserId() },
      });

      // Clear related cache entries
      if (cacheService) {
        cacheService.clear(`${this.historyKeyPrefix}:*`);
      }
    } catch (error: any) {
      throw new Error(`Failed to delete translation: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Batch delete translations from history
   */
  public async batchDeleteTranslations(translationIds: number[]): Promise<void> {
    try {
      await apiRequest.post('/api/v1/translate/history/batch-delete', {
        translation_ids: translationIds,
        user_id: this.getCurrentUserId(),
      });

      // Clear related cache entries
      if (cacheService) {
        cacheService.clear(`${this.historyKeyPrefix}:*`);
      }
    } catch (error: any) {
      throw new Error(`Failed to batch delete translations: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Private helper methods

  private getCurrentUserId(): string {
    const userId = getCookie('user_id');
    if (!userId) {
      throw new Error('User not authenticated');
    }
    return userId;
  }

  private async getCachedTranslation(cacheKey: string): Promise<TranslationResponse | null> {
    try {
      return cacheService ? await cacheService.get(cacheKey) : null;
    } catch (error) {
      console.error('Failed to get cached translation:', error);
      return null;
    }
  }

  private async cacheTranslation(cacheKey: string, translation: TranslationResponse): Promise<void> {
    try {
      if (cacheService) {
        await cacheService.set(cacheKey, translation, { ttl: 7 * 24 * 60 * 60 * 1000 }); // 7 days
      }
    } catch (error) {
      console.error('Failed to cache translation:', error);
    }
  }

  private async saveToHistory(translation: TranslationResponse): Promise<void> {
    try {
      // This would typically be handled by the backend, but we can
      // also maintain a local copy for immediate UI updates
      const historyKey = `${this.historyKeyPrefix}:local:${this.getCurrentUserId()}`;
      const history = cacheService ? (await cacheService.get(historyKey)) || [] : [];

      history.unshift({
        id: translation.id,
        sourceLanguage: translation.sourceLanguage,
        targetLanguage: translation.targetLanguage,
        originalText: translation.originalText,
        translatedText: translation.translatedText,
        createdAt: translation.createdAt,
        isBookmarked: false,
      });

      // Keep only last 100 entries locally
      if (history.length > 100) {
        history.splice(100);
      }

      if (cacheService) {
        await cacheService.set(historyKey, history, { ttl: 24 * 60 * 60 * 1000 }); // 24 hours
      }
    } catch (error) {
      console.error('Failed to save to history:', error);
    }
  }

  private async updateHistoryWithFeedback(feedback: TranslationFeedback): Promise<void> {
    try {
      const historyKey = `${this.historyKeyPrefix}:local:${this.getCurrentUserId()}`;
      const history = cacheService ? (await cacheService.get(historyKey)) || [] : [];

      const entry = history.find((e: any) => e.id === feedback.translationId);
      if (entry) {
        entry.feedback = feedback;
        if (cacheService) {
          await cacheService.set(historyKey, history, { ttl: 24 * 60 * 60 * 1000 });
        }
      }
    } catch (error) {
      console.error('Failed to update history with feedback:', error);
    }
  }
}

// Export singleton instance
export const translationAPI = TranslationAPIService.getInstance();

// Export types for use in components
export type {
  TranslationRequest,
  TranslationResponse,
  TranslationFeedbackRequest,
  TranslationFeedback,
  TranslationHistoryEntry,
  PersonalizationSettings,
  TranslationStreamChunk,
  TranslationCacheEntry,
};