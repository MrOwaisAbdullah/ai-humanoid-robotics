---

description: "Task list for Authentication and UX Improvements feature implementation"
---

# Tasks: Authentication and UX Improvements

**Input**: Design documents from `/specs/001-auth-ux-improvements/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`
- **Frontend**: `src/`
- **Tests**: `tests/backend/` and `tests/frontend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Verify existing project structure matches plan.md requirements
- [X] T002 Check AnonymousSession model exists in backend/src/models/auth.py
- [X] T003 Verify existing AuthContext in src/contexts/AuthContext.tsx
- [X] T004 Verify existing ChatWidget components in src/components/ChatWidget/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Add GET /auth/anonymous-session/{session_id} endpoint in backend/src/api/routes/auth.py
- [X] T006 Create sessionStorage utility in src/utils/sessionStorage.ts
- [X] T007 Update UserBackground model to match new schema in backend/src/models/auth.py
- [X] T008 Add UserBackground schema to backend/src/schemas/auth.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Guest Session Persistence (Priority: P1) 🎯 MVP

**Goal**: Guest users maintain their message count across page refreshes for 24 hours

**Independent Test**: Send messages as a guest, refresh the page, and verify the correct message count is still displayed

### Implementation for User Story 1

- [X] T009 [US1] Update ChatWidgetContainer.tsx to fetch session data on mount in src/components/ChatWidget/ChatWidgetContainer.tsx
- [X] T010 [US1] Update ChatInterface to initialize message count from backend in src/components/ChatWidget/components/ChatInterface.tsx
- [X] T011 [US1] Update chat API to track message count in AnonymousSession in backend/src/api/routes/chat.py
- [X] T012 [US1] Add fingerprint fallback logic to sessionStorage.ts in src/utils/sessionStorage.ts

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Persistent Authentication (Priority: P1)

**Goal**: Authenticated users stay logged in across browser sessions for 7 days

**Independent Test**: Log in, refresh the page, and verify the user remains authenticated

### Implementation for User Story 2

- [X] T013 [US2] Fix AuthContext token check on initialization in src/contexts/AuthContext.tsx
- [X] T014 [US2] Add silent token refresh mechanism in src/contexts/AuthContext.tsx
- [X] T015 [US2] Update login endpoint to set 7-day cookie in backend/src/api/routes/auth.py
- [X] T016 [US2] Add token refresh endpoint in backend/src/api/routes/auth.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Knowledge Collection During Registration (Priority: P2)

**Goal**: Collect software/hardware experience during user registration

**Independent Test**: Go through registration flow and verify background information is collected and stored

### Implementation for User Story 3

- [X] T017 [US3] Create RegistrationForm component in src/components/Auth/RegistrationForm.tsx
- [X] T018 [US3] Update registration API to accept background data in backend/src/api/routes/auth.py
- [X] T019 [US3] Update AuthContext register method to include background data in src/contexts/AuthContext.tsx
- [X] T020 [US3] Update UserCreate schema to include optional background fields in backend/src/schemas/auth.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Improved Message Limit Notifications (Priority: P2)

**Goal**: Clear notifications about remaining messages for guest users

**Independent Test**: Send messages as a guest and observe notification timing and content

### Implementation for User Story 4

- [X] T021 [US4] Update message limit warning to show after 2nd message in src/components/ChatWidget/components/ChatInterface.tsx
- [X] T022 [US4] Enhance AuthenticationBanner with dynamic message count in src/components/Auth/AuthenticationBanner.tsx
- [X] T023 [US4] Add visual message counter for guest users in src/components/ChatWidget/components/ChatInterface.tsx

---

## Phase 7: User Story 5 - Improved Course Navigation (Priority: P3)

**Goal**: Display "Module X" instead of "Part X" with Module 1 expanded by default

**Independent Test**: View course navigation and verify labels and expansion state

### Implementation for User Story 5

- [X] T024 [US5] Update sidebar labels from "Part" to "Module" in sidebars.ts
- [X] T025 [US5] Set Module 1 to expanded by default in sidebars.ts
- [X] T026 [US5] Add mobile CSS for navigation drawer in src/css/custom.css
- [X] T027 [US5] Hide GitHub and Read Book links on mobile in src/css/custom.css

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028 [P] Update all document references from "Part" to "Module" in docs/
- [X] T029 [P] Add error handling for session fetch failures
- [ ] T030 Add unit tests for sessionStorage utility in tests/frontend/utils/
- [ ] T031 Add integration tests for guest session persistence in tests/backend/integration/
- [ ] T032 Run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on existing auth system
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 implementation
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Independent of other stories

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority
- Backend models/services before frontend components

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories 1 and 2 can start in parallel (both P1)
- User stories 3 and 4 can start in parallel after P1 stories are complete
- Document updates in Phase 8 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch backend and frontend tasks for User Story 1 together:
Task: "Update ChatWidgetContainer.tsx to fetch session data on mount"
Task: "Update chat API to track message count in AnonymousSession"
Task: "Add fingerprint fallback logic to sessionStorage.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Stories 3 & 4 → Test independently → Deploy/Demo
5. Add User Story 5 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Guest Session Persistence)
   - Developer B: User Story 2 (Auth Persistence)
3. After P1 stories complete:
   - Developer A: User Story 3 (Knowledge Collection)
   - Developer B: User Story 4 (Message Notifications)
   - Developer C: User Story 5 (Navigation Updates)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- User Stories 1 & 2 are both P1 priority and should be completed first
- User Stories 3 & 4 are P2 priority and can be developed in parallel
- User Story 5 is P3 priority and can be developed independently
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence