/**
 * Personalization API service with authentication handling.
 *
 * This module provides API methods for content personalization features
 * with proper authentication checks and error handling.
 */

import { apiRequest, api } from './api';

// Types based on backend schemas
export interface PersonalizationRequest {
  content: string;
  title?: string;
  personalization_type?: 'technical_depth' | 'example_relevance' | 'learning_path' | 'full_personalization';
  target_audience?: string;
  focus_areas?: string[];
  avoid_topics?: string[];
  preferred_length?: 'shorter' | 'same' | 'longer';
  include_examples?: boolean;
  include_analogies?: boolean;
}

export interface PersonalizationAdaptation {
  type: string;
  original: string;
  adapted: string;
  reasoning?: string;
}

export interface PersonalizationResponse {
  id: string;
  original_content: string;
  personalized_content: string;
  adaptations_made: PersonalizationAdaptation[];
  processing_time_ms: number;
  user_profile_summary: Record<string, any>;
  content_segments: Array<{
    id: string;
    content: string;
    word_count: number;
    order: number;
  }>;
  metadata: Record<string, any>;
  created_at: string;
}

export interface PersonalizationError {
  error_code: string;
  error_message: string;
  details?: Record<string, any>;
  retry_possible: boolean;
  retry_after_seconds?: number;
}

export interface SavedPersonalization {
  id: string;
  title: string;
  personalization_type: string;
  rating?: number;
  is_favorite: boolean;
  access_count: number;
  tags: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PersonalizationStats {
  total_personalizations: number;
  saved_personalizations: number;
  average_rating?: number;
  favorite_count: number;
  total_processing_time_ms: number;
  average_processing_time_ms: number;
  most_used_personalization_type?: string;
  created_at: string;
}

export interface ContentExtractionResponse {
  content: string;
  title?: string;
  word_count: number;
  source_url?: string;
  extraction_method: string;
  metadata: Record<string, any>;
}

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  // Check for token in cookies (fallback for components without AuthContext)
  const token = getCookie('access_token');
  return !!token;
};

/**
 * Get authentication token
 */
export const getAuthToken = (): string | null => {
  return getCookie('access_token');
};

/**
 * Helper function to get cookie value
 */
const getCookie = (name: string): string | null => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null;
  }
  return null;
};

/**
 * Personalization API class with authentication checks
 */
class PersonalizationAPI {
  /**
   * Personalize content
   * Requires authentication
   */
  async personalizeContent(request: PersonalizationRequest): Promise<PersonalizationResponse> {
    // Check authentication before making request
    if (!isAuthenticated()) {
      throw new Error('AUTHENTICATION_REQUIRED');
    }

    try {
      const response = await apiRequest.post<PersonalizationResponse>(
        '/api/v1/personalize',
        request
      );
      return response.data;
    } catch (error: any) {
      // Handle specific error cases
      if (error.response?.status === 401) {
        throw new Error('AUTHENTICATION_REQUIRED');
      }
      if (error.response?.status === 403) {
        throw new Error('INSUFFICIENT_PERMISSIONS');
      }
      if (error.response?.status === 429) {
        const retryAfter = error.response.data?.retry_after;
        throw new Error(`RATE_LIMIT_EXCEEDED:${retryAfter || 60}`);
      }

      // Pass through other errors
      throw error;
    }
  }

  /**
   * Get saved personalizations for the authenticated user
   */
  async getSavedPersonalizations(page: number = 1, perPage: number = 10): Promise<{
    items: SavedPersonalization[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  }> {
    if (!isAuthenticated()) {
      throw new Error('AUTHENTICATION_REQUIRED');
    }

    const response = await apiRequest.get('/api/v1/personalize/saved', {
      params: { page, per_page: perPage }
    });
    return response.data;
  }

  /**
   * Save a personalization
   */
  async savePersonalization(
    personalizationId: string,
    title: string,
    tags?: string[],
    notes?: string
  ): Promise<SavedPersonalization> {
    if (!isAuthenticated()) {
      throw new Error('AUTHENTICATION_REQUIRED');
    }

    const response = await apiRequest.post<SavedPersonalization>(
      `/api/v1/personalize/saved/${personalizationId}`,
      { title, tags, notes }
    );
    return response.data;
  }

  /**
   * Rate a saved personalization
   */
  async ratePersonalization(
    savedId: string,
    rating: number,
    feedback?: string
  ): Promise<void> {
    if (!isAuthenticated()) {
      throw new Error('AUTHENTICATION_REQUIRED');
    }

    await apiRequest.post(`/api/v1/personalize/saved/${savedId}/rate`, {
      rating,
      feedback
    });
  }

  /**
   * Delete a saved personalization
   */
  async deleteSavedPersonalization(savedId: string): Promise<void> {
    if (!isAuthenticated()) {
      throw new Error('AUTHENTICATION_REQUIRED');
    }

    await apiRequest.delete(`/api/v1/personalize/saved/${savedId}`);
  }

  /**
   * Toggle favorite status
   */
  async toggleFavorite(savedId: string): Promise<SavedPersonalization> {
    if (!isAuthenticated()) {
      throw new Error('AUTHENTICATION_REQUIRED');
    }

    const response = await apiRequest.patch<SavedPersonalization>(
      `/api/v1/personalize/saved/${savedId}/favorite`
    );
    return response.data;
  }

  /**
   * Get user personalization statistics
   */
  async getPersonalizationStats(): Promise<PersonalizationStats> {
    if (!isAuthenticated()) {
      throw new Error('AUTHENTICATION_REQUIRED');
    }

    const response = await apiRequest.get<PersonalizationStats>(
      '/api/v1/personalize/stats'
    );
    return response.data;
  }

  /**
   * Extract content from a URL or current page
   * Can be used by unauthenticated users for content extraction only
   */
  async extractContent(
    url?: string,
    selector?: string,
    excludeSelectors?: string[]
  ): Promise<ContentExtractionResponse> {
    // This endpoint doesn't require authentication
    const response = await apiRequest.post<ContentExtractionResponse>(
      '/api/v1/personalize/extract',
      {
        url,
        selector,
        exclude_selectors: excludeSelectors
      }
    );
    return response.data;
  }

  /**
   * Validate if content can be personalized
   * Returns validation result without personalizing
   */
  async validateContent(content: string): Promise<{
    valid: boolean;
    word_count: number;
    estimated_processing_time_ms: number;
    errors?: string[];
  }> {
    // This endpoint doesn't require authentication
    const response = await apiRequest.post('/api/v1/personalize/validate', {
      content
    });
    return response.data;
  }
}

// Create singleton instance
export const personalizationAPI = new PersonalizationAPI();

// Export the class for testing or custom instances
export { PersonalizationAPI };

// Export error types for error handling
export const PERSONALIZATION_ERRORS = {
  AUTHENTICATION_REQUIRED: 'AUTHENTICATION_REQUIRED',
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  CONTENT_TOO_LONG: 'CONTENT_TOO_LONG',
  CONTENT_TOO_SHORT: 'CONTENT_TOO_SHORT',
  PROCESSING_ERROR: 'PROCESSING_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR'
} as const;

/**
 * Check if personalization should be available
 * Returns true if authenticated, false otherwise
 */
export const canPersonalize = (): boolean => {
  return isAuthenticated();
};

/**
 * Get personalization availability status
 */
export const getPersonalizationStatus = (): {
  available: boolean;
  requiresAuth: boolean;
  reason?: string;
} => {
  if (!isAuthenticated()) {
    return {
      available: false,
      requiresAuth: true,
      reason: 'Authentication required for content personalization'
    };
  }

  return {
    available: true,
    requiresAuth: false
  };
};

/**
 * Create a hook for personalization authentication status
 * This should be used within components that have access to AuthContext
 */
export const usePersonalizationAuth = (isAuthenticated: boolean) => {
  return {
    canPersonalize: isAuthenticated,
    status: {
      available: isAuthenticated,
      requiresAuth: !isAuthenticated,
      reason: !isAuthenticated ? 'Authentication required for content personalization' : undefined
    }
  };
};