# Chat Widget Templates

This directory contains all the template files for creating a production-ready ChatGPT-style chatbot widget.

## Template Files

### Core Components
- `ChatWidgetContainer.tsx` - Main widget container with state management
- `ChatInterface.tsx` - ChatGPT-style UI component
- `ChatButton.tsx` - Floating action button
- `SelectionTooltip.tsx` - Text selection "Ask AI" tooltip
- `ErrorBoundary.tsx` - Error handling component

### Hooks
- `useChatSession.tsx` - Chat session management
- `useTextSelection.tsx` - Text selection detection
- `useErrorHandler.tsx` - Error handling utilities
- `useStreamingResponse.tsx` - SSE streaming management

### State Management
- `contexts/index.ts` - Split context implementation
- `hooks/chatReducer.ts` - State reducer
- `types/index.ts` - TypeScript type definitions

### Utilities
- `utils/api.ts` - API request/response formatting
- `utils/animations.ts` - Framer Motion animation configs
- `utils/renderCounter.ts` - Debug render counter
- `utils/performanceMonitor.ts` - Performance monitoring

### Styles
- `styles/ChatWidget.module.css` - Component styles

## Usage

```bash
# Create the widget directory
mkdir -p src/components/ChatWidget/{components,hooks,contexts,utils,styles}

# Copy all templates
cp -r .claude/skills/chatbot-widget-creator/templates/* src/components/ChatWidget/
```

## Integration

Add to your site root:

```tsx
import ChatWidgetContainer from '../components/ChatWidget/ChatWidgetContainer';

export default function Root({ children }) {
  return (
    <>
      {children}
      <ChatWidgetContainer
        apiUrl="http://localhost:7860/api/chat"
        maxTextSelectionLength={2000}
      />
    </>
  );
}
```