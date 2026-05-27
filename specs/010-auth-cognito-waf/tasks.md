# Tasks: Cognito + WAF Authentication

**Input**: Design documents from `specs/010-auth-cognito-waf/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-middleware.md

**Tests**: Included (spec references pytest, Vitest, and Playwright).

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US4)
- Exact file paths included

## User Stories (from spec)

| ID | Title | Priority |
|----|-------|----------|
| US1 | Authenticated session start | P1 (MVP) |
| US2 | WebSocket JWT validation | P1 (MVP) |
| US3 | WAF rate limiting & protection | P2 |
| US4 | User registration & password management | P3 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, project structure, auth module scaffolding

- [ ] T001 Add `python-jose[cryptography]` and `httpx` to pyproject.toml dependencies
- [ ] T002 [P] Add `@aws-amplify/auth` and `aws-amplify` to frontend/package.json dependencies
- [ ] T003 [P] Create auth module directory structure: src/voice_server/auth/__init__.py
- [ ] T004 [P] Create Terraform auth module directory: terraform/modules/auth/

**Checkpoint**: Dependencies installable, directories exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core auth infrastructure that ALL stories depend on — Cognito user pool and JWKS fetcher

- [ ] T005 Implement Cognito Terraform module: user pool with email verification and password policy in terraform/modules/auth/cognito.tf
- [ ] T006 [P] Implement Cognito app client (no secret, SPA) and domain in terraform/modules/auth/cognito.tf
- [ ] T007 [P] Create Terraform auth module variables in terraform/modules/auth/variables.tf
- [ ] T008 [P] Create Terraform auth module outputs (user_pool_id, client_id, domain) in terraform/modules/auth/outputs.tf
- [ ] T009 Wire auth module into terraform/main.tf with appropriate variables
- [ ] T010 Implement JWKS key fetcher with 1-hour cache in src/voice_server/auth/jwks.py
- [ ] T011 Implement auth config dataclass (COGNITO_USER_POOL_ID, CLIENT_ID, REGION, LOCAL_MODE) in src/voice_server/auth/config.py
- [ ] T012 Add COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_REGION env vars to src/voice_server/config.py

**Checkpoint**: `terraform validate` passes with auth module. JWKS fetcher can retrieve keys from a Cognito endpoint.

---

## Phase 3: User Story 1 — Authenticated Session Start (Priority: P1) 🎯 MVP

**Goal**: Unauthenticated users see login form. After sign-in, they can create capture sessions. User identity attached to session.

**Independent Test**: Open frontend without auth → see login. Sign in → see Start Capture. Create session → user email in session participants.

### Tests for US1

- [ ] T013 [P] [US1] Unit test for JWT validation middleware (valid/expired/missing/malformed tokens) in tests/unit/test_auth_middleware.py
- [ ] T014 [P] [US1] Unit test for AuthContext (signIn/signOut state transitions) in frontend/src/contexts/AuthContext.test.tsx

### Implementation for US1

- [ ] T015 [US1] Implement `get_current_user` FastAPI dependency in src/voice_server/auth/middleware.py (validate Bearer token, extract JWTClaims, LOCAL_MODE bypass)
- [ ] T016 [US1] Wire auth middleware into REST endpoints: POST/GET/DELETE /sessions in src/voice_server/capture/endpoints.py
- [ ] T017 [US1] Update CaptureSession creation to include user email from JWT claims in src/voice_server/capture/endpoints.py
- [ ] T018 [P] [US1] Create Amplify configuration in frontend/src/config/amplify.ts (Cognito pool settings from APP_CONFIG)
- [ ] T019 [US1] Implement AuthContext in frontend/src/contexts/AuthContext.tsx (isAuthenticated, user, signIn, signOut, fetchSession)
- [ ] T020 [US1] Implement LoginForm in frontend/src/components/auth/LoginForm.tsx (email/password, error handling, loading state)
- [ ] T021 [US1] Implement ProtectedRoute in frontend/src/components/auth/ProtectedRoute.tsx (redirect to login if not authenticated)
- [ ] T022 [US1] Wire AuthContext into App.tsx: wrap content with ProtectedRoute, show LoginForm when unauthenticated
- [ ] T023 [US1] Update sessionService.ts to include Authorization header from AuthContext token in frontend/src/services/sessionService.ts
- [ ] T024 [US1] Add VITE_COGNITO_USER_POOL_ID, VITE_COGNITO_CLIENT_ID, VITE_COGNITO_REGION to frontend/.env.development and .env.example

**Checkpoint**: Full flow: open app → login form → sign in → Start Capture works → session has user email.

---

## Phase 4: User Story 2 — WebSocket JWT Validation (Priority: P1) 🎯 MVP

**Goal**: WebSocket endpoint rejects connections without valid JWT. Authenticated connections get user identity.

**Independent Test**: Connect WebSocket without token → close 4001. Connect with valid JWT → codec_ack received.

### Tests for US2

- [ ] T025 [P] [US2] Integration test: WebSocket connection rejected without token in tests/integration/test_ws_auth.py
- [ ] T026 [P] [US2] Integration test: WebSocket connection accepted with valid token in tests/integration/test_ws_auth.py

### Implementation for US2

- [ ] T027 [US2] Implement `validate_ws_token` helper in src/voice_server/auth/middleware.py (extract from query param, validate, return claims or close)
- [ ] T028 [US2] Update WebSocket handler to validate token before accept in src/voice_server/ws/handler.py
- [ ] T029 [US2] Pass user_id from JWT claims into session_ready message in src/voice_server/ws/handler.py
- [ ] T030 [US2] Update websocketService.ts to append `?token=<jwt>` to WebSocket URL in frontend/src/services/websocketService.ts
- [ ] T031 [US2] Handle WebSocket close code 4001/4003 in frontend: trigger token refresh, retry connection in frontend/src/services/websocketService.ts

**Checkpoint**: WebSocket connections require and validate JWT. Frontend includes token automatically.

---

## Phase 5: User Story 3 — WAF Rate Limiting & Protection (Priority: P2)

**Goal**: WAF protects ALB with rate limiting (100/min/IP) and request size limits (8KB body).

**Independent Test**: Send 200 rapid requests from one IP → WAF blocks. Normal traffic → passes.

### Implementation for US3

- [ ] T032 [P] [US3] Implement WAF WebACL with rate-limit rule (100/min/IP) in terraform/modules/auth/waf.tf
- [ ] T033 [P] [US3] Implement WAF size-constraint rule (8KB body limit) in terraform/modules/auth/waf.tf
- [ ] T034 [US3] Implement WAF association with ALB in terraform/modules/auth/waf.tf
- [ ] T035 [US3] Add WAF WebACL ARN to Terraform outputs in terraform/modules/auth/outputs.tf
- [ ] T036 [US3] Add WAF CloudWatch metrics to dashboard in terraform/modules/voice-service/cloudwatch.tf

**Checkpoint**: `terraform plan` shows WAF resources. WAF associated with ALB.

---

## Phase 6: User Story 4 — User Registration & Password Management (Priority: P3)

**Goal**: New users can self-register with email verification. Password reset via email.

**Independent Test**: Register new email → verify code → sign in works. Reset password → new password works.

### Tests for US4

- [ ] T037 [P] [US4] Component test for SignUpForm (form validation, submit flow) in frontend/src/components/auth/SignUpForm.test.tsx

### Implementation for US4

- [ ] T038 [US4] Implement SignUpForm in frontend/src/components/auth/SignUpForm.tsx (email, password, confirm password, verification code step)
- [ ] T039 [US4] Add signUp and confirmSignUp methods to AuthContext in frontend/src/contexts/AuthContext.tsx
- [ ] T040 [US4] Add resetPassword and confirmResetPassword methods to AuthContext in frontend/src/contexts/AuthContext.tsx
- [ ] T041 [US4] Add "Sign Up" and "Forgot Password" links to LoginForm in frontend/src/components/auth/LoginForm.tsx
- [ ] T042 [US4] Implement password reset flow UI (enter email → enter code + new password) in frontend/src/components/auth/LoginForm.tsx

**Checkpoint**: Full registration + password reset flows work end-to-end.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: E2E testing, security hardening, documentation

- [ ] T043 [P] Write E2E test: unauthenticated user sees login, signs in, starts session in frontend/tests/e2e/auth-flow.spec.ts
- [ ] T044 [P] Add startup warning log when LOCAL_MODE=true in src/voice_server/main.py
- [ ] T045 Verify ECS task definition does NOT set LOCAL_MODE in terraform/modules/voice-service/ecs.tf
- [ ] T046 [P] Update frontend public/config.js with COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID placeholders
- [ ] T047 Update CI workflow to set LOCAL_MODE=true for backend tests in .github/workflows/ci.yml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 (needs JWKS fetcher + Cognito pool)
- **Phase 4 (US2)**: Depends on US1 (needs middleware + frontend token)
- **Phase 5 (US3)**: Depends on Phase 2 only (Terraform, independent of backend/frontend auth)
- **Phase 6 (US4)**: Depends on US1 (extends AuthContext and LoginForm)
- **Phase 7 (Polish)**: Depends on US1 + US2 complete

### User Story Dependencies

- **US1 (Auth Session)**: Foundational only — MUST be first
- **US2 (WebSocket JWT)**: Depends on US1 (needs middleware + token in frontend)
- **US3 (WAF)**: Foundational only — can parallel with US1/US2
- **US4 (Registration)**: Depends on US1 (extends auth context)

### Within Each User Story

- Tests written first (must FAIL before implementation)
- Infrastructure (Terraform) before backend
- Backend middleware before frontend integration
- Frontend services before UI components

### Parallel Opportunities

Within Phase 2: T005-T008 (Terraform files) in parallel, T010-T012 (backend config) in parallel.

US3 (WAF) can run entirely in parallel with US1/US2 since it's Terraform-only.

Within US1: T018 (Amplify config) parallel with T015-T017 (backend middleware).

---

## Parallel Example: User Story 1

```bash
# Parallel batch 1 (backend + frontend independent):
Task T015: "Implement get_current_user dependency in src/voice_server/auth/middleware.py"
Task T018: "Create Amplify configuration in frontend/src/config/amplify.ts"

# Parallel batch 2 (tests):
Task T013: "Unit test for JWT validation middleware"
Task T014: "Unit test for AuthContext"
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Phase 1: Setup → dependencies installed
2. Phase 2: Foundational → Cognito pool exists, JWKS fetcher works
3. Phase 3: US1 → login works, REST endpoints secured
4. Phase 4: US2 → WebSocket secured with JWT
5. **STOP**: MVP delivered — all endpoints require authentication

### Incremental Delivery

6. Phase 5: US3 → WAF protection layer added
7. Phase 6: US4 → Self-service registration + password reset
8. Phase 7: Polish → E2E tests, security hardening

### Parallel Team Strategy

- Developer A: US1 + US2 (backend + frontend auth)
- Developer B: US3 (WAF Terraform — fully independent)
- Both converge at Phase 7 for E2E testing

---

## Notes

- Total tasks: 47
- MVP tasks (US1 + US2): 28
- Parallel opportunities: 8 batches identified
- Each user story independently testable at its checkpoint
- LOCAL_MODE=true bypasses all auth — essential for local dev and existing tests
- Existing backend tests continue to pass because LOCAL_MODE is set in test env
