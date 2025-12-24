/**
 * Personalization modal for generating and managing personalized content explanations.
 */

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../../context/AuthContext';
import { apiRequest } from '../../services/api';
import { Loader2, Sparkles, Save, X, ChevronRight, Clock, User, FileText, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface PersonalizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: string;
  contentType: 'selected' | 'page';
  wordCount?: number;
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

  // Render markdown content with syntax highlighting
  const renderMarkdown = (text: string) => {
    const components = {
      // Custom component for headings
      h1: ({children, ...props}: any) => (
        <h1 {...props} className="markdown-heading heading-1 text-2xl font-bold mb-4 mt-6 first:mt-0 text-zinc-900 dark:text-zinc-100">
          {children}
        </h1>
      ),
      h2: ({children, ...props}: any) => (
        <h2 {...props} className="markdown-heading heading-2 text-xl font-bold mb-3 mt-6 first:mt-0 text-zinc-900 dark:text-zinc-100 border-b border-zinc-200 dark:border-zinc-700 pb-2">
          {children}
        </h2>
      ),
      h3: ({children, ...props}: any) => (
        <h3 {...props} className="markdown-heading heading-3 text-lg font-semibold mb-3 mt-5 first:mt-0 text-zinc-900 dark:text-zinc-100">
          {children}
        </h3>
      ),
      h4: ({children, ...props}: any) => (
        <h4 {...props} className="markdown-heading heading-4 text-base font-semibold mb-2 mt-4 first:mt-0 text-zinc-900 dark:text-zinc-100">
          {children}
        </h4>
      ),
      h5: ({children, ...props}: any) => (
        <h5 {...props} className="markdown-heading heading-5 text-sm font-semibold mb-2 mt-4 first:mt-0 text-zinc-900 dark:text-zinc-100">
          {children}
        </h5>
      ),
      h6: ({children, ...props}: any) => (
        <h6 {...props} className="markdown-heading heading-6 text-sm font-medium mb-2 mt-4 first:mt-0 text-zinc-700 dark:text-zinc-300">
          {children}
        </h6>
      ),
      // Custom paragraph component
      p: ({children, ...props}: any) => (
        <p {...props} className="markdown-paragraph mb-4 last:mb-0 text-zinc-700 dark:text-zinc-300 leading-relaxed">
          {children}
        </p>
      ),
      // Custom list components
      ul: ({children, ...props}: any) => (
        <ul {...props} className="markdown-list mb-4 pl-6 list-disc text-zinc-700 dark:text-zinc-300">
          {children}
        </ul>
      ),
      ol: ({children, ...props}: any) => (
        <ol {...props} className="markdown-list mb-4 pl-6 list-decimal text-zinc-700 dark:text-zinc-300">
          {children}
        </ol>
      ),
      li: ({children, ...props}: any) => (
        <li {...props} className="markdown-list-item mb-1 leading-relaxed">
          {children}
        </li>
      ),
      // Code block component with syntax highlighting
      code: ({node, inline, className, children, ...props}: any) => {
        const match = /language-(\w+)/.exec(className || '');
        const isInlineCode = inline !== undefined
          ? inline
          : !match && !String(children).includes('\n');

        if (isInlineCode) {
          return (
            <code
              className="inline-code px-1.5 py-0.5 text-xs font-mono bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 rounded"
              {...props}
            >
              {children}
            </code>
          );
        }

        return (
          <div className="code-block-wrapper relative group">
            <div className="flex items-center justify-between bg-zinc-900 text-zinc-100 px-4 py-2 text-xs font-mono rounded-t-md">
              <span>{className ? className.replace('language-', '') : 'code'}</span>
            </div>
            <SyntaxHighlighter
              style={oneDark}
              language={match ? match[1] : 'text'}
              PreTag="div"
              customStyle={{
                margin: 0,
                borderTopLeftRadius: 0,
                borderTopRightRadius: '0.5rem',
                borderBottomLeftRadius: '0.5rem',
                borderBottomRightRadius: '0.5rem',
                fontSize: '0.875rem',
              }}
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          </div>
        );
      },
      // Custom blockquote
      blockquote: ({children, ...props}: any) => (
        <blockquote {...props} className="markdown-blockquote my-4 pl-4 border-l-4 border-[#0d9488] dark:border-[#14b8a6] bg-zinc-50 dark:bg-zinc-900/50 text-zinc-700 dark:text-zinc-300 italic">
          {children}
        </blockquote>
      ),
      // Custom table components
      table: ({children, ...props}: any) => (
        <table {...props} className="markdown-table w-full border-collapse my-4 text-sm">
          {children}
        </table>
      ),
      thead: ({children, ...props}: any) => (
        <thead {...props} className="bg-zinc-50 dark:bg-zinc-900/50">
          {children}
        </thead>
      ),
      tbody: ({children, ...props}: any) => (
        <tbody {...props} className="divide-y divide-zinc-200 dark:divide-zinc-700">
          {children}
        </tbody>
      ),
      tr: ({children, ...props}: any) => (
        <tr {...props} className="hover:bg-zinc-50 dark:hover:bg-zinc-900/30">
          {children}
        </tr>
      ),
      th: ({children, ...props}: any) => (
        <th {...props} className="px-4 py-2 text-left font-semibold text-zinc-900 dark:text-zinc-100">
          {children}
        </th>
      ),
      td: ({children, ...props}: any) => (
        <td {...props} className="px-4 py-2 text-zinc-700 dark:text-zinc-300">
          {children}
        </td>
      ),
      // Horizontal rule
      hr: ({...props}: any) => (
        <hr {...props} className="markdown-hr my-6 border-0 h-px bg-zinc-200 dark:bg-zinc-700" />
      ),
      // Strong/Bold
      strong: ({children, ...props}: any) => (
        <strong {...props} className="font-semibold text-zinc-900 dark:text-zinc-100">
          {children}
        </strong>
      ),
      // Emphasis/Italic
      em: ({children, ...props}: any) => (
        <em {...props} className="italic text-zinc-700 dark:text-zinc-300">
          {children}
        </em>
      ),
    };

    return (
      <div className="markdown-content">
        <ReactMarkdown
          remarkPlugins={[]}
          components={components}
        >
          {text}
        </ReactMarkdown>
      </div>
    );
  };

  const isExpired = (dateString: string): boolean => {
    return new Date(dateString) < new Date();
  };

  // Don't render if not mounted or not open
  if (!mounted || !isOpen) {
    return null;
  }

  const modalContent = (
    <div className="fixed inset-0 z-[99999] overflow-y-auto" style={{ zIndex: 99999 }}>
      <div className="flex items-center justify-center min-h-screen px-4 py-6">
        {/* Background overlay with blur */}
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />

        {/* Modal Container */}
        <div className="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl w-full max-w-4xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col animate-in fade-in zoom-in-95 duration-200">
          
          {/* Header */}
          <div className="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/50 backdrop-blur sticky top-0 z-10 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-[#0d9488]/10 dark:bg-[#14b8a6]/20 rounded-lg">
                  <Sparkles className="w-5 h-5 text-[#0d9488] dark:text-[#14b8a6]" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                    Personalized Explanation
                  </h2>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">
                    Based on your background & expertise
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-zinc-400 hover:text-zinc-900 dark:text-zinc-500 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto bg-zinc-50/50 dark:bg-black/20">
            <div className="p-6 space-y-6">
              
              {/* Error Alert */}
              {error && (
                <div className="p-4 text-sm text-red-600 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-2 shrink-0" />
                  {error}
                </div>
              )}

              {/* Source Context Card */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-zinc-500 dark:text-zinc-400">
                  <FileText className="w-4 h-4" />
                  <span>Original Content</span>
                  <span className="ml-auto text-xs bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700">
                    {contentType === 'selected' ? 'Selection' : 'Full Page'} • {wordCount || content.split(' ').length} words
                  </span>
                </div>
                <div className="p-3 bg-zinc-50 dark:bg-zinc-950/50 border border-zinc-100 dark:border-zinc-800 rounded-md text-sm text-zinc-600 dark:text-zinc-400 max-h-32 overflow-y-auto leading-relaxed font-mono text-xs">
                  {(content || '').substring(0, 300)}{content && content.length > 300 ? '...' : ''}
                </div>
              </div>

              {/* AI Output Section */}
              {!explanation ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="w-16 h-16 bg-[#0d9488]/5 dark:bg-[#14b8a6]/10 rounded-2xl flex items-center justify-center mb-4">
                    <Sparkles className="w-8 h-8 text-[#0d9488] dark:text-[#14b8a6] opacity-50" />
                  </div>
                  <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
                    Ready to Personalize
                  </h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 max-w-sm mb-8">
                    Our AI will analyze this content and explain it using concepts and analogies that match your specific background.
                  </p>
                  
                  <button
                    onClick={generatePersonalization}
                    disabled={isGenerating}
                    className="group relative inline-flex items-center justify-center px-6 py-2.5 text-sm font-medium text-white transition-all duration-200 bg-[#0d9488] hover:bg-[#0f766e] dark:bg-[#14b8a6] dark:hover:bg-[#0d9488] rounded-lg shadow-md hover:shadow-lg disabled:opacity-70 disabled:cursor-not-allowed disabled:shadow-none focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0d9488] dark:ring-offset-zinc-900"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing & Personalizing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2 transition-transform group-hover:scale-110" />
                        Generate Explanation
                      </>
                    )}
                  </button>
                </div>
              ) : (
                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#0d9488] dark:bg-[#14b8a6]" />
                      Personalized Explanation
                    </h3>
                    <div className="flex gap-2">
                      <button
                        onClick={generatePersonalization}
                        disabled={isGenerating}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors"
                      >
                        {isGenerating ? <Loader2 className="w-3 h-3 mr-1.5 animate-spin" /> : <Sparkles className="w-3 h-3 mr-1.5" />}
                        Regenerate
                      </button>
                      <button
                        onClick={savePersonalization}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-[#0d9488] hover:bg-[#0f766e] dark:bg-[#14b8a6] dark:hover:bg-[#0d9488] rounded-md shadow-sm transition-colors"
                      >
                        <Save className="w-3 h-3 mr-1.5" />
                        Save to Library
                      </button>
                    </div>
                  </div>
                  
                  <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-sm">
                    {renderMarkdown(explanation)}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Saved Personalizations Drawer (Bottom) */}
          {savedPersonalizations.length > 0 && (
            <div className="border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex-shrink-0">
              <button
                onClick={() => setShowSaved(!showSaved)}
                className="w-full flex items-center justify-between px-6 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors group"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-zinc-600 dark:text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-200">
                  <Clock className="w-4 h-4" />
                  <span>Saved Personalizations</span>
                  <span className="bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full text-xs text-zinc-500 dark:text-zinc-500 border border-zinc-200 dark:border-zinc-700">
                    {savedPersonalizations.length}
                  </span>
                </div>
                <ChevronRight
                  className={`w-4 h-4 text-zinc-400 transition-transform duration-200 ${showSaved ? 'rotate-90' : ''}`}
                />
              </button>

              {/* Expandable List */}
              <div 
                className={`overflow-hidden transition-all duration-300 ease-in-out bg-zinc-50/50 dark:bg-black/20 ${showSaved ? 'max-h-60 border-t border-zinc-200 dark:border-zinc-800' : 'max-h-0'}`}
              >
                <div className="p-4 grid gap-3 overflow-y-auto max-h-60">
                  {savedPersonalizations.map((saved) => (
                    <div
                      key={saved.id}
                      onClick={() => setExplanation(saved.explanation)}
                      className="group flex flex-col p-3 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg cursor-pointer hover:border-[#0d9488]/50 dark:hover:border-[#14b8a6]/50 hover:shadow-md transition-all duration-200 relative overflow-hidden"
                    >
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#0d9488] dark:bg-[#14b8a6] opacity-0 group-hover:opacity-100 transition-opacity" />
                      
                      <div className="flex items-start justify-between mb-1">
                        <h4 className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate pr-4">
                          {saved.title}
                        </h4>
                        {isExpired(saved.expires_at) && (
                          <span className="text-[10px] uppercase tracking-wider font-bold text-red-500 bg-red-50 dark:bg-red-900/20 px-1.5 py-0.5 rounded">
                            Expired
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-4 text-xs text-zinc-500 dark:text-zinc-500">
                        <span>{formatDate(saved.created_at)}</span>
                        <span className="truncate max-w-[200px] opacity-75">
                          {saved.original_content.substring(0, 40)}...
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return mounted ? createPortal(modalContent, document.body) : null;
};
