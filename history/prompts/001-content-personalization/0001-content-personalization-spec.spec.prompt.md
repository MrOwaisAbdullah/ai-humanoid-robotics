---
id: 0001
title: Content Personalization Spec
stage: spec
date: 2025-01-15
surface: agent
model: glm-4.6
feature: 001-content-personalization
branch: 001-content-personalization
user: User
command: /sp.specify
labels: ["feature", "personalization", "ai", "llm"]
links:
  spec: specs/001-content-personalization/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-content-personalization/spec.md
  - specs/001-content-personalization/checklists/requirements.md
tests:
  - Specification validation checklist completed
---

## Prompt

# Module 11: Content Personalization Implementation

## Overview
Implement the "Personalize" feature for the "Physical AI & Humanoid Robotics" book. This feature leverages the user's background information (collected during signup) to rewrite or summarize chapter content using an LLM, tailoring the explanation to their specific expertise level (e.g., explaining "ROS Nodes" differently to a Python Expert vs. a Novice).

## Context
- **Auth System**: We have a custom Python/FastAPI backend with JWT authentication.
- **User Profile**: Users have a `UserBackground` (software experience, hardware expertise) stored in the database.
- **UI**: The `AIFeaturesBar` already has a "Personalize" button.
- **Constraint**: This feature is **strictly for authenticated users**.

## Tools & Skills
- **SDK**: `openai-agents` (Python SDK) configured for Gemini.
- **Skill**: `openai-agents-sdk-gemini` (Refer to `.claude/skills/openai-agents-sdk-gemini/skills.md` for implementation patterns).
- **Subagents**: Utilize the `openai-agents-sdk-specialist` subagent logic if complex agent orchestration is needed (e.g., a "Researcher" agent to look up specific analogies).
- **Model**: `gemini-2.0-flash-lite` (via `GEMINI_API_KEY`).

## Implementation Plan

### Phase 1: Backend - Personalization Endpoint (Using OpenAI Agents SDK)

1.  **Create Agent**: Define a `PersonalizationTutor` agent using the `openai-agents` SDK.
    *   **Model**: Configure with `OpenAIChatCompletionsModel` pointing to Gemini (`base_url`, `api_key`).
    *   **Instructions**: "You are an expert technical tutor specializing in Robotics and AI. Your goal is to adapt complex content to the user's specific background..."
    *   **Tools**: Consider adding tools if needed (e.g., to look up specific analogies), but primarily this is a generation task.

2.  **Create Endpoint** `POST /api/v1/personalize` in `backend/src/api/routes/ai.py` (create if missing):
    *   **Input**: JSON body `{ "text": "...", "context": "..." }`.
    *   **Auth**: Require valid session (`get_current_user`).
    *   **Logic**:
        1.  Fetch the authenticated user's `UserBackground` from the DB.
        2.  Initialize the `PersonalizationTutor` agent.
        3.  Run the agent using `Runner.run()` (as per the skill documentation).
        4.  **Prompt Construction**: Pass the text and user profile to the agent.
            > "User Profile: Software=[Level], Hardware=[Level].
            > Content: [Text]
            > Task: Rewrite/Summarize this for the user. Explain concepts they might not know based on their profile. Use analogies relevant to their background."
        5.  Return the agent's final output.

2.  **Update Models** (if needed):
    *   Ensure `User` model has a relationship to `UserBackground` to easily access profile data.

### Phase 2: Frontend - Integration

1.  **Update `AIFeaturesBar.tsx`**:
    *   Connect the "Personalize" button `onClick`.
    *   **Auth Check**: Use `useAuth()`. If `!isAuthenticated`, trigger the `LoginModal` or show a specific toast "Please sign in to personalize content".
    *   **Action**:
        *   Extract the current page content (reuse the logic from `extractContent` or similar).
        *   Call `POST /api/v1/personalize`.
        *   Show a loading state (spinner on button).
    *   **Display**:
        *   How should the result appear?
        *   *Option A*: Replace the main content (too disruptive?).
        *   *Option B (Recommended)*: Show a "Personalized Summary" card/modal *overlay* or inject it at the top of the content.
        *   Let's implement a **Personalized Content Modal** or **Drawer** to keep it distinct from the original book text.

2.  **UI Components**:
    *   Create `PersonalizationModal.tsx` to display the result.
    *   Allow "Copy" or "Save to Notes" (future proofing).

### Phase 3: Testing

1.  **Test Case 1 (Guest)**: Click Personalize -> Prompt for Login.
2.  **Test Case 2 (Logged In)**: Click Personalize -> Backend receives request -> Agent processes with Gemini -> Returns tailored text.
3.  **Test Case 3 (Empty Profile)**: If user has no background info set, default to "General/Intermediate" or prompt them to update profile.

## Files to Modify

- `backend/src/api/routes/ai.py` (New)
- `backend/src/agents/personalization_agent.py` (New - define the Agent here)
- `src/theme/DocItem/AIFeaturesBar.tsx`
- `src/services/api.ts`
- `src/components/Personalization/PersonalizationModal.tsx` (New)

## Key Constraints
- Use the existing `AuthContext` for user state.
- Ensure the LLM prompt is robust and handles missing profile data gracefully.
- Keep the UI "Glassmorphism" consistent.
- **Mandatory**: Use `openai-agents` SDK for the backend logic.

## Response snapshot

Successfully created specification for Content Personalization feature including:
- Branch: 001-content-personalization
- Comprehensive spec with user stories, requirements, and success criteria
- Quality checklist validation
- Resolved 2 clarification points: smart segmentation (2000 words) and saving (10 items)

## Outcome

- ✅ Impact: Feature specification complete and validated
- 🧪 Tests: Quality checklist passed (100%)
- 📁 Files: Created spec.md and requirements checklist
- 🔁 Next prompts: /sp.plan to create implementation plan
- 🧠 Reflection: Specification effectively balances user needs with technical constraints

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All validation criteria met
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
