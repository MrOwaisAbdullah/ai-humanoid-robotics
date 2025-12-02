import React from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatPanelProps {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  selectedText: string | null;
  onClose: () => void;
  onSendMessage: (message: string) => void;
  onClearError: () => void;
  onClearSelection: () => void;
}

/**
 * Expanded chat panel
 * Full chat interface with messages and input
 */
export default function ChatPanel({
  messages,
  isLoading,
  error,
  selectedText,
  onClose,
  onSendMessage,
  onClearError,
  onClearSelection
}: ChatPanelProps) {
  return (
    <div className="fixed bottom-6 right-6 w-[400px] h-[600px] max-h-[calc(100vh-48px)] bg-white rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden animate-in slide-in-from-bottom-5 duration-300 md:w-full md:h-full md:bottom-0 md:right-0 md:rounded-none md:max-h-screen">
      {/* Header */}
      <div className="p-5 bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex justify-between items-center rounded-t-2xl md:rounded-none">
        <span className="text-lg font-semibold m-0">Ask a Question</span>
        <button
          onClick={onClose}
          className="bg-white/20 border-none text-white text-xl w-8 h-8 rounded-lg cursor-pointer transition-colors flex items-center justify-center hover:bg-white/30"
          aria-label="Close Chat"
        >
          ✕
        </button>
      </div>

      {/* Selection Context (if text selected) */}
      {selectedText && (
        <div className="px-5 py-3 bg-gradient-to-br from-amber-200 to-orange-300 border-b border-black/5">
          <div className="text-xs font-semibold text-gray-800 mb-1.5 flex justify-between items-center">
            Selected text:
            <button onClick={onClearSelection} className="bg-transparent border-none cursor-pointer px-1 text-base text-gray-800 opacity-60 hover:opacity-100">✕</button>
          </div>
          <div className="text-sm italic leading-snug text-gray-600">
            "{selectedText.substring(0, 100)}
            {selectedText.length > 100 ? '...' : ''}"
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="px-5 py-3 bg-gradient-to-br from-red-400 to-red-600 text-white flex justify-between items-center text-sm">
          {error}
          <button
            onClick={onClearError}
            className="bg-white/20 border-none text-white cursor-pointer px-2 py-1 rounded hover:bg-white/30"
          >
            ✕
          </button>
        </div>
      )}

      {/* Messages */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
      />

      {/* Input */}
      <MessageInput
        onSend={onSendMessage}
        disabled={isLoading}
      />
    </div>
  );
}