/sp.specify
Implement Bonus Features: Authentication, Personalization, and Localization.

**Context & Goals:**
This is Module 5. Aiming for the 150 bonus points. We will add Auth, Personalization, and Urdu Translation.

**Requirements:**

1.  **Authentication (Better Auth)**:
    *   *Action*: Use `mcp__context7__get-library-docs` with libraryID="better-auth" to implement a lightweight signup/login flow.
    *   **Onboarding**: On Signup, present a modal asking:
        *   "What is your Software Background?" (Novice/Intermediate/Expert)
        *   "What is your Hardware/Robotics Background?" (None/Arduino/ROS-Pro)
    *   Store this profile in the backend (Postgres/Neon or simple metadata in Qdrant/KV store).
2.  **Content Personalization**:
    *   Activate the "Personalize" button created in Module 1.
    *   **Logic**: When clicked, send the current chapter text + user profile to the LLM.
    *   **Prompt**: "Rewrite this introduction/summary to match the user's level (e.g., Use simple analogies for novices, technical jargon for experts)."
    *   **Display**: Replace the visible text or show a "Personalized Summary" block at the top.
3.  **Urdu Translation**:
    *   Activate the "Translate" button.
    *   **Logic**: Send text to LLM with "Translate to Urdu" prompt.
    *   **Display**: Show Urdu text (ensure RTL font support, e.g., Noto Nastaliq Urdu) either replacing the text or side-by-side.

**Deliverable:**
- Auth components.
- Profile management logic.
- API endpoints for `personalize` and `translate`.
- UI updates to hook up the buttons.
