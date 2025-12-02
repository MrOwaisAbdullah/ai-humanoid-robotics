import React, { useState, useRef, useEffect } from 'react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
}

/**
 * Auto-resizing message input
 * Submit on Enter, newline on Shift+Enter
 */
export default function MessageInput({
  onSend,
  disabled,
  placeholder = "Type your message..."
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height =
        `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  return (
    <form onSubmit={handleSubmit} className="p-4 md:p-5 border-t border-gray-200 bg-white flex gap-3 items-end">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 p-3 border border-gray-200 rounded-lg text-sm font-sans resize-none max-h-[150px] overflow-y-auto bg-white text-gray-800 transition-colors focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/10 disabled:opacity-60 disabled:cursor-not-allowed"
        rows={1}
        aria-label="Message input"
      />

      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-none text-lg cursor-pointer transition-all shrink-0 flex items-center justify-center hover:shadow-md hover:-translate-y-px active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:transform-none"
      >
        {disabled ? '⏳' : '➤'}
      </button>
    </form>
  );
}