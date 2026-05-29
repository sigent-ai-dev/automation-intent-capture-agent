# Tasks: Vite 6 Upgrade and Cognito Authentication

**Input**: Design documents from `specs/006-vite6-cognito-auth/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — SC-005 in the spec explicitly requires auth unit tests with full coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Vite 6 upgrade and Cognito Terraform provisioning — foundational work that all auth stories depend on.

- [x] T001 Upgrade vite to ^6.0.0, vitest to ^2.0.0, @vitejs/plugin-react to ^4.3.0, @testing-library/react to ^16.0.0 in frontend/package.json
- [x] T002 Upgrade jsdom to ^25.0.0 and @testing-library/jest-dom to ^6.6.0 in frontend/package.json for vitest 2 compatibility
- [x] T003 Run npm install and fix any peer dependency conflicts in frontend/
- [x] T004 Update frontend/vite.config.ts for Vite 6 compatibility (verify dev server and proxy config still works)
- [x] T005 Run existing test suite (npm test) and fix any vitest 2.x breaking changes in frontend/src/test-setup.ts
- [x] T006 Verify npm run build produces valid output and npm run dev starts without errors
- [x] T007 [P] Create terraform/modules/cognito/variables.tf with user pool configuration variables (project_name, environment, callback_urls)
- [x] T008 [P] Create terraform/modules/cognito/main.tf with Cognito user pool, domain, SPA client, and user groups (admin, user)
- [x] T009 [P] Create terraform/modules/cognito/outputs.tf exposing user_pool_id, client_id, domain
- [x] T010 Wire cognito module into terraform/main.tf and add cognito variables to terraform/variables.tf

**Checkpoint**: Vite 6 builds/tests pass, Cognito infrastructure is defined.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core auth infrastructure that MUST be complete before ANY user story can be implemented.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T011 Add aws-amplify ^6.16.3 and @aws-amplify/auth ^6.0.0 to frontend/package.json dependencies
- [x] T012 Create frontend/src/types/auth.ts with AuthState union type and AuthUser interface per data-model.md
- [x] T013 Create frontend/src/config/amplify.ts with configureAmplify() function reading VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID env vars
- [x] T014 Call configureAmplify() in frontend/src/main.tsx before React render
- [x] T015 Create frontend/.env.example with all VITE_COGNITO_* environment variables documented

**Checkpoint**: Foundation ready — Amplify configured, types defined, user story implementation can begin.

---

## Phase 3: User Story 3 - Build Tooling Upgrade (Priority: P1) MVP

**Goal**: Verify that the Vite 5→6 upgrade from Phase 1 is fully working with all existing functionality intact.

**Independent Test**: Run `npm run dev`, `npm run build`, and `npm test` — all must pass with zero modifications to test logic.

### Implementation for User Story 3

- [x] T016 [US3] Verify all existing unit tests pass with vitest 2.x in frontend/ (fix imports if needed)
- [x] T017 [US3] Verify Playwright E2E tests pass with Vite 6 dev server in frontend/
- [x] T018 [US3] Update .github/workflows/ci.yml frontend job if any commands changed for Vite 6

**Checkpoint**: All existing tests pass, CI green, Vite 6 upgrade complete.

---

## Phase 4: User Story 1 - Authenticated User Accesses Voice Interface (Priority: P1) MVP

**Goal**: Unauthenticated users see a login form; authenticated users access the voice interface with token attached to WebSocket.

**Independent Test**: Create a Cognito user, log in via the form, verify voice interface appears with valid token in Sec-WebSocket-Protocol header.

### Tests for User Story 1

- [x] T019 [P] [US1] Create frontend/tests/unit/services/authService.test.ts with tests for login, getToken, isAuthenticated (mock aws-amplify/auth)
- [x] T020 [P] [US1] Create frontend/tests/unit/contexts/AuthContext.test.tsx testing state transitions (loading → authenticated, loading → unauthenticated)

### Implementation for User Story 1

- [x] T021 [P] [US1] Create frontend/src/services/authService.ts with login(), getToken(), isAuthenticated() functions using Amplify signIn and fetchAuthSession
- [x] T022 [US1] Create frontend/src/contexts/AuthContext.tsx with AuthProvider implementing state machine (loading → authenticated | unauthenticated)
- [x] T023 [US1] Create frontend/src/components/auth/LoginForm.tsx with email/password form, error display, and loading state
- [x] T024 [US1] Update frontend/src/App.tsx to wrap with AuthProvider and conditionally render LoginForm vs existing voice interface based on auth state
- [x] T025 [US1] Update frontend/src/services/websocketService.ts to pass Cognito ID token via Sec-WebSocket-Protocol header per contracts/websocket-auth.md (note: backend must echo accepted protocol — see follow-up in T025a)
- [x] T025a [US1] Document backend requirement: WebSocket upgrade handler must extract token from Sec-WebSocket-Protocol, validate JWT, and echo 'v1.audio.intent' as accepted protocol (add TODO comment in src/server/websocket.py or create follow-up issue)
- [x] T026 [US1] Handle session expiry in AuthContext — redirect to unauthenticated state when token refresh fails; verify session persists across page refresh (Amplify localStorage tokens)

**Checkpoint**: Login works, voice interface is gated behind auth, WebSocket carries token.

---

## Phase 5: User Story 2 - User Signs Out (Priority: P2)

**Goal**: Authenticated users can sign out, terminating session and WebSocket connection.

**Independent Test**: Log in, verify voice interface visible, click sign out, confirm login form reappears and WebSocket disconnects.

### Tests for User Story 2

- [x] T027 [P] [US2] Add logout() test to frontend/tests/unit/services/authService.test.ts (verify signOut called)

### Implementation for User Story 2

- [x] T028 [US2] Add logout() function to frontend/src/services/authService.ts calling Amplify signOut
- [x] T029 [US2] Add logout method to AuthContext that calls authService.logout(), clears user state, sets state to unauthenticated in frontend/src/contexts/AuthContext.tsx
- [x] T030 [US2] Add sign-out button to frontend/src/components/layout/Header.tsx (visible when authenticated)
- [x] T031 [US2] Ensure WebSocket connection is closed on logout in frontend/src/services/websocketService.ts

**Checkpoint**: Sign out works end-to-end, WebSocket disconnects cleanly.

---

## Phase 6: User Story 5 - Federated Sign-In (Priority: P2)

**Goal**: Users can sign in via Microsoft, Okta, or Google identity providers using OAuth2/OIDC redirect.

**Independent Test**: Configure a federated provider in Cognito, click provider button, complete external auth, verify redirect back lands on voice interface.

### Tests for User Story 5

- [x] T032 [P] [US5] Add federatedSignIn() test to frontend/tests/unit/services/authService.test.ts (mock signInWithRedirect)
- [x] T033 [P] [US5] Create frontend/tests/unit/components/auth/LoginForm.test.tsx testing federation buttons visibility toggle

### Implementation for User Story 5

- [x] T034 [US5] Add federatedSignIn() function to frontend/src/services/authService.ts with signInWithRedirect + hosted UI fallback per research.md R4
- [x] T035 [US5] Add federated provider buttons to frontend/src/components/auth/LoginForm.tsx (Microsoft, Okta, Google) toggled by VITE_ENABLE_FEDERATION env var
- [x] T036 [US5] Add VITE_COGNITO_DOMAIN and VITE_COGNITO_REDIRECT_URI to frontend/src/config/amplify.ts for hosted UI fallback
- [x] T037 [US5] Handle federation error state in LoginForm (redirect failure shows error message)

**Checkpoint**: Federated sign-in redirect cycle works, buttons toggle via env var.

---

## Phase 7: User Story 4 - New Password Challenge (Priority: P3)

**Goal**: Admin-created users are prompted to set a new password on first login.

**Independent Test**: Create user via admin API, log in with temporary password, verify new-password form appears and works.

### Tests for User Story 4

- [x] T038 [P] [US4] Add completeNewPassword() test to frontend/tests/unit/services/authService.test.ts (mock confirmSignIn)

### Implementation for User Story 4

- [x] T039 [US4] Add completeNewPassword() function to frontend/src/services/authService.ts calling Amplify confirmSignIn
- [x] T040 [US4] Create frontend/src/components/auth/NewPasswordForm.tsx with new password input and submit
- [x] T041 [US4] Add completeNewPassword method to AuthContext and handle new-password-required state transition in frontend/src/contexts/AuthContext.tsx
- [x] T042 [US4] Update frontend/src/App.tsx to render NewPasswordForm when auth state is new-password-required

**Checkpoint**: New password flow works for admin-provisioned accounts.

---

## Phase 8: User Story 6 - Role-Based Access Control (Priority: P3)

**Goal**: Implement route guard mechanism based on Cognito group membership (guards future admin panel).

**Independent Test**: Create users in different groups, log in as each, verify RoleGuard blocks/allows access correctly.

### Tests for User Story 6

- [x] T043 [P] [US6] Create frontend/tests/unit/components/auth/RoleGuard.test.tsx testing group intersection logic per contracts/role-guard.md

### Implementation for User Story 6

- [x] T044 [US6] Extract cognito:groups from ID token in AuthContext (getGroups helper) and include in AuthUser.groups in frontend/src/contexts/AuthContext.tsx
- [x] T045 [US6] Create frontend/src/components/auth/RoleGuard.tsx implementing group-based route guard per contracts/role-guard.md
- [x] T046 [US6] Add example protected route in frontend/src/App.tsx wrapping a placeholder admin area with RoleGuard requiredGroups={["admin"]}

**Checkpoint**: RoleGuard mechanism works, admin-only areas blocked for non-admin users.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: CI updates, documentation, and final validation.

- [x] T047 [P] Update .github/workflows/ci.yml to ensure frontend job installs and tests auth service (npm ci + vitest) — satisfies FR-011 alongside T018
- [x] T048 [P] Update frontend/.env.example and add frontend/.env.local to .gitignore if not already present
- [x] T049 [P] Add lockout error message handling in frontend/src/components/auth/LoginForm.tsx for Cognito throttling/lockout responses
- [ ] T050 Validate quickstart.md flow end-to-end (create user, login, verify WebSocket token, sign out)
- [x] T051 Run full CI pipeline locally (type-check, unit tests, build, E2E) and verify green

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (Vite 6 + Amplify installed)
- **User Story 3 (Phase 3)**: Depends on Phase 1 only (Vite upgrade validation)
- **User Story 1 (Phase 4)**: Depends on Phase 2 (Amplify configured, types defined)
- **User Story 2 (Phase 5)**: Depends on Phase 4 (needs login working to test logout)
- **User Story 5 (Phase 6)**: Depends on Phase 4 (extends authService and LoginForm)
- **User Story 4 (Phase 7)**: Depends on Phase 4 (extends AuthContext state machine)
- **User Story 6 (Phase 8)**: Depends on Phase 4 (needs AuthContext with groups)
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

- **US3 (Vite Upgrade)**: Independent — can run after Phase 1
- **US1 (Login + WebSocket Auth)**: After Phase 2 — no other story dependencies
- **US2 (Sign Out)**: After US1 — extends AuthContext and websocketService
- **US5 (Federation)**: After US1 — extends authService and LoginForm
- **US4 (New Password)**: After US1 — extends AuthContext state machine
- **US6 (RBAC)**: After US1 — extends AuthContext (groups extraction)

### Within Each User Story

- Tests written first (should fail initially)
- Services before contexts
- Contexts before components
- Components before App.tsx integration

### Parallel Opportunities

- T007, T008, T009 (Terraform files) can run in parallel
- T019, T020 (US1 tests) can run in parallel
- T021 (authService) can run in parallel with tests
- T027, T032, T033, T038, T043 (tests for later stories) can run in parallel once US1 is done
- T047, T048, T049 (polish tasks) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch tests in parallel:
Task: "Create authService.test.ts in frontend/tests/unit/services/"
Task: "Create AuthContext.test.tsx in frontend/tests/unit/contexts/"

# Launch implementation (authService has no deps on other new files):
Task: "Create authService.ts in frontend/src/services/"

# Then sequentially:
Task: "Create AuthContext.tsx (depends on authService)"
Task: "Create LoginForm.tsx (depends on AuthContext)"
Task: "Update App.tsx (depends on AuthContext + LoginForm)"
Task: "Update websocketService.ts (depends on authService.getToken)"
```

---

## Implementation Strategy

### MVP First (User Stories 3 + 1)

1. Complete Phase 1: Setup (Vite 6 + Terraform)
2. Complete Phase 2: Foundational (Amplify + types)
3. Complete Phase 3: US3 — Verify Vite upgrade works
4. Complete Phase 4: US1 — Login + WebSocket auth
5. **STOP and VALIDATE**: Test login end-to-end with real Cognito
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Vite 6 working, infrastructure ready
2. US3 (Vite upgrade validation) → CI green
3. US1 (Login) → Core auth gate in place (MVP!)
4. US2 (Sign out) → Session management complete
5. US5 (Federation) → Enterprise SSO ready
6. US4 (New password) → Admin onboarding flow
7. US6 (RBAC) → Guard mechanism ready for future admin panel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
