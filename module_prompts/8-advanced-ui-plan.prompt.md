/sp.plan
Implement the Advanced Chatbot UI and Text Selection features for the Docusaurus frontend.

**Context & Goals:**
We are enhancing the chatbot widget to mimic the modern, "ChatGPT-style" interface (dark mode, sleek animations, markdown rendering) and adding a contextual "Ask AI" feature for selected text. This plan covers the frontend components, hooks, and integration steps required to meet the specification.

**Prerequisites:**
- `chatbot-widget-creator` skill is available.
- `gemini-frontend-assistant` skill is available.
- Docusaurus project is set up with Tailwind CSS.
- Context 7 checks for `react-markdown`, `framer-motion`, and `react-syntax-highlighter` have been performed (or will be as part of the task execution).

**Instructions for the Agent:**

1.  **Setup & Dependencies**:
    *   Install required packages: `react-markdown`, `framer-motion`, `react-syntax-highlighter`, `remark-gfm`, `lucide-react`.
    *   Verify `tailwind.config.js` includes necessary colors/extensions for the new UI (if any specific tokens are needed).

2.  **Component Architecture (src/components/ChatWidget/)**:
    *   `index.tsx`: Main container managing state (open/close, messages, selection context).
    *   `ChatWindow.tsx`: The main view (Start Screen vs. Message List).
    *   `MessageList.tsx`: Scrollable container for messages.
    *   `MessageBubble.tsx`: Individual message component handling User vs. AI styling and animations.
    *   `MessageRenderer.tsx`: The markdown renderer using `react-markdown` + syntax highlighting + source badges.
    *   `InputArea.tsx`: Floating capsule input with send button.
    *   `StartScreen.tsx`: "What can I help with?" view with suggestion chips.
    *   `ThinkingIndicator.tsx`: Pulse/Skeleton animation.

3.  **"Ask AI" Text Selection Logic**:
    *   `src/hooks/useTextSelection.ts`: Hook to track selection range and coordinates.
    *   `src/components/SelectionTooltip.tsx`: Floating "Ask AI" button using Portal (to `document.body`).
    *   **Integration**: In `Layout` or `Root`, mount the `SelectionTooltip`. On click, it calls a method exposed by the `ChatWidget` context to open the chat and set the input value/context.

4.  **State Management**:
    *   Create a simple React Context (`ChatContext`) to manage:
        *   `isOpen`: boolean
        *   `messages`: Array<Message>
        *   `isStreaming`: boolean
        *   `selectedContext`: string | null
        *   `actions`: open(), close(), sendMessage(), setSelection()

5.  **Implementation Steps**:
    *   **Step 1**: Scaffold the file structure and Context.
    *   **Step 2**: Implement `useTextSelection` and `SelectionTooltip`. Verify selection pops up correctly.
    *   **Step 3**: Build `MessageRenderer` with Markdown and Code Highlighting. Test with static content.
    *   **Step 4**: Build the main Chat UI (`StartScreen`, `MessageList`, `InputArea`) with Framer Motion animations.
    *   **Step 5**: Connect the pieces. Wire "Ask AI" to open the chat and insert text.
    *   **Step 6**: Update `chatbot-widget-creator` skill templates with this new, superior implementation.

**Deliverables:**
- Fully functional ChatWidget with new UI.
- Text Selection feature working on documentation pages.
- Updated Skill Templates.

**Constraint Checklist & Confidence Score:**
1. ChatGPT Style? Yes.
2. Text Selection? Yes.
3. Markdown/Code Support? Yes.
4. Framer Motion Animations? Yes.

Confidence Score: 5/5
