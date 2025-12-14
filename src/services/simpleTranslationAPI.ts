/**
 * Simplified Translation API service for direct API calls to the agent endpoint.
 * This service bypasses complex caching and streaming for straightforward translation requests.
 */

import { apiRequest } from './api';

// Type definitions
export interface SimpleTranslationRequest {
  text: string;
  userId?: string;
}

export interface SimpleTranslationResponse {
  translated_text: string;
  original_text: string;
  model: string;
  confidence_score?: number;
  has_code_blocks?: boolean;
  tokens_used?: number;
  cached?: boolean;
  cache_created_at?: string;
  hit_count?: number;
}

class SimpleTranslationAPIService {
  private static instance: SimpleTranslationAPIService;

  private constructor() {}

  public static getInstance(): SimpleTranslationAPIService {
    if (!SimpleTranslationAPIService.instance) {
      SimpleTranslationAPIService.instance = new SimpleTranslationAPIService();
    }
    return SimpleTranslationAPIService.instance;
  }

  /**
   * Get current user ID from cookie or return anonymous placeholder
   */
  private getCurrentUserId(): string {
    // Simple function to get user ID without external dependencies
    const getCookie = (name: string): string | null => {
      if (typeof document === 'undefined') return null;
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) {
        const cookieValue = parts.pop()?.split(';').shift();
        return cookieValue || null;
      }
      return null;
    };

    const userId = getCookie('user_id');
    return userId || 'anonymous_user';
  }

  /**
   * Direct translation using the agent endpoint
   */
  public async translate(request: SimpleTranslationRequest): Promise<SimpleTranslationResponse> {
    const {
      text,
      userId
    } = request;

    console.log('Simple Translation API: Making request to agent endpoint', {
      textLength: text.length,
      userId: userId || this.getCurrentUserId()
    });

    try {
      // Make direct API call to agent endpoint
      const response = await apiRequest.post<SimpleTranslationResponse>(
        '/api/v1/translation/translate/agent',
        {
          text: text.trim(),
          source_language: 'en', // Always from English
          target_language: 'ur', // Always to Urdu
          document_type: 'general',
          user_id: userId || this.getCurrentUserId()
        }
      );

      console.log('Simple Translation API: Received response', {
        success: true,
        responseKeys: Object.keys(response.data),
        translatedTextLength: response.data.translated_text?.length || 0
      });

      return response.data;
    } catch (error: any) {
      console.error('Simple Translation API: Error occurred', {
        error: error.message,
        response: error.response?.data,
        status: error.response?.status
      });

      // Re-throw with more descriptive message
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.message ||
                          error.message ||
                          'Translation failed';

      throw new Error(`Translation failed: ${errorMessage}`);
    }
  }
}

// Export singleton instance
export const simpleTranslationAPI = SimpleTranslationAPIService.getInstance();

// Export types
export type {
  SimpleTranslationRequest,
  SimpleTranslationResponse
};