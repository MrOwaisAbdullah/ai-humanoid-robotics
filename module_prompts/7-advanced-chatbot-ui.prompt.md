/sp.specify
Implement Advanced Chatbot UI with Text Selection Integration ("Ask AI").

**Context & Goals:**
Enhance the Docusaurus frontend with a sophisticated, ChatGPT-style chatbot widget. This module focuses on the user interface, message rendering, and interaction flows, specifically enabling users to select text in the book and query the AI about it.

**Requirements:**

1.  **Chatbot UI Overhaul (ChatGPT Style)**:
    *   **Visual Reference**: Mimic the provided image `chatbot-ui.png` (Dark mode, clean typography, rounded corners, specific color palette).
    *   **Dimensions & Layout**:
        *   **Portrait Orientation**: The widget MUST be a "Portrait" rectangle, not a square. Approximate dimensions: Width ~360px-380px, Height ~600px (or 70vh).
        *   **Compact Width**: Overall width should be slightly decreased compared to standard chat widgets to fit elegantly on the side.
    *   **Components**:
        *   **Start Screen**: "What can I help with today?" headline with quick-start suggestion chips.
        *   **Message Bubble**: Distinct styles for User (accent color bg) vs. AI (transparent/dark bg).
            *   **User Bubble Color**: User message bubble background color MUST dynamically match the Docusaurus theme's primary color (`var(--ifm-color-primary)`).
            *   **No Ticks**: Do NOT display "read" or "sent" ticks.
            *   **No Timestamps**: Do NOT display "just now" or specific timestamps on messages.
            *   **Alignment**: Avatar and message bubble content must be **bottom-aligned** (`items-end`) within the message row.
        *   **Streaming Typography**: Implement a "blinking cursor" effect during streaming.
        *   **Thinking State**: A floating, pulsing "Thinking..." indicator or skeleton loader.
        *   **Input Area**: Floating capsule style with an integrated send button.
            *   **No File Upload**: Do NOT include a file upload button or icon. Text input only.

2.  **Message Rendering Features**:
    *   **Markdown Support**: AI responses must render Markdown (bold, italics, lists, code blocks with syntax highlighting).
    *   **Sources Badges**: When the RAG backend returns source metadata, render these as clickable "badges" below the response.
    *   **Links**: URLs must open in a new tab.

3.  **"Ask AI" Text Selection Feature**:
    *   **Interaction**: When a user highlights text anywhere in the book content:
        1.  Show a small, floating "Ask AI" tooltip/button near the selection.
        2.  On click:
            *   Open the Chatbot Widget (if closed).
            *   **Context Injection**: Automatically add the selected text to the chat context.
            *   **Prompt**: Pre-fill or auto-send a prompt.
    *   **Technical**: Use a React hook (`useTextSelection`) to track selection coordinates. Portal the tooltip.

4.  **Skill Utilization & updates**:
    *   **`gemini-frontend-assistant`**: Use this skill to generate the React/Tailwind code.
    *   **`chatbot-widget-creator`**: Update the existing widget structure.
        *   *Action*: After implementing these features, **update the `chatbot-widget-creator` skill files** with these new, improved templates.

5.  **Research & Verification**:
    *   **Mandatory**: Use `mcp__context7__get-library-docs` to check documentation for:
        *   `react-markdown`, `framer-motion`, `react-syntax-highlighter`.

**Deliverables:**
- Updated `src/components/ChatWidget/` with new UI.
- `src/components/ChatWidget/MessageRenderer.tsx` (Markdown + Badges).
- `src/hooks/useTextSelection.ts` and `src/components/SelectionTooltip.tsx`.
- Updated `chatbot-widget-creator` skill templates.

**Constraint Checklist & Confidence Score:**
1. ChatGPT Visual Style? Yes.
2. Portrait Mode (No Square)? Yes.
3. No File Upload? Yes.
4. No Timestamps/Ticks? Yes.
5. Bottom Aligned Bubbles? Yes.

Confidence Score: 5/5
