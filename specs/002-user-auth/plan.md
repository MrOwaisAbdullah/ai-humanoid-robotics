# Implementation Plan: User Authentication

**Branch**: `002-user-auth` | **Date**: 2025-01-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-user-auth/spec.md`

## Summary

Implement a comprehensive authentication system for the AI book application using Better Auth v1.4.x with JWT plugin. The system will use Neon PostgreSQL with a hybrid approach: Better Auth manages authentication tables via direct PostgreSQL connection while SQLModel handles application-specific tables. Custom FastAPI endpoints will generate and validate Better Auth compatible JWTs, integrating with existing sign-in, register, and onboarding modals. Use context 7 mcp for laest docs.

ALWAYS USE BETTER-AUTH-SPECIALIST SUB AGENT AND SKILL FOR BETTER AUTH IMPLEMENTATION

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/React 18+ (frontend)
**Primary Dependencies**: Better Auth v1.4.x, FastAPI, SQLModel, Neon PostgreSQL, React, Resend (email)
**Storage**: Neon PostgreSQL (Better Auth tables via direct connection, SQLModel tables via ORM)
**Testing**: pytest (backend), Jest/React Testing Library (frontend)
**Target Platform**: Web application (Linux server, browser clients)
**Project Type**: Full-stack web application with hybrid authentication architecture
**Performance Goals**: <200ms p95 authentication response, 1000+ concurrent users, 2-second login
**Constraints**: JWT tokens 7-day expiry, bcrypt password hashing, email verification required
**Scale/Scope**: 10k+ users, 100+ req/s peak, support multiple concurrent sessions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Project Principles Check
- **Simplicity First**: Using Better Auth v1.4.x established patterns, direct PostgreSQL connection for auth tables, SQLModel for app data
- **Production-First**: All authentication flows include error handling, security headers, rate limiting from day one
- **Specification-First**: Complete spec with clarifications, all functional requirements defined with acceptance criteria
- **Co-Learning with AI**: Clarified architecture decisions using Better Auth specialist and Context7 MCP

### SOLID Principles Compliance
- **SRP**: Separate authentication concerns (Better Auth) from business logic (SQLModel)
- **OCP**: Direct PostgreSQL connection allows swapping SQLModel without affecting auth
- **DIP**: FastAPI depends on JWT abstraction, not specific auth implementation

### Gates Status
- ✅ Authentication complexity justified (required for personalized features)
- ✅ Hybrid architecture decision documented with clear rationale
- ✅ Better Auth v1.4.x confirmed as correct version (not v2)
- ✅ Database integration approach feasible (direct connection + SQLModel)

## Project Structure

### Documentation (this feature)

```text
specs/002-user-auth/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── api.md          # API endpoint specifications
│   └── emails.md       # Email template contracts
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure
backend/
├── src/
│   ├── core/
│   │   ├── auth.py           # Better Auth configuration and JWT utilities
│   │   ├── database.py       # Database connections (Better Auth + SQLModel)
│   │   └── security.py       # Security utilities (bcrypt, JWT validation)
│   ├── models/
│   │   ├── user.py          # SQLModel: UserPreferences, extended user data
│   │   └── chat.py          # SQLModel: ChatSession with user linking
│   ├── services/
│   │   ├── auth.py          # Custom auth service (JWT generation/validation)
│   │   ├── email.py         # Resend email service integration
│   │   └── chat.py          # Chat service with user session linking
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py      # Custom FastAPI auth endpoints
│   │       └── users.py     # User profile management endpoints
│   └── middleware/
│       └── auth.py          # JWT validation middleware
└── tests/
    ├── unit/
    │   ├── test_auth.py
    │   └── test_jwt.py
    └── integration/
        └── test_auth_flow.py

frontend/
├── src/
│   ├── components/
│   │   ├── Auth/
│   │   │   ├── SignInModal.tsx    # Enhanced with JWT handling
│   │   │   ├── RegisterModal.tsx   # Enhanced with error states
│   │   │   └── OnboardingModal.tsx # Enhanced with auth flow
│   │   └── ChatWidget/
│   │       └── hooks/
│   │           └── useChatSession.tsx # Enhanced with user linking
│   ├── services/
│   │   ├── api.ts          # API client with JWT header injection
│   │   └── auth.ts         # Auth service (token storage, refresh)
│   ├── context/
│   │   └── AuthContext.tsx # Authentication state management
│   └── types/
│       └── auth.ts         # TypeScript interfaces for auth
└── tests/
    └── components/
        └── Auth/
```

**Structure Decision**: Hybrid architecture leveraging Better Auth v1.4.x strengths while maintaining SQLModel for application data. Clear separation: Better Auth handles core authentication via direct PostgreSQL, FastAPI provides JWT-compatible endpoints, React manages auth state and UI flows.

## Phase 0: Research

### Completed Research Tasks

All technical decisions have been clarified through the `/sp.clarify` process. Key findings:

1. **Better Auth v1.4.x confirmed** - v2 does not exist yet, v1.4.x is latest stable with JWT plugin support
2. **Direct PostgreSQL connection** - Better Auth manages its tables via pg Pool, SQLModel manages app tables
3. **Custom FastAPI endpoints** - Generate/validate Better Auth compatible JWTs for hybrid architecture
4. **Email service** - Resend recommended for transactional emails ($0.003 per email)
5. **Security best practices** - httpOnly cookies for production, localStorage for development, CSRF protection

### No Outstanding Clarifications

All NEEDS CLARIFICATION items have been resolved:
- Better Auth version selected and confirmed
- Database integration approach defined
- Backend architecture decision made
- JWT strategy clarified

## Phase 1: Design & Contracts

### 1. Data Model Design

#### Better Auth Tables (managed via direct PostgreSQL)
- `users` - Core user data (email, name, password_hash, email_verified)
- `sessions` - JWT session tokens with expiration
- `verification_tokens` - Email verification and password reset tokens

#### SQLModel Tables (managed via ORM)
- `user_preferences` - User settings (theme, language, timezone, chat config)
- `chat_sessions` - Enhanced with user_id foreign key for linking
- `chat_messages` - Messages within sessions (unchanged)

### 2. API Contracts

#### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration with email verification
- `POST /api/v1/auth/login` - Authenticate and return JWT token
- `POST /api/v1/auth/logout` - Invalidate session token
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/refresh` - Refresh JWT token

#### Password Reset Flow
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm` - Confirm with token

#### Email Verification
- `POST /api/v1/auth/verify-email` - Verify email with token
- `POST /api/v1/auth/verify-email/resend` - Resend verification email

### 3. Email Templates

#### Template Types
- Email verification welcome
- Password reset notification
- Security alerts (login from new device)
- Password changed confirmation

#### Technical Implementation
- Resend API integration
- HTML templates with consistent branding
- Security headers and verification links
- Localization support prepared

### 4. Quickstart Guide

#### Implementation Steps
1. Environment setup (dependencies, .env)
2. Database configuration (Neon PostgreSQL)
3. Better Auth v1.4.x configuration with JWT plugin
4. Custom FastAPI endpoints implementation
5. Frontend integration with existing modals
6. Email service setup (Resend)
7. Testing procedures

#### Code Examples
- Complete auth configuration examples
- FastAPI endpoint implementations
- React context provider setup
- Token storage and refresh patterns

## Phase 2: Architecture Decisions

### Decision Records

#### ADR-001: Hybrid Authentication Architecture
**Status**: Accepted
**Decision**: Use Better Auth v1.4.x with custom FastAPI endpoints
**Rationale**:
- Leverages Better Auth's security features while maintaining FastAPI backend
- Direct PostgreSQL connection for auth tables avoids adapter complexity
- JWT plugin enables stateless API authentication
- Preserves existing SQLModel-based application architecture

#### ADR-002: Database Separation Strategy
**Status**: Accepted
**Decision**: Better Auth manages auth tables, SQLModel manages app tables
**Rationale**:
- Avoids complex adapter development
- Each system uses optimal database access pattern
- Clear separation of concerns
- Migration path preserved for existing data

#### ADR-003: JWT Token Strategy
**Status**: Accepted
**Decision**: Better Auth compatible JWTs with 7-day expiry
**Rationale**:
- Stateless authentication scales better
- Mobile and web clients unified
- Standard JWT libraries available
- 7-day expiry balances security and UX

## Complexity Tracking

No constitution violations requiring justification. All architectural decisions align with established principles:

| Complexity Source | Justification | Alternatives Considered | Why Rejected |
|------------------|----------------|-------------------------|--------------|
| Hybrid architecture | Maintains existing SQLModel stack while adding Better Auth security | Full Better Auth replacement, Custom auth only | Would require rewriting existing data models, or lose Better Auth's security features |
| Dual database connections | Optimal patterns for each system (direct connection vs ORM) | Single unified adapter | Significant development effort, maintenance burden |
| Custom JWT endpoints | Enables FastAPI integration while using Better Auth crypto | Pure Better Auth session-based auth | Stateful sessions complicate mobile API, stateless JWT preferred |

## Next Steps

With Phase 0 research complete and Phase 1 design finished:
1. **Execute Phase 2**: Run `/sp.tasks` to generate detailed implementation tasks
2. **Agent Context Update**: Run `.specify/scripts/bash/update-agent-context.sh claude`
3. **Implementation**: Follow tasks in priority order (P1 → P2 → P3)

The plan is ready for task generation and implementation.