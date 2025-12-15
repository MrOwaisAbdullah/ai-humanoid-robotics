/**
 * Personalization modal for generating and managing personalized content explanations.
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiRequest } from '../../services/api';
import { Loader2, Sparkles, Save, X, ChevronRight, Clock, User } from 'lucide-react';

interface PersonalizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: string;
  contentType: 'selected' | 'page';
  wordCount?: number;
}

interface PersonalizedExplanation {
  id: string;
  content: string;
  explanation: string;
  created_at: string;
  context_type: 'selected' | 'page';
  word_count: number;
}

interface SavedPersonalization {
  id: string;
  original_content: string;
  explanation: string;
  created_at: string;
  expires_at: string;
  title: string;
}

export const PersonalizationModal: React.FC<PersonalizationModalProps> = ({
  isOpen,
  onClose,
  content,
  contentType,
  wordCount
}) => {
  const { user } = useAuth();
  const [isGenerating, setIsGenerating] = useState(false);
  const [explanation, setExplanation] = useState<string>('');
  const [savedPersonalizations, setSavedPersonalizations] = useState<SavedPersonalization[]>([]);
  const [showSaved, setShowSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isOpen && mounted && user) {
      // Load saved personalizations when modal opens
      loadSavedPersonalizations();
      // Reset state
      setExplanation('');
      setError(null);
      setShowSaved(false);
    }
  }, [isOpen, mounted, user]);

  const loadSavedPersonalizations = async () => {
    if (!user) return;
    
    try {
      const response = await apiRequest.get('/api/v1/personalization/list');
      if (response.data && response.data.personalizations) {
        setSavedPersonalizations(response.data.personalizations);
      }
    } catch (error) {
      console.error('Failed to load saved personalizations:', error);
      // Don't show error for loading saved items
    }
  };

  const generatePersonalization = async () => {
    if (!user || !content || !content.trim()) {
      setError('No content available for personalization');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await apiRequest.post('/api/v1/personalization/generate', {
        content: content.trim(),
        context_type: contentType,
        word_count: wordCount || content.split(' ').length
      });

      if (response.data && response.data.explanation) {
        setExplanation(response.data.explanation);
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.message ||
                          'Failed to generate personalized explanation';
      setError(errorMessage);
      console.error('Personalization generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const savePersonalization = async () => {
    if (!explanation.trim() || !user || !content) return;

    try {
      const response = await apiRequest.post('/api/v1/personalization/save', {
        content: content.trim(),
        explanation: explanation.trim(),
        context_type: contentType,
        word_count: wordCount || content.split(' ').length
      });

      if (response.data) {
        // Add to saved list
        const newSaved: SavedPersonalization = {
          id: response.data.id || Date.now().toString(),
          original_content: content.trim(),
          explanation: explanation.trim(),
          created_at: new Date().toISOString(),
          expires_at: response.data.expires_at || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          title: response.data.title || generateTitle(content)
        };
        setSavedPersonalizations(prev => [newSaved, ...prev]);
        setShowSaved(true);
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.message ||
                          'Failed to save personalization';
      setError(errorMessage);
      console.error('Save personalization failed:', error);
    }
  };

  const generateTitle = (text: string): string => {
    if (!text) return 'Untitled';
    const words = text.split(' ').slice(0, 5).join(' ');
    return words.length > 30 ? words.substring(0, 30) + '...' : words;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isExpired = (dateString: string): boolean => {
    return new Date(dateString) < new Date();
  };

  // Don't render if not mounted or not open
  if (!mounted || !isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-2 sm:px-4 py-4">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-black opacity-50"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white dark:bg-zinc-900 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-zinc-200 dark:border-zinc-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-r from-violet-500 to-purple-500 rounded-lg">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
                    Personalized Explanation
                  </h2>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    {contentType === 'selected' ? 'Selected text' : 'Page content'} • {wordCount || content.split(' ').length} words
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex flex-col h-full max-h-[calc(90vh-8rem)]">
            <div className="flex-1 overflow-y-auto">
              <div className="p-6">
                {/* Error message */}
                {error && (
                  <div className="mb-4 p-3 text-sm text-red-700 bg-red-100 dark:text-red-200 dark:bg-red-900/30 rounded-md">
                    {error}
                  </div>
                )}

                {/* Content preview */}
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                    Original Content
                  </h3>
                  <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded-md text-sm text-zinc-600 dark:text-zinc-400 max-h-32 overflow-y-auto">
                    {(content || '').substring(0, 300)}{content && content.length > 300 ? '...' : ''}
                  </div>
                </div>

                {/* Generate button or explanation */}
                {!explanation ? (
                  <div className="text-center py-8">
                    <button
                      onClick={generatePersonalization}
                      disabled={isGenerating}
                      className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white font-medium rounded-lg hover:from-violet-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                          Generating personalized explanation...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-5 h-5 mr-2" />
                          Generate Personalized Explanation
                        </>
                      )}
                    </button>
                    <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">
                      AI will create a personalized explanation based on your profile
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Explanation */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                          Personalized Explanation
                        </h3>
                        <button
                          onClick={savePersonalization}
                          className="inline-flex items-center px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
                        >
                          <Save className="w-4 h-4 mr-1" />
                          Save
                        </button>
                      </div>
                      <div className="p-4 bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/20 rounded-md">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          {explanation.split('\n').map((paragraph, index) => (
                            <p key={index} className="mb-3 last:mb-0">
                              {paragraph}
                            </p>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Regenerate button */}
                    <div className="text-center">
                      <button
                        onClick={generatePersonalization}
                        disabled={isGenerating}
                        className="inline-flex items-center px-4 py-2 text-sm text-violet-600 dark:text-violet-400 hover:text-violet-700 dark:hover:text-violet-300 transition-colors"
                      >
                        <Sparkles className="w-4 h-4 mr-2" />
                        {isGenerating ? 'Regenerating...' : 'Regenerate'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Saved Personalizations */}
            {savedPersonalizations.length > 0 && (
              <div className="border-t border-zinc-200 dark:border-zinc-700">
                <div className="px-6 py-4">
                  <button
                    onClick={() => setShowSaved(!showSaved)}
                    className="flex items-center justify-between w-full text-left"
                  >
                    <div className="flex items-center space-x-2">
                      <Clock className="w-4 h-4 text-zinc-500" />
                      <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                        Saved Personalizations ({savedPersonalizations.length})
                      </span>
                    </div>
                    <ChevronRight
                      className={`w-4 h-4 text-zinc-500 transition-transform ${
                        showSaved ? 'rotate-90' : ''
                      }`}
                    />
                  </button>

                  {showSaved && (
                    <div className="mt-4 space-y-3 max-h-48 overflow-y-auto">
                      {savedPersonalizations.map((saved) => (
                        <div
                          key={saved.id}
                          className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded-md cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
                          onClick={() => setExplanation(saved.explanation)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate">
                                {saved.title}
                              </p>
                              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                                {formatDate(saved.created_at)}
                                {isExpired(saved.expires_at) && (
                                  <span className="ml-2 text-red-500">Expired</span>
                                )}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};