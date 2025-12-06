---
name: chatbot-widget-creator
description: Creates a modern, glassmorphic Chatbot Widget using OpenAI ChatKit (official library). Includes a floating button and a backend session handler template.
category: frontend
version: 2.0.0
---

# Chatbot Widget Creator Skill

## Purpose

Integrate the **official OpenAI ChatKit** into your Docusaurus or React application.
This skill provides a polished wrapper that adds:
- **Floating Action Button (FAB)** with glassmorphism.
- **Responsive Panel** logic (mobile fullscreen, desktop popover).
- **Theming Integration** mapping your CSS variables to ChatKit's theme engine.

## Prerequisites

1.  **OpenAI API Key**: You need a backend to generate session tokens.
2.  **Package**: Install the official library:
    ```bash
    npm install @openai/chatkit-react
    ```

## Usage Instructions

### 1. Frontend Setup

Use the templates to create the widget:

```bash
# 1. Create directory
mkdir -p src/components/ChatWidget

# 2. Copy the ChatButton (FAB)
cp .claude/skills/chatbot-widget-creator/components/ChatButton.template.tsx src/components/ChatWidget/ChatButton.tsx

# 3. Copy the ChatWidget Wrapper
cp .claude/skills/chatbot-widget-creator/components/ChatWidget.template.tsx src/components/ChatWidget/index.tsx
```

### 2. Backend Setup

ChatKit requires a secure backend to issue session tokens. Do not expose your API key on the frontend!

Use the `api-clients/backend-session.template.ts` as a guide to create your API route (e.g., in Next.js `pages/api/chatkit/session.ts` or your backend framework).

### 3. Integration

Add the widget to your site layout (e.g., `src/theme/Root.tsx` in Docusaurus):

```tsx
import React from 'react';
import ChatWidget from '@site/src/components/ChatWidget';

export default function Root({children}) {
  return (
    <>
      {children}
      <ChatWidget 
        apiSessionEndpoint="https://your-backend.com/api/chatkit/session"
        theme="light" 
        title="Doc Assistant"
      />
    </>
  );
}
```

## Customization

### Theming
The `ChatWidget.template.tsx` automatically maps your CSS variables (like `var(--ifm-color-primary)`) to the ChatKit theme. You can customize the `theme` object passed to `useChatKit` in that file.

### Start Screen
Edit the `startScreen` configuration in `ChatWidget.template.tsx` to change the greeting and suggested prompts.

## Features

- ✅ **Official OpenAI Integration**: Uses the robust `@openai/chatkit-react`.
- ✅ **Glassmorphism**: The widget container uses `backdrop-blur` and transparent borders.
- ✅ **Responsive**: Automatically switches to fullscreen on mobile devices.
- ✅ **Themed**: Inherits your project's primary colors and fonts.
