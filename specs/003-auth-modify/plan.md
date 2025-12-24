# Implementation Plan: Authentication Modification

**Branch**: `002-auth-modify` | **Date**: 2025-01-08 | **Spec**: [link](./spec.md)
**Input**: Feature specification from `/specs/002-auth-modify/spec.md`

## Summary

This feature replaces Google OAuth with email/password authentication and adds an onboarding modal for collecting user background data. The implementation includes: (1) Email/password registration and login, (2) Onboarding flow with structured background questions, (3) Password reset via email, (4) Anonymous chat history migration, and (5) Chat personalization based on user background.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/React 18+ (frontend)
**Primary Dependencies**: FastAPI (backend), React/Docusaurus (frontend), SQLAlchemy (ORM), python-jose (JWT), passlib (password hashing)
**Storage**: SQLite database with SQLAlchemy ORM
**Testing**: pytest (backend), Jest/React Testing Library (frontend)
**Target Platform**: Web application (browser-based)
**Project Type**: Web application with separate frontend and backend
**Performance Goals**: <2s authentication response time, <50ms session validation
**Constraints**: Must integrate with existing Docusaurus site and RAG chat system
**Scale/Scope**: Support 10k concurrent users, maintain 99.9% uptime

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principles Validation
- ✅ **Security First**: Using HTTP-only cookies, password hashing, JWT tokens, email verification
- ✅ **Privacy by Design**: Minimal data collection, explicit consent for background data
- ✅ **User Experience**: Progressive onboarding, clear value proposition, anonymous access path
- ✅ **Simplicity**: Single authentication method (email/password), extensible design for future OAuth

### Gates
1. **Security Gate**:
   - ✅ Password storage: bcrypt hashing with salt
   - ✅ Session management: JWT with HTTP-only cookies
   - ✅ CSRF protection: Required with cookie auth
   - ✅ Password reset: Time-limited secure email links

2. **Performance Gates**:
   - ⚠️ Database queries: Needs indexing strategy for sessions and user background
   - ⚠️ Session validation: Must optimize for chat requests (sliding expiration)
   - ⚠️ Onboarding data processing: Efficient retrieval for personalization

## Project Structure

### Documentation (this feature)

```text
specs/002-auth-modify/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── auth-api.yaml    # OpenAPI spec for auth endpoints
│   └── schemas/         # Pydantic models
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── auth.py           # User, Session, UserBackground models
│   │   └── chat.py           # Updated with user associations
│   ├── services/
│   │   ├── auth.py           # Authentication service
│   │   ├── email.py          # Password reset emails
│   │   └── personalization.py # Background-based response customization
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py       # Login, register, logout endpoints
│   │   │   └── users.py      # Profile, preferences endpoints
│   │   └── middleware/
│   │       ├── auth.py       # JWT validation middleware
│   │       └── csrf.py       # CSRF protection
│   └── database/
│       └── migrations/       # Alembic migrations
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/

frontend/src/
├── components/
│   ├── Auth/
│   │   ├── LoginButton.tsx     # Replaces OAuth button
│   │   ├── OnboardingModal.tsx # Multi-step onboarding flow
│   │   ├── UserProfile.tsx     # Profile display in nav
│   │   └── SettingsModal.tsx   # Update preferences/background
│   └── ChatWidget/
│       └── index.tsx           # Updated with auth checks
├── contexts/
│   └── AuthContext.tsx         # Authentication state
├── services/
│   └── api.ts                  # Axios with auth interceptors
└── types/
    └── auth.ts                 # TypeScript interfaces
```

**Structure Decision**: Web application with existing backend/frontend separation. Backend uses FastAPI with SQLite, frontend uses React within Docusaurus. Authentication integrates with existing chat system without disrupting anonymous access.

## Phase 0: Research & Technical Decisions

### Research Tasks

1. **Email Authentication Pattern**
   - **Task**: Research FastAPI email/password authentication best practices
   - **Decision**: Use passlib with bcrypt for password hashing, python-jose for JWT
   - **Rationale**: Industry standard, well-maintained, secure by default

2. **Onboarding Flow Design**
   - **Task**: Research progressive onboarding patterns
   - **Decision**: Multi-step modal with experience level selection, multi-select for languages
   - **Rationale**: Reduces cognitive load, improves completion rates

3. **Session Management Strategy**
   - **Task**: Research sliding expiration implementation
   - **Decision**: JWT with 7-day sliding expiration stored in HTTP-only cookies
   - **Rationale**: Balances security with user experience

4. **Anonymous Session Migration**
   - **Task**: Research temporary user session patterns
   - **Decision**: UUID-based sessions stored in Redis/memory with migration to user accounts
   - **Rationale**: Simple, reliable, allows seamless upgrade path

### Research Findings

See [research.md](./research.md) for detailed findings and alternatives.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

### API Contracts

See [/contracts](./contracts/) directory for OpenAPI specifications.

### Quick Start Guide

See [quickstart.md](./quickstart.md) for development setup.

## Phase 2: Implementation Tasks

### Backend Implementation

#### 2.1 Database Setup
- [ ] Create/update SQLAlchemy models (auth.py)
- [ ] Add UserBackground, OnboardingResponse, PasswordResetToken models
- [ ] Create Alembic migration for new tables
- [ ] Add database indexes for performance

#### 2.2 Authentication Service
- [ ] Implement password hashing with bcrypt
- [ ] JWT token creation/validation with sliding expiration
- [ ] Email service for password reset
- [ ] Session management with single session enforcement

#### 2.3 API Routes
- [ ] Auth routes: register, login, logout, refresh
- [ ] Password reset flow: request, validate, reset
- [ ] User profile and onboarding endpoints
- [ ] Middleware for protected routes (auth, CSRF)

#### 2.4 Chat Integration
- [ ] Update chat endpoints with authentication dependency
- [ ] Anonymous session tracking (3 message limit)
- [ ] Chat history migration logic
- [ ] Personalization service using UserBackground

### Frontend Implementation

#### 2.5 Auth Context & Infrastructure
- [ ] Create/update AuthProvider with login/logout functions
- [ ] Implement token refresh handling
- [ ] Axios interceptors for auth headers
- [ ] Error handling for auth failures

#### 2.6 UI Components
- [ ] Replace Google OAuth button with LoginButton
- [ ] Create OnboardingModal with multi-step form
- [ ] UserProfile component for navigation
- [ ] SettingsModal for updating background data

#### 2.7 Chat Widget Updates
- [ ] Add authentication check before chat
- [ ] Anonymous user message counter
- [ ] Show registration prompt after 3 messages
- [ ] Display user profile when authenticated

#### 2.8 Navigation & Routing
- [ ] Update Docusaurus theme for auth integration
- [ ] Conditional rendering based on auth state
- [ ] Protected route components if needed

## Success Metrics

### Technical Metrics
- Authentication success rate > 95%
- Session validation latency < 50ms
- Password reset completion rate > 80%
- Database query performance > 90% index coverage
- Zero security vulnerabilities in OWASP scan

### User Metrics
- Registration completion rate > 90%
- Onboarding completion rate > 90%
- Anonymous to registered conversion rate > 20%
- Average time to complete registration < 3 minutes

## Risks & Mitigations

### Technical Risks
1. **Password Security**
   - Mitigation: bcrypt with salt, enforce strong passwords, rate limiting

2. **Session Management Complexity**
   - Mitigation: Sliding expiration with careful testing, secure cookie flags

3. **Email Deliverability**
   - Mitigation: Use reliable email service, handle bounces gracefully

### User Experience Risks
1. **Registration Friction**
   - Mitigation: Progressive onboarding, clear value proposition, minimal required fields

2. **Migration Issues**
   - Mitigation: Robust error handling, fallback to anonymous session

## Timeline

- **Week 1**: Phase 0-1 (Research, Design, Contracts)
- **Week 2**: Phase 2 (Backend Authentication)
- **Week 3**: Phase 2 (Frontend Components & Integration)
- **Week 4**: Testing, Security Review, Deployment

Total estimated duration: 4 weeks

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Architecture follows constitution principles | N/A |