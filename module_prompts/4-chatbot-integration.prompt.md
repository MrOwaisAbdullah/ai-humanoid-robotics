Use the `chatbot-widget-creator` skill to integrate the OpenAI ChatKit widget into our Docusaurus frontend.

**Context & Goals:**
This is Module 4. Connect the React frontend to the FastAPI backend. Enable the interactive "Chat with Book" using the official OpenAI ChatKit library and implementing "Ask about Selection" features.

**Instructions for the Agent:**

1.  **Use Sub-Agent & Skills**:
    *   Invoke the **chatbot-widget-creator** skill to scaffold the base components (`ChatWidget.template.tsx`, `ChatButton.template.tsx`).
    *   Use `mcp__context7__get-library-docs` with `libraryID="/openai/chatkit-js"` to verify the latest API for customizing the `ChatKit` component (themes, start screens).

2.  **Frontend Implementation**:
    *   **Install Dependencies**: `@openai/chatkit-react` and `openai` (for backend session generation).
    *   **Create Wrapper**: Build `src/components/ChatWidget/index.tsx` using the skill's template. It must wrap `<ChatKit />` and handle the open/close state using the glassmorphic `ChatButton`.
    *   **Backend Session**: Implement a Next.js/Node.js API route (or equivalent in Docusaurus if using a custom server, otherwise ensure the FastAPI backend handles session token generation) to securely issue ChatKit tokens.
        *   *Note*: The prompt assumes the FastAPI backend handles the RAG logic. We need a bridge. If ChatKit requires a specific backend structure, adapt the FastAPI `/chat` endpoint to return compatible streams or use ChatKit's backend SDK to proxy the request to our RAG system.

3.  **Text Selection Feature ("Ask AI about this")**:
    *   Create `src/hooks/useTextSelection.ts`: A hook to detect text selection on the page.
    *   Create `SelectionPopover`: A floating tooltip appearing near selected text.
    *   **Integration**: When "Ask AI" is clicked in the popover:
        1.  Open the ChatWidget.
        2.  Programmatically insert the selected text into the ChatKit composer (use `control.setComposerValue` or similar API found via MCP).

4.  **Theming & styling**:
    *   Use the **Glassmorphism** styles provided by the skill.
    *   Ensure the widget respects the Docusaurus light/dark mode (`var(--ifm-color-primary)`, etc.).

**Deliverable:**
- `src/components/ChatWidget/` (The main widget).
- `src/hooks/useTextSelection.ts` (Selection logic).
- Integration in `src/theme/Root.tsx` (Global persistence).

**Constraint Checklist & Confidence Score:**
1. Use `chatbot-widget-creator`? Yes.
2. Use OpenAI ChatKit? Yes.
3. Text Selection Feature? Yes.
4. Glassmorphism? Yes.

Confidence Score: 5/5

**Mental Sandbox Simulation:**
*   *Scenario:* ChatKit requires a specific backend protocol that differs from our simple `/chat` SSE endpoint.
*   *Correction:* I will instruct the agent to verify if we can point ChatKit to a custom RAG endpoint or if we need to wrap our RAG logic within a ChatKit-compatible server handler. Ideally, we use ChatKit for the UI and state, but ensure the "backend" it talks to is our RAG system.

/sp.plan
1.  **Install Dependencies**:
    *   `npm install @openai/chatkit-react`
    *   `npm install lucide-react` (for icons if needed)

2.  **Scaffold Widget**:
    *   Use `chatbot-widget-creator` to generate `ChatWidget` and `ChatButton`.
    *   Customize `ChatWidget` to use `useChatKit` hook.

3.  **Backend Bridge (Session Token)**:
    *   Ensure the FastAPI backend has a `POST /api/chatkit/session` endpoint that returns a client token.
    *   Update `ChatWidget` config to fetch this token.

4.  **Implement Selection Feature**:
    *   Create `useTextSelection` hook.
    *   Create `SelectionPopover` component.
    *   Connect `SelectionPopover` "Ask" button to `ChatWidget` context to open chat and pre-fill message.

5.  **Global Integration**:
    *   Mount `ChatWidget` and `SelectionPopover` in `src/theme/Root.tsx`.

6.  **Verification**:
    *   Test opening/closing.
    *   Test text selection popover appearance.
    *   Test sending a message (mocked or real).