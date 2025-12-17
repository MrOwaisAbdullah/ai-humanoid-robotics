/**
 * Personalization Library Modal
 * View and manage saved personalized explanations.
 */

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiRequest } from '../../services/api';
import { Loader2, X, Clock, FileText, Trash2, Search, BookOpen, Calendar } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface PersonalizationLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SavedPersonalization {
  id: string;
  title: string;
  original_content: string;
  explanation: string;
  created_at: string;
  expires_at: string;
}

export const PersonalizationLibraryModal: React.FC<PersonalizationLibraryModalProps> = ({
  isOpen,
  onClose
}) => {
  const { user } = useAuth();
  const [savedItems, setSavedItems] = useState<SavedPersonalization[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<SavedPersonalization | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isOpen && mounted && user) {
      loadLibrary();
    }
  }, [isOpen, mounted, user]);

  const loadLibrary = async () => {
    setIsLoading(true);
    try {
      const response = await apiRequest.get('/api/v1/personalization/list');
      if (response.data && response.data.personalizations) {
        setSavedItems(response.data.personalizations);
      }
    } catch (error) {
      console.error('Failed to load library:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short', 
      day: 'numeric', 
      year: 'numeric'
    });
  };

  // Render markdown content with syntax highlighting (Shared logic)
  const renderMarkdown = (text: string) => {
    const components = {
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
      p: ({children, ...props}: any) => (
        <p {...props} className="markdown-paragraph mb-4 last:mb-0 text-zinc-700 dark:text-zinc-300 leading-relaxed">
          {children}
        </p>
      ),
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
          <div className="code-block-wrapper relative group my-4">
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
      blockquote: ({children, ...props}: any) => (
        <blockquote {...props} className="markdown-blockquote my-4 pl-4 border-l-4 border-[#0d9488] dark:border-[#14b8a6] bg-zinc-50 dark:bg-zinc-900/50 text-zinc-700 dark:text-zinc-300 italic">
          {children}
        </blockquote>
      ),
      strong: ({children, ...props}: any) => (
        <strong {...props} className="font-semibold text-zinc-900 dark:text-zinc-100">
          {children}
        </strong>
      ),
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

  const filteredItems = savedItems.filter(item => 
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.original_content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!mounted || !isOpen) return null;

  const modalContent = (
    <div className="fixed inset-0 z-[99999] overflow-y-auto" style={{ zIndex: 99999 }}>
      <div className="flex items-center justify-center min-h-screen px-4 py-6">
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onClick={onClose} />

        <div className="relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl w-full max-w-5xl h-[85vh] shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          
          {/* Header */}
          <div className="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/50 backdrop-blur flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#0d9488]/10 dark:bg-[#14b8a6]/20 rounded-lg">
                <BookOpen className="w-5 h-5 text-[#0d9488] dark:text-[#14b8a6]" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Personalization Library</h2>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Your saved explanations</p>
              </div>
            </div>
            <button onClick={onClose} className="p-2 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-1 overflow-hidden">
            {/* Sidebar / List */}
            <div className={`w-full md:w-1/3 border-r border-zinc-200 dark:border-zinc-800 flex flex-col bg-zinc-50/50 dark:bg-zinc-900/50 ${selectedItem ? 'hidden md:flex' : 'flex'}`}>
              
              {/* Search */}
              <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="text"
                    placeholder="Search saved items..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-[#0d9488] focus:border-transparent outline-none transition-all"
                  />
                </div>
              </div>

              {/* List */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {isLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-[#0d9488]" />
                  </div>
                ) : filteredItems.length === 0 ? (
                  <div className="text-center py-12 text-zinc-500 text-sm">
                    {searchQuery ? 'No matches found' : 'No saved items yet'}
                  </div>
                ) : (
                  filteredItems.map(item => (
                    <div
                      key={item.id}
                      onClick={() => setSelectedItem(item)}
                      className={`p-3 rounded-lg cursor-pointer transition-all border ${selectedItem?.id === item.id
                          ? 'bg-white dark:bg-zinc-800 border-[#0d9488] shadow-sm'
                          : 'bg-transparent border-transparent hover:bg-zinc-100 dark:hover:bg-zinc-800/50 hover:border-zinc-200 dark:hover:border-zinc-700'
                      }`}
                    >
                      <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate mb-1">{item.title}</h3>
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(item.created_at)}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Content View */}
            <div className={`flex-1 flex flex-col bg-white dark:bg-zinc-900 overflow-hidden ${!selectedItem ? 'hidden md:flex' : 'flex'}`}>
              {selectedItem ? (
                <>
                  <div className="p-6 border-b border-zinc-200 dark:border-zinc-800 flex justify-between items-start bg-zinc-50/30 dark:bg-black/20">
                    <div>
                      <button 
                        onClick={() => setSelectedItem(null)}
                        className="md:hidden mb-2 text-xs text-zinc-500 hover:text-zinc-900 flex items-center gap-1"
                      >
                        ← Back to list
                      </button>
                      <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50 mb-2">{selectedItem.title}</h2>
                      <div className="flex items-center gap-4 text-xs text-zinc-500">
                        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {formatDate(selectedItem.created_at)}</span>
                        <span className="flex items-center gap-1 text-[#0d9488] font-medium"><Clock className="w-3 h-3" /> Expires: {formatDate(selectedItem.expires_at)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    {/* Source Context */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                        <FileText className="w-3 h-3" /> Original Context
                      </div>
                      <div className="p-4 bg-zinc-50 dark:bg-zinc-950/50 border border-zinc-100 dark:border-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400 font-mono leading-relaxed max-h-48 overflow-y-auto">
                        {selectedItem.original_content}
                      </div>
                    </div>

                    {/* Explanation */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs font-semibold text-[#0d9488] uppercase tracking-wider">
                        <div className="w-2 h-2 rounded-full bg-[#0d9488]" /> Personalized Explanation
                      </div>
                      <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-sm">
                        {renderMarkdown(selectedItem.explanation)}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-zinc-400 p-8 text-center">
                  <div className="w-16 h-16 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-4">
                    <BookOpen className="w-8 h-8 opacity-50" />
                  </div>
                  <p>Select an item from the library to view details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};
