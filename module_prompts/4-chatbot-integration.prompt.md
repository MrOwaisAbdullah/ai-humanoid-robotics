/sp.specify
Integrate the Chatbot and Advanced UI features into the Docusaurus Frontend.

**Context & Goals:**
This is Module 4. Connect the React frontend to the FastAPI backend. Enable the interactive "Chat with Book" and "Ask about Selection" features.

**Requirements:**

1.  **Chat Widget Component**:
    *   Floating action button (bottom-right) that expands into a Chat Window.
    *   *Action*: Use `mcp__context7__get-library-docs` with libraryID="react" or "chatkit-js" if applicable for UI patterns.
    *   UI: Message list (User vs. AI), Input field, Loading indicators (streaming cursor).
    *   State Management: Handle chat history within the session.
2.  **Backend Integration**:
    *   Connect to the Hugging Face Spaces API URL (env variable `REACT_APP_API_URL`).
    *   Handle Streaming responses (process SSE/chunks and append to message state).
3.  **Text Selection Feature**:
    *   Implement a "tooltip" or "popover" that appears when the user selects text in the main book content.
    *   Action: "Ask AI about this".
    *   Behavior: Opens the chat widget (if closed), adds the selected text as a quoted context in the input area, and allows the user to ask a question about it.
4.  **Markdown Rendering in Chat**:
    *   The AI response (which may contain code blocks) must be rendered properly as Markdown within the chat bubble.

**Deliverable:**
- React components (`ChatWidget`, `SelectionPopover`).
- Integration into Docusaurus `Root` or `Layout` to persist across page navigations.
