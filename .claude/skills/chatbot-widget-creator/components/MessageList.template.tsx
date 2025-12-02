import React, { useEffect, useRef } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

/**
 * Scrollable message list
 * Auto-scrolls to bottom on new messages
 */
export default function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4 bg-white scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent hover:scrollbar-thumb-gray-400">
      {messages.length === 0 && (
        <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
          👋 Hi! Ask me anything about the book.
        </div>
      )}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex flex-col gap-1 animate-in slide-in-from-bottom-2 duration-300 ${
            message.role === 'user' ? 'items-end' : 'items-start'
          }`}
        >
          <div 
            className={`max-w-[80%] px-4 py-3 rounded-xl text-sm leading-relaxed break-words ${
              message.role === 'user' 
                ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-br-sm' 
                : 'bg-slate-100 text-gray-800 rounded-bl-sm'
            }`}
          >
            {message.content}
          </div>
          <div className="text-[11px] text-gray-500 px-1">
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="flex gap-1.5 px-4 py-3 bg-slate-100 rounded-xl w-fit items-center">
          <div className="text-xs text-gray-500 mr-1">Thinking...</div>
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce [animation-delay:-0.32s]"></div>
            <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce [animation-delay:-0.16s]"></div>
            <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce"></div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}