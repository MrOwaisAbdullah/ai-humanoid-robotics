# Implementation Tasks: Authentication Modification

**Feature Branch**: `002-auth-modify`
**Created**: 2025-01-08
**Total Tasks**: 109
**Estimated Duration**: 4 weeks

## Phase 1: Setup (Project Initialization)

### Goal
Prepare development environment and install dependencies

- [X] T001 Install backend authentication dependencies in backend/requirements.txt
- [X] T002 [P] Install frontend dependencies (axios, react-hook-form, @hookform/resolvers, zod) in frontend/package.json
- [X] T003 Create backend/src/models/auth.py file structure
- [X] T004 [P] Create frontend/src/contexts/AuthContext.tsx file structure
- [X] T005 Set up environment variables template (.env.example) with auth secrets
- [X] T006 Update requirements.txt with python-jose, passlib, python-multipart, aiosmtplib, jinja2, alembic
- [X] T007 Add TypeScript type definitions in frontend/src/types/auth.ts

## Phase 2: Foundational (Blocking Prerequisites)

### Goal
Implement core authentication infrastructure that all user stories depend on

- [X] T008 Create database configuration in backend/src/database/config.py with SQLite setup
- [X] T009 [P] Create SQLAlchemy models in backend/src/models/auth.py (User, Session, UserBackground, PasswordResetToken)
- [X] T010 Set up Alembic for database migrations
- [X] T011 Create initial database migration with auth tables (Alembic)
- [X] T012 Add database indexes for performance (sessions user_id, token_hash, expires_at)
- [X] T013 Implement JWT token utilities in backend/src/services/auth.py (create, verify, refresh)
- [X] T014 [P] Configure FastAPI CORS settings for cookies in backend/main.py
- [X] T015 Create anonymous session tracking utility in backend/src/services/anonymous.py
- [X] T016 Implement password hashing utilities with bcrypt
- [X] T017 [P] Create Pydantic schemas in backend/src/schemas/auth.py
- [X] T018 Set up email service configuration for password resets
- [X] T019 Create FastAPI security dependencies (HTTPBearer, OAuth2PasswordRequestForm)

## Phase 3: User Story 1 - Email/Password Registration (P1)

### Goal
Enable users to sign in using email/password and view their profile

**Independent Test**: Click sign-in button, authenticate with email/password, verify profile display in navigation

- [X] T020 [US1] Create Google OAuth hide functionality in frontend/src/components/Auth/LoginButton.tsx
- [X] T021 [US1] Implement email/password registration route in backend/src/api/routes/auth.py (/auth/register)
- [X] T022 [US1] Implement email/password login route in backend/src/api/routes/auth.py (/auth/login)
- [X] T023 [US1] Create user retrieval endpoint (/auth/me) for profile display
- [X] T024 [P] [US1] Create React AuthProvider in frontend/src/contexts/AuthContext.tsx
- [X] T025 [P] [US1] Implement login button component with modal for email/password
- [X] T026 [US1] Add email/password login button to Docusaurus navigation
- [X] T027 [US1] Display user profile information in navigation bar when authenticated
- [X] T028 [P] [US1] Implement Axios interceptors for token handling in frontend/src/services/api.ts
- [X] T029 [US1] Create login form validation with react-hook-form and zod
- [X] T030 [US1] Implement password reset request flow
- [X] T031 [US1] Add email validation and uniqueness checks
- [X] T032 [US1] Test complete email/password authentication flow end-to-end
- [X] T033 [US1] Update existing chat integration to check for authentication

## Phase 4: User Story 2 - Onboarding Data Collection (P1)

### Goal
Collect user background data during registration for personalization

**Independent Test**: Create account, complete onboarding questions, verify answers saved and personalization applied

- [X] T034 [US2] Create onboarding modal component in frontend/src/components/Auth/OnboardingModal.tsx
- [X] T035 [US2] Create UserBackground model in backend/src/models/auth.py with experience fields
- [X] T036 [P] [US2] Create onboarding question components (experience level, years, languages, hardware)
- [X] T037 [US2] Implement onboarding submission endpoint (/users/onboarding) in backend/src/api/routes/users.py
- [X] T038 [US2] Create OnboardingResponse model for tracking question answers
- [X] T039 [US2] Add multi-step form wizard logic to onboarding modal
- [X] T040 [US2] Implement progress indicator for onboarding flow
- [X] T041 [US2] Save onboarding responses to database with timestamps
- [X] T042 [US2] Create skip onboarding option with reminder
- [X] T043 [US2] Test onboarding flow completion and data persistence

## Phase 5: User Story 3 - Chat Access for Authenticated Users (P1)

### Goal
Allow authenticated users to use chat with persistent history

**Independent Test**: Sign in, use chat, send message, verify conversation saved and retrievable

- [ ] T044 [US3] Update chat endpoint with authentication dependency in backend/src/api/routes/chat.py
- [ ] T045 [US3] Create ChatSession model for thread-based conversations in backend/src/models/chat.py
- [ ] T046 [P] [US3] Update ChatMessage model with user association and metadata
- [ ] T047 [US3] Implement chat history persistence in chat handler service
- [ ] T048 [US3] Add auto-title generation for chat sessions (first 50 chars)
- [ ] T048a [US3] [P] Implement title generation utility function in backend/src/services/title_generator.py
- [ ] T048b [US3] Update chat session creation to auto-generate title from first message content
- [ ] T049 [US3] Implement anonymous user message counter (limit 3 messages)
- [ ] T050 [US3] Create anonymous session to authenticated user migration logic
- [ ] T051 [US3] Update ChatWidget to check authentication status before access
- [ ] T052 [US3] Add registration prompt after 3 anonymous messages
- [ ] T053 [US3] Display chat history for authenticated users
- [ ] T054 [US3] Migrate last 10 messages from anonymous session to user account
- [ ] T055 [US3] Test chat persistence across browser sessions
- [ ] T056 [US3] Implement personalization service using UserBackground data

## Phase 6: User Story 4 - Secure Logout (P2)

### Goal
Enable users to securely sign out and invalidate sessions

**Independent Test**: Click logout, verify session termination and redirect to homepage

- [ ] T057 [US4] Create logout endpoint with session invalidation in backend/src/api/routes/auth.py
- [ ] T058 [US4] Implement single session enforcement (invalidate previous sessions)
- [ ] T059 [P] [US4] Add logout button to navigation bar in frontend
- [ ] T060 [US4] Clear HTTP-only cookie on logout
- [ ] T061 [US4] Redirect to homepage after logout
- [ ] T062 [US4] Test protected route access after logout
- [ ] T063 [US4] Verify session token expiration handling
- [ ] T064 [US4] Add session refresh functionality for sliding expiration

## Phase 7: User Preferences Management (P2)

### Goal
Allow users to manage their theme, language, and notification settings

- [ ] T065 Create UserPreferences model in backend/src/models/auth.py
- [ ] T066 [P] Implement preferences GET endpoint (/users/preferences) in backend/src/api/routes/users.py
- [ ] T067 [P] Implement preferences PUT endpoint (/users/preferences) in backend/src/api/routes/users.py
- [ ] T068 Create preferences validation Pydantic models
- [ ] T069 [P] Create SettingsModal component in frontend/src/components/Auth/SettingsModal.tsx
- [ ] T070 Implement theme switching (light/dark/auto) in frontend
- [ ] T071 Add language selection dropdown in settings
- [ ] T072 Implement notification toggle settings
- [ ] T072a Add email notification preferences (chat responses, mentions)
- [ ] T072b Implement browser notification permissions and display
- [ ] T072c Add notification frequency settings (immediate, hourly, daily digest)
- [ ] T072d Create notification preferences API endpoints
- [ ] T073 Create chat-specific settings (model, temperature) in settings modal
- [ ] T074 Test preferences persistence and application across sessions

## Phase 8: Security & Performance Enhancements

### Goal
Implement security best practices and performance optimizations

- [ ] T075 Implement CSRF protection middleware for cookie-based auth
- [ ] T076 [P] Add rate limiting on authentication endpoints
- [ ] T076a [P] Implement rate limiting on registration endpoint (5 attempts per hour per IP)
- [ ] T076b [P] Implement rate limiting on login endpoint (10 attempts per minute per IP)
- [ ] T076c [P] Implement rate limiting on password reset endpoint (3 attempts per hour per email)
- [ ] T076d [P] Add rate limiting on chat endpoint (20 messages per minute per user)
- [ ] T081 [P] Configure secure cookie settings (HttpOnly, Secure, SameSite)
- [ ] T082 Implement password strength validation (min 8 chars, letters + numbers)
- [ ] T083 Add account lockout after failed login attempts
- [ ] T084 [P] Optimize database queries with proper indexing
- [ ] T085 [P] Implement session caching for faster validation
- [ ] T086 Add request logging for security monitoring
- [ ] T087 Implement email verification for new accounts

## Phase 8.5: Accessibility Compliance (Critical)

### Goal
Ensure WCAG 2.1 AA compliance for all authentication and user interface components

- [ ] T087a [A11y] Add ARIA labels to all form inputs (email, password, onboarding)
- [ ] T087b [A11y] Implement keyboard navigation for all modals (login, onboarding, settings)
- [ ] T087c [A11y] Add screen reader support for form validation errors
- [ ] T087d [A11y] Ensure color contrast ratios meet WCAG AA standards (4.5:1 for normal text)
- [ ] T087e [A11y] Add focus indicators for all interactive elements
- [ ] T087f [A11y] Implement skip links for navigation
- [ ] T087g [A11y] Add semantic HTML structure (proper heading hierarchy, landmarks)
- [ ] T087h [A11y] Test with screen readers (NVDA, VoiceOver)
- [ ] T087i [A11y] Test keyboard-only navigation
- [ ] T087j [A11y] Add accessibility testing to CI/CD pipeline

## Phase 9: Testing & Documentation

### Goal
Ensure comprehensive test coverage and documentation

- [ ] T098 [P] Write unit tests for authentication service
- [ ] T099 [P] Write integration tests for email/password auth flow
- [ ] T100 [P] Write E2E tests for complete auth journey
- [ ] T101 Write security tests (CSRF, XSS, session hijacking)
- [ ] T102 Update API documentation with OpenAPI specs
- [ ] T103 Create developer setup guide
- [ ] T104 Document authentication flow and architecture decisions
- [ ] T105 Create troubleshooting guide for common auth issues

## Dependencies

### Phase Dependencies
- Phase 2 must complete before any User Story phase (foundational auth)
- Phase 3 (US1) must complete before Phase 4, 5, 6 (needs auth)
- Phase 4 (US2) should complete before Phase 6 (personalization)
- Phase 5 (US3) can run in parallel with Phase 4 after US1

### Parallel Execution Opportunities

**Within User Stories:**
- T024-T027 can be parallel (all frontend US1 components)
- T035-T038 can be parallel (backend onboarding models and endpoints)
- T046-T048 can be parallel (chat models and persistence logic)
- T059-T061 can be parallel (frontend logout components)
- T066-T069 can be parallel (preferences endpoints and UI)

**Across Stories:**
- Once US1 is complete, US2, US3, and US4 can be implemented in parallel by different developers
- Phase 8 (Security) can be worked on in parallel with user stories after initial implementation

## Independent Test Criteria

### User Story 1
1. Navigate to homepage
2. Click "Login" button (not Google OAuth)
3. Enter email and password in modal
4. Verify successful authentication
5. Verify user profile appears in navigation
6. Verify session persists on page refresh

### User Story 2
1. Register new account
2. Complete onboarding questions in modal
3. Verify all questions presented (experience, years, languages, hardware)
4. Submit onboarding form
5. Check settings page to verify background saved
6. Start chat and verify responses reference background

### User Story 3
1. Sign in with email/password
2. Open chat widget
3. Send a message
4. Receive AI response
5. Close and reopen chat widget
6. Verify conversation history displayed
7. Refresh page and verify history persists

### User Story 4
1. Sign in with email/password
2. Click logout button
3. Verify redirect to homepage
4. Try to access chat widget
5. Verify prompted to sign in again
6. Check browser cookies - verify access_token cleared

## Implementation Strategy

### MVP Scope (First Release)
Complete User Story 1 (Email/Password Registration) only:
- Enables basic authentication with email/password
- Replaces Google OAuth with login button
- Users can sign in and see their profile
- Foundation for adding onboarding later

### Incremental Delivery
1. **Week 1**: Phase 1-2 + US1 (Email/Password Auth)
2. **Week 2**: Phase 3 (Onboarding) + US2
3. **Week 3**: Phase 4 (Chat Integration) + US3 + US4
4. **Week 4**: Phase 5-9 (Preferences, Security, Testing, Documentation)

### Risk Mitigation
- Deploy US1 first to verify email/password flow works in production
- Test anonymous migration thoroughly before enabling
- Implement rate limiting early to prevent abuse
- Keep anonymous access optional during rollout

## File Paths Reference

### Backend Files
- `backend/requirements.txt` - Dependencies
- `backend/src/database/config.py` - Database setup
- `backend/src/models/auth.py` - SQLAlchemy auth models
- `backend/src/models/chat.py` - Updated chat models
- `backend/src/services/auth.py` - Authentication logic
- `backend/src/services/email.py` - Password reset emails
- `backend/src/api/routes/auth.py` - Auth API routes
- `backend/src/api/routes/users.py` - User management routes
- `backend/src/middleware/auth.py` - JWT validation middleware
- `backend/src/middleware/csrf.py` - CSRF protection
- `backend/main.py` - FastAPI app integration
- `backend/rag/chat.py` - Chat integration updates

### Frontend Files
- `frontend/src/contexts/AuthContext.tsx` - Auth state management
- `frontend/src/components/Auth/LoginButton.tsx` - Login component
- `frontend/src/components/Auth/OnboardingModal.tsx` - Onboarding flow
- `frontend/src/components/Auth/UserProfile.tsx` - Profile display
- `frontend/src/components/Auth/SettingsModal.tsx` - Preferences UI
- `frontend/src/components/ChatWidget/index.tsx` - Chat updates
- `frontend/src/services/api.ts` - Axios with auth interceptors
- `frontend/src/types/auth.ts` - TypeScript interfaces
- `frontend/src/theme/Root.tsx` - Docusaurus theme integration

### Configuration
- `.env` - Environment variables
- `.env.example` - Environment template
- `alembic/versions/` - Database migrations

## Success Metrics

### Technical Metrics
- Authentication success rate: >95%
- Session validation latency: <50ms
- Database query performance: >90% index coverage
- Zero security vulnerabilities in OWASP scan

### User Metrics
- Registration completion rate: >90%
- Chat session persistence: 100%
- Settings save success rate: >99%
- Average sign-in time: <30 seconds
- Onboarding completion rate: >90%

## Rollback Plan

If any User Story fails in production:
1. Deploy previous version without affected feature
2. Keep database schema changes (backward compatible)
3. Document issues for next iteration
4. Maintain anonymous access as fallback