---

description: "Task list for Content Personalization feature implementation"
---

# Tasks: Content Personalization

**Input**: Design documents from `/specs/001-content-personalization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included for critical functionality as specified in the feature requirements

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create directory structure for personalization feature in backend/src/agents/, backend/src/api/routes/personalization.py, backend/src/services/personalization.py
- [ ] T002 [P] Install OpenAI Agents SDK with Gemini support: pip install "openai-agents[litellm]"
- [ ] T003 [P] Add Gemini API key to environment variables and .env.example
- [ ] T004 [P] Configure Redis for caching in docker-compose.yml
- [ ] T005 [P] Update frontend package.json with required dependencies: react-query, framer-motion, lucide-react

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create PersonalizationAgent base class in backend/src/agents/personalization_agent.py
- [X] T007 [P] Configure Gemini client with OpenAI compatibility in backend/src/agents/personalization_agent.py
- [X] T008 [P] Implement rate limiting middleware in backend/src/middleware/rate_limit.py
- [X] T009 [P] Create personalization cache utilities in backend/src/cache/personalization.py
- [X] T010 Create database migration for saved_personalizations table in backend/alembic/versions/001_add_personalization.py
- [X] T011 [P] Create base request/response models in backend/src/models/personalization.py
- [X] T012 [P] Create PersonalizationEngine service class in backend/src/services/personalization.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Guest User Attempts Personalization (Priority: P1) 🎯 MVP

**Goal**: Guest users clicking Personalize are prompted to authenticate without making backend calls

**Independent Test**: Access site as guest, click Personalize button, verify login modal appears and no backend personalization calls are made

### Tests for User Story 1 ⚠️

- [ ] T013 [P] [US1] Unit test: Guest user sees login prompt in tests/unit/test_guest_personalization.py
- [ ] T014 [P] [US1] Integration test: Personalize button disabled for guests in tests/integration/test_auth_flow.py

### Implementation for User Story 1

- [ ] T015 [US1] Add personalization check to AIFeaturesBar component in src/theme/DocItem/AIFeaturesBar.tsx
- [ ] T016 [US1] [P] Update API service to handle authentication for personalization in src/services/api.ts
- [ ] T017 [US1] Implement content extraction utility in src/utils/contentExtractor.ts
- [ ] T018 [US1] Show login modal when guest clicks Personalize button
- [ ] T019 [US1] Disable Personalize button for unauthenticated users

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Authenticated User Personalizes Content (Priority: P1) 🎯 MVP

**Goal**: Authenticated users can generate and view personalized content based on their background

**Independent Test**: Create test user with specific background, click Personalize, verify content is adapted accordingly

### Tests for User Story 2 ⚠️

- [ ] T020 [P] [US2] Contract test: POST /api/v1/personalize endpoint in tests/contract/test_personalization_api.py
- [ ] T021 [P] [US2] Integration test: End-to-end personalization flow in tests/integration/test_personalization_flow.py
- [ ] T022 [P] [US2] Performance test: Response time <10 seconds in tests/performance/test_personalization_speed.py

### Implementation for User Story 2

#### Backend Tasks

- [ ] T023 [P] [US2] Implement PersonalizationAgent with context-aware prompting in backend/src/agents/personalization_agent.py
- [ ] T024 [US2] [P] Create PersonalizationRequest schema in backend/src/schemas/personalization.py
- [ ] T025 [US2] [P] Create PersonalizationResponse schema in backend/src/schemas/personalization.py
- [ ] T026 [US2] Implement content personalization logic in PersonalizationEngine
- [ ] T027 [US2] Create POST /api/v1/personalize endpoint in backend/src/api/routes/personalization.py
- [ ] T028 [US2] Implement user background integration in personalization service
- [ ] T029 [US2] Add error handling for API failures and timeouts

#### Frontend Tasks

- [ ] T030 [P] [US2] Create PersonalizationModal component in src/components/Personalization/PersonalizationModal.tsx
- [ ] T031 [US2] [P] Implement modal state management in PersonalizationContext
- [ ] T032 [US2] Add loading indicator to Personalize button in AIFeaturesBar
- [ ] T033 [US2] [P] Add glassmorphism styling to PersonalizationModal
- [ ] T034 [US2] Implement copy to clipboard functionality in modal
- [ ] T035 [US2] Display adaptations made and processing time in modal

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - User with Incomplete Profile (Priority: P2)

**Goal**: Users with incomplete profiles receive general content and are prompted to complete profile

**Independent Test**: Create user without background data, attempt personalization, verify general content and profile prompt appears

### Tests for User Story 3 ⚠️

- [ ] T036 [P] [US3] Unit test: Default profile handling in tests/unit/test_profile_defaults.py
- [ ] T037 [P] [US3] Integration test: Incomplete profile flow in tests/integration/test_profile_handling.py

### Implementation for User Story 3

- [ ] T038 [P] [US3] Implement default profile logic in PersonalizationEngine
- [ ] T039 [US3] [P] Create default user profile factory in backend/src/utils/profile_defaults.py
- [ ] T040 [US3] Add profile completion prompt to PersonalizationModal
- [ ] T041 [US3] [P] Implement partial profile handling in backend/src/services/personalization.py
- [ ] T042 [US3] Update user experience for intermediate default explanations

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Save & Manage Personalizations (Extended Feature)

**Goal**: Users can save up to 10 personalized items and manage their saved content

**Independent Test**: Personalize content, save it, verify it appears in saved list

### Tests for Save Feature ⚠️

- [ ] T043 [P] Contract test: GET /api/v1/personalize/saved endpoint
- [ ] T044 [P] Contract test: DELETE /api/v1/personalize/saved/{id} endpoint
- [ ] T045 [P] Contract test: POST /api/v1/personalize/saved/{id}/rate endpoint

### Implementation for Save Feature

#### Backend Tasks

- [ ] T046 [P] Create SavedPersonalization model in backend/src/models/personalization.py
- [ ] T047 [P] Implement save personalization logic in PersonalizationEngine
- [ ] T048 [P] Create GET /api/v1/personalize/saved endpoint
- [ ] T049 [P] Create DELETE /api/v1/personalize/saved/{id} endpoint
- [ ] T050 [P] Create POST /api/v1/personalize/saved/{id}/rate endpoint
- [ ] T051 [P] Implement 10-item limit per user

#### Frontend Tasks

- [ ] T052 [P] Add Save button to PersonalizationModal
- [ ] T053 [P] Create Rating component with 1-5 stars
- [ ] T054 [P] Create SavedPersonalizationsList component
- [ ] T055 [P] Add delete functionality to saved items
- [ ] T056 [P] Update user stats display

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057 [P] Add comprehensive error handling with user-friendly messages
- [ ] T058 [P] Implement content preview in PersonalizationModal
- [ ] T059 [P] Add keyboard shortcuts (ESC to close modal, Ctrl+C to copy)
- [ ] T060 [P] Implement analytics tracking for personalization usage
- [ ] T061 [P] Add support for different content types (code blocks, tables)
- [ ] T062 [P] Optimize prompt engineering for better personalization quality
- [ ] T063 [P] Update user documentation with personalization feature guide
- [ ] T064 Run performance tests and optimize bottlenecks
- [ ] T065 [P] Add unit tests for edge cases (empty content, API failures)
- [ ] T066 [P] Implement streaming responses for long content
- [ ] T067 [P] Add dark mode support to PersonalizationModal
- [ ] T068 Security audit of personalization endpoints
- [ ] T069 Run quickstart.md validation checklist
- [ ] T070 [P] Create deployment checklist for personalization feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1) and User Story 2 (P1) can proceed in parallel for MVP
  - User Story 3 (P2) can follow or proceed in parallel if staffed
  - Save Feature (Phase 6) depends on User Story 2 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Core personalization functionality
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Extends US2 with default handling
- **Save Feature (Phase 6)**: Depends on User Story 2 completion

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models and schemas before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 and 2 can start in parallel (MVP approach)
- All tests for a user story marked [P] can run in parallel
- Backend and frontend tasks within the same story can run in parallel if properly defined
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2 (Core Personalization)

```bash
# Launch all tests for User Story 2 together:
Task: "Contract test: POST /api/v1/personalize endpoint in tests/contract/test_personalization_api.py"
Task: "Integration test: End-to-end personalization flow in tests/integration/test_personalization_flow.py"
Task: "Performance test: Response time <10 seconds in tests/performance/test_personalization_speed.py"

# Launch all backend models and schemas together:
Task: "Create PersonalizationRequest schema in backend/src/schemas/personalization.py"
Task: "Create PersonalizationResponse schema in backend/src/schemas/personalization.py"
Task: "Implement PersonalizationAgent with context-aware prompting in backend/src/agents/personalization_agent.py"

# Launch all frontend components together:
Task: "Create PersonalizationModal component in src/components/Personalization/PersonalizationModal.tsx"
Task: "Add glassmorphism styling to PersonalizationModal"
Task: "Implement copy to clipboard functionality in modal"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Guest handling)
4. Complete Phase 4: User Story 2 (Core personalization)
5. **STOP and VALIDATE**: Test both stories independently
6. Deploy/demo MVP functionality

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo
3. Add User Story 2 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Save Feature → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Guest handling)
   - Developer B: User Story 2 (Core personalization) - PRIMARY
   - Developer C: Begin User Story 3 (Profile handling)
3. User stories complete and integrate independently
4. Developer B continues with Save Feature after US2 complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- MVP consists of User Story 1 + User Story 2 only
- User Story 3 and Save Feature are post-MVP enhancements
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence