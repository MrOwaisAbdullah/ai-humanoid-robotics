---
id: 0002
title: chatkit-integration architecture
stage: plan
date: 2025-01-05
surface: agent
model: glm-4.6
feature: 001-chatkit-integration
branch: 001-chatkit-integration
user: K TECH
command: /sp.plan
labels: ["chatkit","architecture","planning","frontend","integration"]
links:
  spec: specs/001-chatkit-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - D:\GIAIC\Quarter 4\ai-book\specs\001-chatkit-integration\plan.md
 - D:\GIAIC\Quarter 4\ai-book\specs\001-chatkit-integration\research.md
 - D:\GIAIC\Quarter 4\ai-book\specs\001-chatkit-integration\data-model.md
 - D:\GIAIC\Quarter 4\ai-book\specs\001-chatkit-integration\quickstart.md
tests:
 - Research validation of ChatKit SDK patterns
 - Data model consistency checks
 - Architecture compliance with constitution principles

---

## Prompt

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

## Response snapshot

Created comprehensive implementation plan including:
- Research findings on ChatKit React SDK integration patterns
- Detailed data model with TypeScript interfaces
- Step-by-step quickstart guide
- Architecture design following constitution principles
- Risk mitigation strategies for glassmorphism effects and SSE streaming

## Outcome

- ✅ Impact: Complete architecture plan for ChatKit integration with research-backed decisions
- 🧪 Tests: Validated ChatKit SDK patterns, confirmed data model consistency
- 📁 Files: Created plan.md, research.md, data-model.md, quickstart.md
- 🔁 Next prompts: /sp.tasks for implementation
- 🧠 Reflection: Chose ChatKit over custom implementation to leverage proven streaming patterns and reduce development time

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All constitution gates cleared
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Consider adding ChatKit session token endpoint to backend for better session management
