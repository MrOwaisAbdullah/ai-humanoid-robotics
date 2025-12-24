# Implementation Tasks: User Authentication

**Feature**: User Authentication
**Created**: 2025-01-21
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Summary

Complete implementation of a hybrid authentication system using Better Auth v1.4.x with custom FastAPI endpoints for JWT token management. The system supports user registration, login, profile management, password reset, and email verification with Neon PostgreSQL storage and Resend email delivery.

## Implementation Strategy

### MVP Scope (Phase 3)
- User Story 1 (Registration) and User Story 2 (Login) form the core MVP
- These enable users to create accounts and access personalized features
- All other stories build on this foundation

### Incremental Delivery
1. **Phase 1-2**: Infrastructure setup (blocking all stories)
2. **Phase 3**: Core authentication (US1 + US2) - MVP
3. **Phase 4**: Profile management (US3) - enhances UX
4. **Phase 5**: Password reset (US4) - user support
5. **Phase 5**: Email verification (US5) - security enhancement
6. **Phase 6**: Polish and cross-cutting concerns

## Phase 1: Project Setup

### Goal
Initialize project structure and install required dependencies for the hybrid authentication system.

### Independent Test Criteria
- All dependencies installed without conflicts
- Environment configured for local development
- Database connection established

### Tasks

- [X] T001 Install backend dependencies (Better Auth v1.4.x, FastAPI, SQLModel, asyncpg, etc.)
- [X] T002 [P] Create backend directory structure per plan.md
- [ ] T003 [P] Install frontend dependencies (React 18+, TypeScript, axios, etc.)
- [ ] T004 [P] Create frontend directory structure per plan.md
- [X] T005 Configure environment variables (.env files for backend and frontend)
- [ ] T006 Set up Neon PostgreSQL database connection:
    1. Sign up at https://neon.tech
    2. Create a new project named "ai-book-auth"
    3. Copy the connection string (format: postgresql+asyncpg://[user]:[pass]@[host]/[db]?sslmode=require)
    4. Update backend/.env DATABASE_URL with your connection string
- [X] T007 Initialize Alembic for database migrations
- [X] T008 Configure Resend email service account

## Phase 2: Foundational Infrastructure

### Goal
Set up core authentication infrastructure that all user stories depend on.

### Independent Test Criteria
- Better Auth configured with PostgreSQL connection
- JWT service created and tested
- Database schema created with all tables
- Email service integrated

### Tasks

- [X] T009 Create Better Auth v1.4.x configuration with JWT plugin in backend/src/core/auth.py
- [X] T010 [P] Set up SQLModel database connection in backend/src/core/database.py
- [X] T011 Create JWT service for token generation and validation in backend/src/services/jwt.py
- [X] T012 Implement email service with Resend integration in backend/src/services/email.py
- [X] T013 [P] Create UserPreferences SQLModel in backend/src/models/user.py
- [X] T014 [P] Update ChatSession model to support user linking in backend/src/models/chat.py
- [X] T015 Create and run database migration for Better Auth and SQLModel tables
- [X] T016 Set up FastAPI application with CORS configuration in backend/src/main.py
- [X] T017 Create authentication schemas for request validation in backend/src/schemas/auth.py

## Phase 3: User Registration & Login (US1 & US2)

### Story Goal (US1)
Enable new users to create accounts with email and password, automatically creating default preferences and sending verification emails.

### Story Goal (US2)
Enable registered users to authenticate with email/password, receiving JWT tokens for session management.

### Independent Test Criteria
- User can register with valid credentials and receive JWT token
- Duplicate email registration is properly rejected
- User can login with valid credentials
- Invalid credentials show appropriate error messages
- JWT tokens are properly formatted and contain required claims

### Tasks

- [X] T018 Create custom authentication service in backend/src/services/auth.py
- [X] T019 [P] Implement user registration endpoint POST /api/v1/auth/register
- [X] T020 [P] Implement user login endpoint POST /api/v1/auth/login
- [X] T021 [P] Implement current user endpoint GET /api/v1/auth/me
- [X] T022 [P] Implement logout endpoint POST /api/v1/auth/logout
- [X] T023 [P] Implement token refresh endpoint POST /api/v1/auth/refresh
- [X] T024 [P] Create JWT validation middleware in backend/src/middleware/auth.py
- [X] T025 Create TypeScript interfaces for authentication in frontend/src/types/auth.ts
- [X] T026 [P] Create AuthContext provider in frontend/src/context/AuthContext.tsx
- [X] T027 [P] Update RegisterModal.tsx with registration functionality
- [X] T028 [P] Update SignInModal.tsx with login functionality
- [X] T029 [P] Create API client with JWT header injection in frontend/src/services/api.ts
- [X] T030 Integrate AuthProvider in App component for auth state management

## Phase 4: Profile Management (US3)

### Story Goal
Allow logged-in users to update their profile information and preferences that persist across sessions.

### Independent Test Criteria
- User can update name, timezone, and language
- User preferences are saved and retrieved correctly
- Preferences persist across logout/login cycles
- Invalid preference updates are rejected

### Tasks

- [X] T031 [P] Create UserPreferencesUpdateSchema in backend/src/schemas/auth.py
- [X] T032 [P] Implement profile update endpoint PUT /api/v1/auth/me
- [X] T033 [P] Create profile management component in frontend/src/components/Profile/
- [X] T034 [P] Add preference settings UI (theme, language, timezone)
- [X] T035 [P] Implement notification preferences toggle
- [X] T036 [P] Implement chat settings configuration

## Phase 5.1: Password Reset (US4)

### Story Goal
Enable users who forgot their password to securely reset it via email links with 1-hour expiry.

### Independent Test Criteria
- User can request password reset with email
- Password reset email contains valid link
- User can reset password with valid token within 1 hour
- Expired or invalid tokens are properly rejected

### Tasks

- [X] T037 [P] Create PasswordResetSchema and ConfirmPasswordResetSchema
- [X] T038 [P] Implement password reset request endpoint POST /api/v1/auth/password-reset
- [X] T039 [P] Implement password reset confirmation endpoint POST /api/v1/auth/password-reset/confirm
- [X] T040 [P] Create password reset email template
- [X] T041 [P] Create forgot password page/form in frontend
- [X] T042 [P] Create reset password page/form with token validation

## Phase 5.2: Email Verification (US5)

### Story Goal
Require email verification before allowing login, ensuring account security and valid communication channels.

### Independent Test Criteria
- Email verification is sent upon registration
- User cannot login without verifying email
- Verification link properly marks account as verified
- Unverified users see appropriate messaging

### Tasks

- [X] T043 [P] Configure Better Auth to require email verification before login
- [X] T044 [P] Implement email verification endpoint POST /api/v1/auth/verify-email
- [X] T045 [P] Implement resend verification email endpoint POST /api/v1/auth/verify-email/resend
- [X] T046 [P] Create email verification template
- [X] T047 [P] Add email verification status to login flow
- [X] T048 [P] Create email verification reminder component
- [X] T049 [P] Update registration flow to show verification requirement

## Phase 6: Chat System Integration

### Goal
Link anonymous chat sessions to authenticated users and ensure chat features respect user authentication status.

### Independent Test Criteria
- Anonymous sessions can be linked to authenticated users
- Chat endpoints require valid authentication
- User-specific chat history is preserved

### Tasks

- [X] T050 [P] Create session linking endpoint POST /api/v1/auth/link-sessions
- [X] T051 [P] Update chat session creation to associate with authenticated user
- [X] T052 [P] Implement authentication middleware for chat endpoints
- [X] T053 [P] Update ChatWidget to use authenticated user context
- [X] T054 [P] Implement session migration service for anonymous-to-authenticated flow
- [X] T055 [P] Add "Link previous chats" option to user profile

## Phase 7: Polish & Cross-Cutting Concerns

### Goal
Add security features, error handling, monitoring, and performance optimizations.

### Independent Test Criteria
- Rate limiting prevents abuse
- All endpoints have proper error handling
- Security headers are present
- Performance meets requirements (<200ms p95)

### Tasks

- [X] T056 [P] Implement rate limiting on authentication endpoints
- [X] T057 [P] Add comprehensive error handling with user-friendly messages
- [X] T058 [P] Implement security headers middleware
- [X] T059 [P] Add logging for authentication events
- [X] T060 [P] Create health check endpoint for auth service
- [X] T061 [P] Add input validation and sanitization
- [X] T062 [P] Implement session cleanup job for expired sessions
- [X] T063 [P] Add loading states and error displays to all auth components
- [X] T064 [P] Create comprehensive error messages for all failure scenarios
- [X] T065 [P] Optimize database queries with proper indexes
- [X] T066 [P] Add TypeScript strict mode to all frontend files
- [X] T067 [P] Create documentation for API endpoints
- [X] T068 [P] Add integration tests for complete auth flows

## Dependencies

### Story Completion Order
1. **Phase 1-2** (Setup & Foundational): Must complete before any user stories
2. **US1 & US2** (Registration & Login): Core MVP, foundation for all other stories
3. **US3** (Profile Management): Depends on US1 & US2 for user context
4. **US4** (Password Reset): Depends on US1 for user existence
5. **US5** (Email Verification): Depends on US1 for user registration
6. **Integration**: Depends on US1 & US2 for user context

### Parallel Execution Opportunities

#### Phase 3 (US1 & US2)
- Backend endpoints can be implemented in parallel: T019, T020, T021, T022, T023
- Frontend components can be implemented in parallel: T027, T028, T029
- Database models can be implemented in parallel with backend endpoints

#### Phase 4 (US3)
- Backend endpoint T032 can be implemented while frontend profile component T033 is being built
- Individual preference settings can be implemented in parallel: T034, T035, T036

#### Phase 5 (US4 & US5)
- Password reset (US4) and email verification (US5) can be implemented in parallel
- Frontend forms for both can be built concurrently

#### Phase 6 & 7
- Most tasks are independent and can be parallelized
- Cross-cutting concerns can be addressed incrementally

## Independent Testing Strategy

Each user story has an independent test that can be executed without other stories:

1. **US1 (Registration)**: Test complete registration flow from UI to database
2. **US2 (Login)**: Test login with credentials created in US1
3. **US3 (Profile)**: Test profile updates with authenticated user from US2
4. **US4 (Password Reset)**: Test reset flow with existing user
5. **US5 (Email Verification)**: Test verification requirement blocks login

## Total Tasks: 68

- Phase 1: 8 tasks
- Phase 2: 9 tasks
- Phase 3: 13 tasks
- Phase 4: 6 tasks
- Phase 5.1: 6 tasks
- Phase 5.2: 7 tasks
- Phase 6: 6 tasks
- Phase 7: 13 tasks

## Implementation Notes

1. **Hybrid Database Approach**: Better Auth manages auth tables directly via PostgreSQL pool, SQLModel manages application data via async connection
2. **JWT Strategy**: Custom FastAPI endpoints generate/validate JWTs compatible with Better Auth's cryptographic standards
3. **Email Integration**: Resend service for transactional emails (verification, password reset)
4. **Session Management**: Stateless JWT tokens with 7-day expiry and refresh capability
5. **Security**: bcrypt for passwords, CSRF protection, rate limiting, security headers
6. **Frontend**: React Context for auth state, automatic token injection, handling of expired tokens