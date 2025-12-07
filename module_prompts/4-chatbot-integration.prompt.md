Use the `chatbot-widget-creator` skill to scaffold the UI, but implement the logic to connect directly to our Python backend.

**Context & Goals:**
This is Module 4. Connect the React frontend to the FastAPI backend. We are building a custom "Chat with Book" widget. **Crucially**, we are NOT using the `openai-chatkit` JavaScript library on the frontend. Instead, the frontend will consume Server-Sent Events (SSE) directly from our Python backend (which handles the RAG logic).

**Instructions for the Agent:**

1.  **Use Sub-Agent & Skills**:
    *   Invoke the **chatbot-widget-creator** skill to scaffold the visual components (`ChatWidget.template.tsx`, `ChatButton.template.tsx`) to ensure the "Glassmorphism" look.
    *   Use **gemini-frontend-assistant** to implement the custom React hooks for streaming data, as we are bypassing the standard ChatKit JS SDK.

2.  **Frontend Implementation (Custom RAG Client)**:
    *   **Install Dependencies**: `lucide-react` (icons), `react-markdown` (rendering), `framer-motion` (animations), `remark-gfm`.
    *   **Network Layer**: Create a custom hook `src/hooks/useChatStream.ts`:
        *   Connects to `POST ${API_URL}/api/v1/chat` (configured in Docusaurus `customFields`).
        *   Handles **Server-Sent Events (SSE)** parsing. Expect the backend to stream JSON chunks (or text) and update the message state in real-time.
        *   Manages states: `isLoading`, `isStreaming`, `messages` array.
    *   **UI Integration**:
        *   Update `src/components/ChatWidget/index.tsx` to use this custom hook instead of `ChatKit` providers.
        *   Ensure the "Thinking" state matches the ChatGPT-style "pulsing" indicator defined in the UI design.

3.  **Text Selection Feature ("Ask AI about this")**:
    *   Create `src/hooks/useTextSelection.ts`: A hook to detect text selection on the page (debounce the selection event).
    *   Create `SelectionPopover`: A floating tooltip appearing near selected text using `ReactDOM.createPortal`.
    *   **Integration**:
        *   When "Ask AI" is clicked, it should call the `openChat()` method from your `ChatContext`.
        *   It should automatically populate the chat input or immediately send the prompt: "Explain this context: \"[Selected Text]\"$.

4.  **Theming & Styling**:
    *   Strict adherence to the **Glassmorphism** aesthetic (backdrop-blur, translucent borders).
    *   Ensure strict Dark Mode compatibility (Docusaurus `html[data-theme='dark']`).

**Deliverables:**
- `src/components/ChatWidget/` (Custom implementation).
- `src/hooks/useChatStream.ts` (SSE Logic).
- `src/hooks/useTextSelection.ts` (Selection Logic).
- Integration in `src/theme/Root.tsx`.

**Constraint Checklist & Confidence Score:**
1. Custom React Implementation (No ChatKit JS)? Yes.
2. SSE Streaming? Yes.
3. Text Selection Integration? Yes.
4. Glassmorphism? Yes.

Confidence Score: 5/5

**Mental Sandbox Simulation:**
*   *Scenario:* The backend returns raw text chunks, but the frontend expects JSON events.
*   *Correction:* The prompt explicitly mentions implementing an SSE parser. I will ensure the `useChatStream` hook is robust enough to handle the specific stream format defined in Module 3 (FastAPI).

/sp.plan
1.  **Install Frontend Deps**:
    *   `npm install framer-motion react-markdown remark-gfm lucide-react clsx tailwind-merge`

2.  **Scaffold Components**:
    *   Use `chatbot-widget-creator` templates for the *visuals* (CSS/Tailwind structure), but strip out any ChatKit JS provider logic.

3.  **Develop `useChatStream`**:
    *   Implement `fetch` with `ReadableStream`.
    *   Parse the stream (handling `data: {...}` lines if standard SSE, or raw chunks).
    *   Update a `currentMessage` state ref during streaming to prevent re-renders on every character (performance optimization).

4.  **Develop Selection Logic**:
    *   `useTextSelection` listens to `selectionchange`.
    *   Calculate `getBoundingClientRect` of range to position the Popover.
    *   `SelectionPopover` component renders only when text is selected.

5.  **Assemble ChatWidget**:
    *   Combine `MessageList` (rendering Markdown), `InputArea`, and `ChatButton`.
    *   Wrap with `ChatContext` to allow the Selection Popover to control the widget state.

6.  **Global Mount**:
    *   Swizzle or create `src/theme/Root.tsx` to mount the Widget and Popover globally across all doc pages.
