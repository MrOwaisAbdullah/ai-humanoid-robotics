# Implementation Plan: Authentication and UX Improvements

**Branch**: `001-auth-ux-improvements` | **Date**: 2025-01-08 | **Spec**: [specs/001-auth-ux-improvements/spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-auth-ux-improvements/spec.md`

## Summary

This plan addresses critical UX improvements for the AI Book platform: guest session persistence across refreshes, seamless user authentication, knowledge collection during registration, improved navigation with "Module" terminology, and enhanced message limit notifications. The implementation follows modern web application patterns with React/TypeScript frontend and FastAPI/SQLAlchemy backend.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript 5.0+
**Primary Dependencies**: FastAPI, SQLAlchemy, python-jose, React, Axios, JWT
**Storage**: SQLite with SQLAlchemy ORM
**Testing**: pytest (backend), Jest + React Testing Library (frontend)
**Target Platform**: Web application (desktop + mobile responsive)
**Project Type**: Web application with React frontend and Python backend
**Performance Goals**: <100ms API response time, handle 10k concurrent anonymous sessions
**Constraints**: Stateless design where possible, HTTP-only cookies for security, 3-message limit for anonymous users
**Scale/Scope**: Support 10k+ concurrent users with graceful degradation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gates Status: ✓ PASSED

1. **Specification-First Development** ✓
   - Complete spec with user stories and acceptance criteria
   - Clear functional requirements and success metrics
   - Research findings documented and integrated

2. **Production-First Mindset** ✓
   - JWT tokens with proper expiration
   - HTTP-only cookies for security
   - Error handling and graceful degradation
   - Rate limiting and protection measures

3. **Co-Learning with AI** ✓
   - Comprehensive research completed before implementation
   - Best practices from external sources integrated
   - Production-ready code patterns adopted

4. **SOLID Principles** ✓
   - Single Responsibility: Separation of session, auth, and UI concerns
   - Open/Closed: Configurable validation rules and storage strategies
   - Dependency Inversion: Interface-based design for storage and auth providers
   - DRY: Shared utilities and reusable components

5. **Documentation Research** ✓
   - Used Context7 MCP for latest authentication patterns
   - Web Search for performance benchmarks
   - All technical implementations verified against current documentation

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

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py            # Authentication endpoints
│   │       └── chat.py            # Chat endpoints with session middleware
│   ├── models/
│   │   ├── auth.py             # User and session models
│   │   └── anonymous_session.py  # Guest session model
│   ├── middleware/
│   │   ├── auth.py             # Authentication middleware
│   │   ├── csrf.py             # CSRF protection
│   │   └── rate_limiter.py     # Rate limiting middleware
│   ├── services/
│   │   ├── auth.py             # Authentication logic
│   │   └── anonymous.py       # Guest session service
│   └── main.py               # FastAPI application setup

frontend/
├── src/
│   ├── components/
│   │   ├── Auth/
│   │   │   ├── LoginButton.tsx      # Login/Registration component
│   │   │   ├── AuthenticationBanner.tsx  # Guest prompt banner
│   │   │   ├── UserProfile.tsx      # User profile dropdown
│   │   │   ├── RegistrationForm.tsx  # Enhanced registration form
│   │   │   └── OnboardingModal.tsx  # Knowledge collection modal
│   │   └── ChatWidget/
│   │       ├── ChatInterface.tsx      # Main chat interface with notifications
│   │       ├── ChatWidgetContainer.tsx # Widget container with session logic
│   │       └── InputArea.tsx          # Message input with limit enforcement
│   ├── contexts/
│   │   └── AuthContext.tsx       # Global authentication state
│   ├── utils/
│   │   └── sessionStorage.ts      # localStorage helper with fallback
│   └── css/
│       └── custom.css           # Mobile navigation styles

tests/
├── backend/
│   ├── unit/
│   │   ├── test_auth.py
│   │   └── test_sessions.py
│   └── integration/
│       └── test_guest_flows.py
└── frontend/
    ├── components/
    └── Auth/
        └── AuthenticationBanner.test.tsx
```

**Structure Decision**: Web application with React/TypeScript frontend and FastAPI/SQLAlchemy backend

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
