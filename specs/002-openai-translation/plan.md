# Implementation Plan: OpenAI Translation System

**Branch**: `002-openai-translation` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-openai-translation/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements a robust translation system that replaces the broken Gemini-based translation with OpenAI Agents SDK using Gemini API. The system translates complete book pages from English to Urdu while preserving formatting and handling code blocks appropriately. Key features include intelligent caching, progress tracking, and streaming responses.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript/React 18+ (Frontend)
**Primary Dependencies**: OpenAI Agents SDK, Gemini API, FastAPI, SQLAlchemy, React
**Storage**: SQLite (development), PostgreSQL (production), Redis (caching)
**Testing**: pytest (backend), Jest/React Testing Library (frontend)
**Target Platform**: Web (Hugging Face Spaces deployment)
**Project Type**: Full-stack web application with translation service
**Performance Goals**: <3 second response time, 95% cache hit rate, 99.9% uptime
**Constraints**: Rate limited API calls, content size <100k chars, concurrent users <1000
**Scale/Scope**: Support book translation, handle 5000-word pages, maintain session state

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
