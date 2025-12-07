# Implementing a ChatGPT-Style Chatbot UI in React

A comprehensive guide for building a modern chatbot interface using React, react-markdown, framer-motion, and react-syntax-highlighter.

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Core Components](#core-components)
3. [Message Rendering with Markdown](#message-rendering-with-markdown)
4. [Syntax Highlighting for Code](#syntax-highlighting-for-code)
5. [Animations with Framer Motion](#animations-with-framer-motion)
6. [Streaming Message Effects](#streaming-message-effects)
7. [Complete Chat Interface Example](#complete-chat-interface-example)
8. [Best Practices](#best-practices)

## Installation & Setup

### Required Packages

```bash
npm install react-markdown framer-motion react-syntax-highlighter
npm install --save-dev @types/react-syntax-highlighter  # TypeScript support
```

### Optional Plugins for Enhanced Markdown

```bash
npm install remark-gfm  # GitHub Flavored Markdown support
```

## Core Components

### 1. Message Component Structure

```jsx
import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

const Message = ({ message, isStreaming = false }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`message ${message.role}`}
    >
      <div className="message-content">
        {renderMessageContent(message.content, isStreaming)}
      </div>
    </motion.div>
  );
};
```

## Message Rendering with Markdown

### Basic react-markdown Setup

```jsx
import ReactMarkdown from 'react-markdown';

const renderMessageContent = (content, isStreaming) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }) {
          // Custom code block rendering (see syntax highlighting section)
          return <CodeBlock {...props} inline={inline} className={className}>
            {children}
          </CodeBlock>;
        },
        // Custom component mapping for other elements
        a: ({ node, ...props }) => (
          <a target="_blank" rel="noopener noreferrer" {...props} />
        ),
      }}
    >
      {isStreaming ? content + '▋' : content}
    </ReactMarkdown>
  );
};
```

### Key react-markdown Props

- `children`: The markdown content string
- `remarkPlugins`: Array of remark plugins for processing
- `rehypePlugins`: Array of rehype plugins for HTML transformation
- `components`: Object mapping markdown elements to React components
- `skipHtml`: Boolean to skip HTML in markdown
- `allowedElements/disallowedElements`: Control which HTML elements are allowed

## Syntax Highlighting for Code

### Integration with react-markdown

```jsx
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, prism } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeBlock = ({ inline, className, children, ...props }) => {
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';

  return !inline && match ? (
    <SyntaxHighlighter
      style={vscDarkPlus}  // or prism for light theme
      language={language}
      PreTag="div"
      showLineNumbers={true}
      wrapLines={true}
      customStyle={{
        borderRadius: '8px',
        padding: '16px',
        fontSize: '14px',
        lineHeight: '1.5',
      }}
      codeTagProps={{
        style: {
          fontFamily: 'Fira Code, Monaco, Consolas, monospace',
        },
      }}
      {...props}
    >
      {String(children).replace(/\n$/, '')}
    </SyntaxHighlighter>
  ) : (
    <code className={className} {...props}>
      {children}
    </code>
  );
};
```

### Available Syntax Highlighter Options

```jsx
// Import different themes
import {
  vscDarkPlus,  // VS Code Dark+
  prism,        // Default Prism theme
  atomDark,     // Atom Dark theme
  darcula,      // IntelliJ Darcula
  vs,           // Visual Studio Light
} from 'react-syntax-highlighter/dist/esm/styles/prism';

// Line number styling
const lineNumberStyle = {
  color: '#8b949e',
  paddingRight: '1em',
  userSelect: 'none',
  opacity: 0.5,
};

// Custom code block container
const CodeContainer = ({ children, language }) => (
  <div className="code-block-container">
    <div className="code-header">
      <span className="language-label">{language}</span>
      <button onClick={() => copyToClipboard(children)}>
        Copy
      </button>
    </div>
    {children}
  </div>
);
```

## Animations with Framer Motion

### Message Entry Animations

```jsx
import { motion, AnimatePresence } from 'framer-motion';

const messageVariants = {
  hidden: {
    opacity: 0,
    y: 20,
    scale: 0.95
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.3,
      ease: "easeOut",
      staggerChildren: 0.1
    }
  },
  exit: {
    opacity: 0,
    y: -20,
    scale: 0.95,
    transition: { duration: 0.2 }
  }
};

const MessageList = ({ messages }) => {
  return (
    <AnimatePresence mode="popLayout">
      {messages.map((message, index) => (
        <motion.div
          key={message.id}
          variants={messageVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          layout
          transition={{
            layout: { duration: 0.3 },
            opacity: { duration: 0.2 },
            transform: { duration: 0.3 },
          }}
        >
          <Message message={message} />
        </motion.div>
      ))}
    </AnimatePresence>
  );
};
```

### Typing Indicator Animation

```jsx
const TypingIndicator = () => {
  return (
    <motion.div
      className="typing-indicator"
      animate={{ opacity: [0.4, 1, 0.4] }}
      transition={{
        repeat: Infinity,
        duration: 1.5,
        ease: "easeInOut"
      }}
    >
      <div className="typing-dots">
        <motion.span
          animate={{ y: [0, -10, 0] }}
          transition={{ repeat: Infinity, duration: 0.6 }}
        >.</motion.span>
        <motion.span
          animate={{ y: [0, -10, 0] }}
          transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }}
        >.</motion.span>
        <motion.span
          animate={{ y: [0, -10, 0] }}
          transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }}
        >.</motion.span>
      </div>
    </motion.div>
  );
};
```

### Scroll Animations

```jsx
import { useScroll } from 'framer-motion';
import { useEffect, useRef } from 'react';

const ChatContainer = ({ children }) => {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({ container: containerRef });

  useEffect(() => {
    // Auto-scroll to bottom on new messages
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [children]);

  return (
    <motion.div
      ref={containerRef}
      className="chat-container"
      style={{
        opacity: scrollYProgress,
        transform: `translateY(${1 - scrollYProgress.get() * 20}px)`
      }}
    >
      {children}
    </motion.div>
  );
};
```

## Streaming Message Effects

### Character-by-Character Animation

```jsx
const StreamingText = ({ text, isComplete = false }) => {
  return (
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.01 }}
    >
      {text}
      {!isComplete && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{
            repeat: Infinity,
            duration: 0.8,
            repeatDelay: 0.4
          }}
        >
          ▋
        </motion.span>
      )}
    </motion.span>
  );
};

const StreamingMessage = ({ content, isStreaming }) => {
  const [displayedContent, setDisplayedContent] = useState('');

  useEffect(() => {
    if (isStreaming && content !== displayedContent) {
      const timeout = setTimeout(() => {
        setDisplayedContent(content);
      }, 30);
      return () => clearTimeout(timeout);
    }
  }, [content, isStreaming, displayedContent]);

  return (
    <ReactMarkdown components={markdownComponents}>
      {isStreaming ? displayedContent : content}
    </ReactMarkdown>
  );
};
```

### Word-by-Word Reveal Animation

```jsx
const WordReveal = ({ text }) => {
  const words = text.split(' ');

  const container = {
    hidden: { opacity: 0 },
    visible: (i = 1) => ({
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.04 * i,
      },
    }),
  };

  const child = {
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        damping: 12,
        stiffness: 100,
      },
    },
    hidden: {
      opacity: 0,
      y: 20,
      transition: {
        type: "spring",
        damping: 12,
        stiffness: 100,
      },
    },
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="visible"
    >
      {words.map((word, index) => (
        <motion.span
          key={index}
          variants={child}
          style={{ display: 'inline-block', marginRight: '0.25em' }}
        >
          {word}
        </motion.span>
      ))}
    </motion.div>
  );
};
```

## Complete Chat Interface Example

```jsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle message submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setIsStreaming(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `# Hello!\n\nI'm an AI assistant. Here's some code:\n\n\`\`\`javascript\nconst greeting = "Hello, World!";\nconsole.log(greeting);\n\`\`\`\n\nHow can I help you today?`,
        timestamp: new Date().toISOString(),
      };
      setIsTyping(false);
      setMessages(prev => [...prev, aiMessage]);
      setIsStreaming(false);
    }, 1000);
  };

  // Code block component
  const CodeBlock = ({ inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '');
    return !inline && match ? (
      <div className="code-block-wrapper">
        <div className="code-block-header">
          <span className="language-badge">{match[1]}</span>
          <button
            className="copy-button"
            onClick={() => navigator.clipboard.writeText(String(children))}
          >
            Copy
          </button>
        </div>
        <SyntaxHighlighter
          style={vscDarkPlus}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      </div>
    ) : (
      <code className={className} {...props}>
        {children}
      </code>
    );
  };

  return (
    <div className="chat-interface">
      <div ref={chatContainerRef} className="messages-container">
        <AnimatePresence mode="popLayout">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`message ${message.role}`}
              layout
            >
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code: CodeBlock,
                    a: ({ node, ...props }) => (
                      <a target="_blank" rel="noopener noreferrer" {...props} />
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            </motion.div>
          ))}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="message assistant typing"
            >
              <div className="message-avatar">🤖</div>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="message-input"
            disabled={isStreaming}
          />
          <motion.button
            type="submit"
            className="send-button"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={!input.trim() || isStreaming}
          >
            Send
          </motion.button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
```

### Styling (CSS)

```css
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: #f5f5f5;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  max-width: 70%;
}

.message.user {
  align-self: flex-end;
  background: #007bff;
  color: white;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  line-height: 1.5;
}

.message-content h1,
.message-content h2,
.message-content h3 {
  margin-top: 0;
  margin-bottom: 0.5em;
}

.message-content p {
  margin: 0 0 0.5em 0;
}

.message-content pre {
  margin: 0.5em 0;
  border-radius: 6px;
  overflow: hidden;
}

.code-block-wrapper {
  margin: 0.5em 0;
  border-radius: 6px;
  overflow: hidden;
  background: #1e1e1e;
}

.code-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.language-badge {
  color: #9cdcfe;
  font-size: 12px;
  font-weight: 600;
}

.copy-button {
  padding: 4px 12px;
  background: #007acc;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.copy-button:hover {
  background: #005a9e;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #666;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.input-form {
  padding: 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-container {
  display: flex;
  gap: 12px;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  border-color: #007bff;
}

.send-button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #0056b3;
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .chat-interface {
    background: #1a1a1a;
  }

  .message.assistant {
    background: #2a2a2a;
    color: #e0e0e0;
  }

  .input-form {
    background: #2a2a2a;
    border-top-color: #444;
  }

  .message-input {
    background: #3a3a3a;
    border-color: #555;
    color: #e0e0e0;
  }

  .message-input:focus {
    border-color: #007bff;
  }
}
```

## Best Practices

### 1. Performance Optimization

```jsx
import { memo, useMemo } from 'react';

// Memoize expensive markdown rendering
const MemoizedMarkdown = memo(({ content, isStreaming }) => {
  const memoizedContent = useMemo(() => content, [content]);

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={markdownComponents}
    >
      {isStreaming ? memoizedContent + '▋' : memoizedContent}
    </ReactMarkdown>
  );
});

// Use React.memo for message component
const Message = memo(({ message, isStreaming }) => {
  return (
    <motion.div className="message">
      <MemoizedMarkdown
        content={message.content}
        isStreaming={isStreaming}
      />
    </motion.div>
  );
});
```

### 2. Accessibility Considerations

```jsx
// Add ARIA labels and roles
const Message = ({ message, isStreaming }) => (
  <motion.div
    role="article"
    aria-label={`${message.role} message`}
    className={`message ${message.role}`}
    aria-live={isStreaming ? "polite" : "off"}
    aria-atomic="true"
  >
    {/* Message content */}
  </motion.div>
);

// Keyboard navigation support
const ChatInterface = () => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <input
      type="text"
      onKeyDown={handleKeyDown}
      aria-label="Type your message"
      aria-describedby="send-button"
    />
  );
};
```

### 3. Error Handling

```jsx
const MessageWithErrorBoundary = ({ message }) => {
  return (
    <ErrorBoundary
      fallback={
        <div className="message-error">
          Failed to render message
        </div>
      }
    >
      <Message message={message} />
    </ErrorBoundary>
  );
};
```

### 4. Responsive Design

```css
/* Mobile-first responsive design */
.chat-interface {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.message {
  max-width: 100%;
}

@media (min-width: 768px) {
  .message {
    max-width: 70%;
  }
}

@media (min-width: 1024px) {
  .chat-interface {
    max-width: 800px;
    margin: 0 auto;
  }
}
```

### 5. Theme Support

```jsx
const ThemeContext = createContext();

const ChatInterface = () => {
  const [theme, setTheme] = useState('light');

  const getSyntaxTheme = () => {
    return theme === 'dark' ? vscDarkPlus : prism;
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <div className={`chat-interface theme-${theme}`}>
        {/* Chat content */}
      </div>
    </ThemeContext.Provider>
  );
};
```

## Summary

This guide provides a comprehensive foundation for building ChatGPT-style chatbot interfaces in React using:

1. **react-markdown** for markdown rendering with custom component mapping
2. **framer-motion** for smooth animations and transitions
3. **react-syntax-highlighter** for beautiful code highlighting

Key features implemented:
- Message entry/exit animations
- Typing indicators
- Syntax-highlighted code blocks
- Streaming message effects
- Responsive design
- Accessibility support
- Theme switching
- Performance optimizations

The examples provided can be customized and extended to fit specific use cases and design requirements for your chatbot application.

Sources:
- [react-markdown documentation](https://github.com/remarkjs/react-markdown)
- [Framer Motion documentation](https://www.framer.com/motion/)
- [react-syntax-highlighter documentation](https://github.com/react-syntax-highlighter/react-syntax-highlighter)