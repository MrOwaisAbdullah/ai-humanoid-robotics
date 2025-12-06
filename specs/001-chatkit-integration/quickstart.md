# Quickstart: ChatKit Integration

This guide will help you integrate the OpenAI ChatKit widget into your Docusaurus site with RAG backend support.

## Prerequisites

- Node.js 18+ installed
- Backend API running (FastAPI with `/chat` endpoint)
- Docusaurus site already configured

## Step 1: Install Dependencies

```bash
cd your-docusaurus-site
npm install @openai/chatkit-react@latest
npm install framer-motion@latest
npm install lucide-react@latest
```

## Step 2: Create Chat Widget Component

Create `src/components/ChatWidget/index.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { ChatKit, useChatKit } from '@openai/chatkit-react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X } from 'lucide-react';
import { useTextSelection } from './hooks/useTextSelection';
import { useSessionPersistence } from './hooks/useSessionPersistence';

// Chat Panel Component
const ChatPanel = ({ isOpen, onClose, children }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        className="fixed bottom-20 right-4 w-full max-w-md h-[600px]
                   bg-white/10 backdrop-blur-md border border-white/20
                   rounded-2xl shadow-2xl overflow-hidden z-50"
        style={{
          background: 'rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)'
        }}
      >
        <div className="relative h-full">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 rounded-lg
                       bg-white/10 hover:bg-white/20 text-white/70
                       hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="p-4">
            {children}
          </div>
        </div>
      </motion.div>
    )}
  </AnimatePresence>
);

// Main Chat Widget
export const ChatWidget = ({ apiEndpoint }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const { saveSession, loadSession } = useSessionPersistence();

  const { control, sendUserMessage, setThreadId } = useChatKit({
    api: {
      url: apiEndpoint,
    },
    theme: 'dark',
    composer: {
      placeholder: 'Ask anything about the content...'
    }
  });

  // Load saved session
  useEffect(() => {
    const session = loadSession();
    if (session?.threadId) {
      setThreadId(session.threadId);
    }
  }, [loadSession, setThreadId]);

  // Handle text selection
  useTextSelection({
    onTextSelected: (text) => {
      if (text && text.length > 3) {
        setSelectedText(text);
        if (!isOpen) setIsOpen(true);
      }
    }
  });

  // Save session state
  useEffect(() => {
    saveSession({ isOpen, threadId: control.threadId });
  }, [isOpen, control.threadId, saveSession]);

  const handleAskAboutSelection = () => {
    if (selectedText) {
      sendUserMessage({
        text: `Can you help me understand: "${selectedText}"`
      });
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 right-4 z-50 p-4 bg-blue-500
                   hover:bg-blue-600 text-white rounded-full
                   shadow-lg transition-all duration-200
                   hover:scale-105 active:scale-95"
      >
        <MessageCircle className="w-6 h-6" />
      </button>

      {/* Chat Panel */}
      <ChatPanel isOpen={isOpen} onClose={() => setIsOpen(false)}>
        {selectedText && (
          <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30
                        rounded-lg backdrop-blur-sm">
            <p className="text-sm text-blue-300 mb-2">Selected text:</p>
            <p className="text-sm text-gray-200 italic">"{selectedText}"</p>
            <button
              onClick={handleAskAboutSelection}
              className="mt-2 px-3 py-1 bg-blue-500 hover:bg-blue-600
                         text-white text-xs rounded-md transition-colors"
            >
              Ask about this
            </button>
          </div>
        )}

        <ChatKit control={control} className="h-full" />
      </ChatPanel>
    </>
  );
};
```

## Step 3: Create Custom Hooks

Create `src/components/ChatWidget/hooks/useTextSelection.ts`:

```typescript
import { useCallback, useEffect, useRef } from 'react';

export const useTextSelection = ({ onTextSelected }) => {
  const debounceRef = useRef(null);

  const handleSelection = useCallback(() => {
    const selection = window.getSelection();
    if (!selection) return;

    const selectedText = selection.toString().trim();

    if (selectedText.length >= 3) {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      debounceRef.current = setTimeout(() => {
        onTextSelected?.(selectedText);
      }, 300);
    }
  }, [onTextSelected]);

  useEffect(() => {
    document.addEventListener('mouseup', handleSelection);
    document.addEventListener('keyup', handleSelection);

    return () => {
      document.removeEventListener('mouseup', handleSelection);
      document.removeEventListener('keyup', handleSelection);
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [handleSelection]);
};
```

Create `src/components/ChatWidget/hooks/useSessionPersistence.ts`:

```typescript
export const useSessionPersistence = (key = 'chat-session') => {
  const saveSession = (session) => {
    try {
      localStorage.setItem(key, JSON.stringify(session));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  };

  const loadSession = () => {
    try {
      const stored = localStorage.getItem(key);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Failed to load session:', error);
      return null;
    }
  };

  const clearSession = () => {
    localStorage.removeItem(key);
  };

  return { saveSession, loadSession, clearSession };
};
```

## Step 4: Integrate with Docusaurus

Update `src/theme/Root.tsx`:

```typescript
import React from 'react';
import Layout from '@theme/Layout';
import { ChatWidget } from '@site/src/components/ChatWidget';

export default function Root({ children }) {
  return (
    <Layout>
      {children}
      <ChatWidget
        apiEndpoint={process.env.CHAT_API_ENDPOINT || 'http://localhost:7860'}
      />
    </Layout>
  );
}
```

## Step 5: Configure Environment

Create `.env.local` in your Docusaurus root:

```
# RAG Backend API endpoint (from 1-rag-backend branch)
CHAT_API_ENDPOINT=http://localhost:7860
```

## Step 6: Run Development Server

```bash
# Terminal 1: Start RAG backend (from 1-rag-backend branch)
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 7860 --reload

# Terminal 2: Start frontend
npm run start
```

## Step 7: Test the Integration

1. Open your Docusaurus site
2. Click the blue chat button in the bottom-right
3. Type a message like "What is forward kinematics?"
4. Highlight any text on the page
5. Click "Ask about this" in the chat

## Customization Options

### Glassmorphism Effect
Modify the styling in `ChatPanel` component:

```css
/* Adjust blur amount */
backdrop-filter: blur(12px); /* Default: 20px */

/* Adjust transparency */
background: 'rgba(255, 255, 255, 0.12)'; /* Default: 0.08 */

/* Adjust border opacity */
border: '1px solid rgba(255, 255, 255, 0.25)'; /* Default: 0.2 */
```

### Mobile Behavior
Add responsive styles:

```css
/* For mobile devices */
@media (max-width: 768px) {
  .chat-panel {
    bottom: 0 !important;
    right: 0 !important;
    left: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    height: 70vh !important;
    border-radius: 20px 20px 0 0 !important;
  }
}
```

### API Endpoint Configuration
For production, update the environment variable:

```
CHAT_API_ENDPOINT=https://your-backend-domain.com
```

## Troubleshooting

### Common Issues

1. **CORS Error**: Ensure backend allows your frontend domain
2. **SSE Not Working**: Check that backend endpoint returns `text/event-stream`
3. **ChatKit Not Loading**: Verify API endpoint is accessible
4. **Glassmorphism Not Visible**: Check browser compatibility for backdrop-filter

### Debug Mode

Enable debug logging:

```typescript
// In ChatWidget component
const { control } = useChatKit({
  // ... other props
  debug: true, // Enable ChatKit debug logs
});
```

## Next Steps

1. Implement user authentication (optional)
2. Add conversation export functionality
3. Implement rate limiting
4. Add analytics tracking
5. Customize ChatKit themes