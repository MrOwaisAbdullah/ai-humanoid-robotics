---
id: 0001
title: Advanced Chatbot UI Implementation
stage: spec
date: 2025-12-06
surface: agent
model: claude-sonnet
feature: 003-chat-ui
branch: 003-chat-ui
user: Claude
command: /sp.specify
labels: ["spec", "chatbot", "ui", "text-selection"]
links:
  spec: specs/003-chat-ui/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-chat-ui/spec.md (Created comprehensive specification with 4 user stories and 14 functional requirements)
  - specs/003-chat-ui/checklists/requirements.md (Created quality checklist)
tests:
  - Specification validation completed successfully
  - All acceptance scenarios defined with given/when/then format
  - Success criteria are measurable and technology-agnostic
---

## Prompt

Implement Advanced Chatbot UI with Text Selection Integration ("Ask AI"). Enhance the Docusaurus frontend with a sophisticated, ChatGPT-style chatbot widget. This module focuses on the user interface, message rendering, and interaction flows, specifically enabling users to select text in the book and query the AI about it.

**Requirements:**

1. **Chatbot UI Overhaul (ChatGPT Style)**:
   - **Visual Reference**: Mimic the provided image `chatbot-ui.png` (Dark mode, clean typography, rounded corners, specific color palette).
   - **Components**:
     - **Start Screen**: "What can I help with today?" headline with quick-start suggestion chips (e.g., "Summarize this chapter", "Explain key concepts").
     - **Message Bubble**: Distinct styles for User (accent color bg) vs. AI (transparent/dark bg).
     - **Streaming Typography**: Implement a "blinking cursor" effect during streaming.
     - **Thinking State**: A floating, pulsing "Thinking..." indicator or skeleton loader that appears while waiting for the first token, similar to modern LLM interfaces.
     - **Input Area**: Floating capsule style with an integrated send button (arrow icon).

2. **Message Rendering Features**:
   - **Markdown Support**: AI responses must render Markdown (bold, italics, lists, code blocks with syntax highlighting).
   - **Sources Badges**: When the RAG backend returns source metadata (e.g., "Chapter 2: Sensors"), render these as clickable "badges" or footnotes below the AI response. Clicking a badge should navigate to that section (if possible) or display a small citation tooltip.
   - **Links**: Ensure any URLs in the response are clickable and open in a new tab.

3. **"Ask AI" Text Selection Feature**:
   - **Interaction**: When a user highlights text anywhere in the book content:
     1.  Show a small, floating "Ask AI" tooltip/button near the selection.
     2.  On click:
        - Open the Chatbot Widget (if closed).
        - **Context Injection**: Automatically add the selected text to the chat context (hidden or visible quote).
        - **Prompt**: Pre-fill or auto-send a prompt like: "Explain this text: [Selection]".
   - **Technical**: Use a React hook (`useTextSelection`) to track selection coordinates and state. Portal the tooltip to the document body to ensure it floats correctly over other elements.

4. **Skill Utilization & updates**:
   - **`gemini-frontend-assistant`**: Use this skill to generate the React/Tailwind code for the new UI components.
   - **`chatbot-widget-creator`**: Update the existing widget structure.
     - *Action*: After implementing these features, **update the `chatbot-widget-creator` skill files** with these new, improved templates so future projects benefit from this "ChatGPT-style" implementation.

5. **Research & Verification**:
   - **Mandatory**: Use `mcp__context7__get-library-docs` to check documentation for:
     - `react-markdown` (for rendering responses).
     - `framer-motion` (for smooth widget open/close and message entry animations).
     - `react-syntax-highlighter` (for code blocks).

**Deliverables**:
- Updated `src/components/ChatWidget/` with new UI.
- `src/components/ChatWidget/MessageRenderer.tsx` (Markdown + Badges).
- `src/hooks/useTextSelection.ts` and `src/components/SelectionTooltip.tsx`.
- Updated `chatbot-widget-creator` skill templates (in `.claude/skills/`).

**Constraint Checklist & Confidence Score**:
1. ChatGPT Visual Style? Yes.
2. Source Badges? Yes.
3. Text Selection -> Ask AI flow? Yes.
4. Update Skill files? Yes.
5. Context 7 Research? Yes.

Confidence Score: 5/5

## Response snapshot

Successfully created comprehensive specification for Advanced Chatbot UI with Text Selection Integration. The spec includes:

- 4 detailed user stories with clear priorities (P1-P2)
- 14 functional requirements covering all core features
- 12 measurable success criteria including performance benchmarks
- Complete edge case analysis and assumptions
- Clear scope definition with out-of-scope items

Key components defined:
- ChatGPT-style UI with dark mode aesthetics
- Rich markdown rendering with syntax highlighting
- Contextual text selection with "Ask AI" functionality
- Smooth animations and transitions
- Source citation badges and navigation

## Outcome

- ✅ Impact: Created comprehensive specification that enables development of modern ChatGPT-style chatbot interface with text selection integration
- 🧪 Tests: All acceptance scenarios defined with given/when/then format for each user story
- 📁 Files: Created spec.md and requirements.md checklist files
- 🔁 Next prompts: Ready for /sp.plan to create implementation plan

## Evaluation notes (flywheel)

- Failure modes observed: None during specification creation
- Graders run and results (PASS/FAIL): All validation checks passed
- Prompt variant (if applicable): Original prompt used successfully
- Next experiment (smallest change to try): Begin implementation of P1 features first
