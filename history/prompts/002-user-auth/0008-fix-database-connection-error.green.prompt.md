---
id: 0008
title: fix-database-connection-error
stage: green
date: 2025-12-26
surface: agent
model: glm-4.7
feature: 002-user-auth
branch: 002-user-auth
user: User
command: [Continuation from previous session]
labels: [database, async, middleware, bugfix]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/api/routes/users.py
 - backend/src/core/database.py
tests:
 - Import test for users routes
 - Main app import test
---

## Prompt

This session is being continued from a previous conversation that ran out of context. The conversation is summarized below:

[The user had been working on implementing user authentication. The main issues were:
1. Onboarding modal not appearing after registration
2. Frontend state management issues - user logged out on page refresh
3. Token mismatch between different axios instances
4. Database connection error: `TypeError: connect() got an unexpected keyword argument 'sslmode'` when accessing `/api/v1/background` endpoint]

The last error showed a database connection problem in `src/security/dependencies.py`. The `get_current_user` function uses synchronous SQLAlchemy (`db.query(User)`) which doesn't work with async PostgreSQL (asyncpg driver). This causes the `sslmode` error when trying to create a new database connection.

Please continue the conversation from where we left it off without asking the user any further questions. Continue with the last task that you were asked to work on.

## Response snapshot

The issue was in `backend/src/api/routes/users.py` which was using:
1. Old `get_current_active_user` dependency from `src.security.dependencies` that uses synchronous database (`get_db`)
2. Synchronous `get_db` from `src.database.base`

The `/api/v1/background` endpoint uses these outdated dependencies. The middleware correctly sets `request.state.user` but the users routes don't use it.

**Fix Applied:**
1. Updated `backend/src/api/routes/users.py` to:
   - Use `get_async_db` from `src.core.database` instead of `get_db` from `src.database.base`
   - Use `request.state.user` from middleware instead of `get_current_active_user` dependency
   - Convert all synchronous queries (`db.query()`) to async queries (`await db.execute(select())`)
   - Use proper async patterns for commit/refresh operations

2. Installed missing dependencies:
   - `psycopg2-binary` for sync database operations
   - `sqlmodel` for User model

The authentication is actually working correctly (as shown by the successful `/api/v1/auth/me` call), but the database connection issue in the users routes was preventing authenticated endpoints from working.

## Outcome

- ✅ Impact: Fixed database connection error for authenticated user endpoints (like `/api/v1/background`)
- 🧪 Tests: Import tests passed for both users routes and main app
- 📁 Files: Updated `backend/src/api/routes/users.py` to use async database and middleware user object
- 🔁 Next prompts: Test the `/api/v1/background` endpoint with authenticated request in browser
- 🧠 Reflection: The root cause was synchronous SQLAlchemy being used with async PostgreSQL driver. The middleware already handled authentication correctly and set `request.state.user`, but the users routes were not using it.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A - manual testing required
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Test the `/api/v1/background` endpoint in browser with authenticated user to verify the fix works end-to-end
