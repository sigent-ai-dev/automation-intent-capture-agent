# Tasks: Deploy Voice Service Infrastructure

**Input**: Design documents from `specs/011-deploy-voice-infra/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — smoke tests are a core requirement (FR-011 to FR-013) and unit tests for the auth handler.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Provision VPC networking and container registry — foundational AWS resources that all stories depend on.

- [x] T001 Create terraform/modules/networking/main.tf with VPC (10.0.0.0/16), 2 public subnets, 2 private subnets, IGW, NAT Gateway
- [x] T002 [P] Create terraform/modules/networking/variables.tf with project_name, environment, vpc_cidr inputs
- [x] T003 [P] Create terraform/modules/networking/outputs.tf exposing vpc_id, public_subnet_ids, private_subnet_ids
- [x] T004 Create terraform/environments/dev.tfvars with dev-specific values (region, project name, single NAT, no autoscaling)
- [x] T005 Update terraform/main.tf to add networking module and wire its outputs to voice-service module (replacing hard-coded VPC vars)
- [x] T006 Update terraform/variables.tf to remove vpc_id, public_subnet_ids, private_subnet_ids (now from networking module)
- [x] T007 Generate self-signed certificate and document import command in terraform/environments/README.md

**Checkpoint**: `terraform plan` succeeds with networking + existing modules wired together.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: GitHub OIDC role and deploy workflow updates — required before any deployment can happen.

**CRITICAL**: No deployment can proceed until this phase is complete.

- [x] T008 Create terraform/modules/cicd/main.tf with IAM OIDC provider for GitHub Actions and deploy role (scoped to repo sigent-ai-dev/automation-intent-capture-agent)
- [x] T009 [P] Create terraform/modules/cicd/variables.tf with github_org, github_repo, environment inputs
- [x] T010 [P] Create terraform/modules/cicd/outputs.tf exposing deploy_role_arn
- [x] T011 Wire cicd module into terraform/main.tf
- [x] T012 Update .github/workflows/deploy.yml to use OIDC auth (replace hardcoded role reference with repository secret pattern)

**Checkpoint**: `terraform plan` shows OIDC provider + role creation. Deploy workflow references the role correctly.

---

## Phase 3: User Story 1 - Frontend Connects to Deployed Backend (Priority: P1) MVP

**Goal**: Backend deployed and reachable from frontend with valid Cognito auth over WebSocket.

**Independent Test**: Open frontend, log in, start capture — WebSocket connects to ALB endpoint.

### Implementation for User Story 1

- [ ] T013 [US1] Run `terraform apply` in builder-admin account to provision VPC, ECR, ECS, ALB, DynamoDB (depends on T007 — cert ARN needed for ALB HTTPS listener)
- [ ] T014 [US1] Build Docker image and push to ECR (first manual push to bootstrap ECS service)
- [ ] T015 [US1] Verify ECS service reaches RUNNING state and ALB health checks pass (`GET /health/live` returns 200)
- [ ] T016 [US1] Update frontend/.env.local with deployed ALB URL (VITE_WEBSOCKET_URL and VITE_API_URL)
- [ ] T017 [US1] Test frontend-to-backend WebSocket connection with Cognito auth token end-to-end

**Checkpoint**: Frontend connects to deployed backend, auth succeeds, codec negotiation works.

---

## Phase 4: User Story 3 - Backend Validates WebSocket Auth Token (Priority: P1)

**Goal**: Backend extracts and validates Cognito JWT from Sec-WebSocket-Protocol header per contracts/websocket-protocol-auth.md.

**Independent Test**: WebSocket upgrade with valid token succeeds; invalid/missing token returns close code 4001.

### Tests for User Story 3

- [x] T018 [P] [US3] Create tests/unit/test_ws_protocol_auth.py testing token extraction from Sec-WebSocket-Protocol header (valid, invalid, missing)

### Implementation for User Story 3

- [x] T019 [US3] Update src/voice_server/ws/auth.py to parse Sec-WebSocket-Protocol header: split by comma, extract second value as JWT token
- [x] T020 [US3] Update src/voice_server/ws/auth.py to validate JWT using existing auth/middleware.py validate_token() function
- [x] T021 [US3] Update src/voice_server/ws/handler.py to call websocket.accept(subprotocol='v1.audio.intent') on successful auth
- [x] T022 [US3] Update src/voice_server/ws/handler.py to close with code=4001 when auth fails
- [x] T023 [US3] Add COGNITO_USER_POOL_ID and COGNITO_REGION environment variables to ECS task definition in terraform/modules/voice-service/ecs.tf
- [x] T024 [US3] Update src/voice_server/auth/config.py to read pool ID and region from environment for JWKS URL construction

**Checkpoint**: Unit tests pass. WebSocket connections with valid tokens are accepted; invalid tokens get 4001.

---

## Phase 5: User Story 2 - Developer Deploys New Version (Priority: P2)

**Goal**: CI/CD pipeline builds, pushes, and deploys on workflow trigger with automatic rollback on failure.

**Independent Test**: Trigger deploy workflow, verify new image is running within 5 minutes.

### Implementation for User Story 2

- [ ] T025 [US2] Add GitHub repository secret AWS_DEPLOY_ROLE_ARN with the OIDC role ARN from terraform output
- [x] T026 [US2] Update .github/workflows/deploy.yml to add `--force-new-deployment` and wait for service stability
- [x] T027 [US2] Add deployment_circuit_breaker with rollback enabled in terraform/modules/voice-service/ecs.tf
- [ ] T028 [US2] Trigger deploy workflow manually and verify new container version is serving traffic
- [ ] T029 [US2] Verify rollback by deploying a deliberately broken image and confirming previous version stays active

**Checkpoint**: Deploy workflow completes end-to-end. Rollback works on failed health checks.

---

## Phase 6: User Story 4 - Smoke Tests Verify Deployment (Priority: P2)

**Goal**: Automated post-deploy smoke tests verify health, auth, and codec negotiation per contracts/smoke-tests.md.

**Independent Test**: Run smoke-test.sh against deployed service — all 5 checks pass.

### Implementation for User Story 4

- [x] T030 [P] [US4] Create .github/scripts/smoke-test.sh with ST-01 (health/live) and ST-02 (health/ready) curl checks
- [x] T031 [US4] Add ST-03 (WebSocket auth accept) to smoke-test.sh using Python websockets library with valid test token
- [x] T032 [US4] Add ST-04 (WebSocket auth reject) to smoke-test.sh — connect without token, verify close code 4001
- [x] T033 [US4] Add ST-05 (codec negotiation) to smoke-test.sh — send codec_negotiate, verify codec_ack + session_ready
- [x] T034 [US4] Add smoke test step to .github/workflows/deploy.yml after ECS service stabilization
- [x] T035 [US4] Add mechanism to generate a valid test token in CI (admin-initiate-auth with test user or GitHub secret)

**Checkpoint**: Smoke tests pass against deployed service. Deploy workflow fails if smoke tests fail.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation.

- [ ] T036 [P] Update README.md with deployment section (link to quickstart.md)
- [ ] T037 [P] Add terraform/environments/README.md documenting self-signed cert generation and import
- [ ] T038 Remove hard-coded VPC variables from terraform/terraform.tfvars.example (now auto-provisioned)
- [ ] T039 Run full smoke test suite against live deployment and verify all 5 tests pass
- [ ] T040 Update frontend/.env.example with placeholder for deployed ALB URL

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (networking module must exist for plan)
- **User Story 1 (Phase 3)**: Depends on Phase 1 + 2 (infrastructure must be provisioned)
- **User Story 3 (Phase 4)**: Can start in parallel with Phase 3 (code change, not infra-dependent)
- **User Story 2 (Phase 5)**: Depends on Phase 2 (OIDC role) + Phase 3 (running service)
- **User Story 4 (Phase 6)**: Depends on Phase 4 (auth must work for smoke tests) + Phase 3 (service deployed)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (Frontend → Backend)**: After infra provisioned — no code changes needed (backend already works in non-local mode)
- **US3 (WebSocket Auth)**: Independent code change — can develop/test locally, deploy after US1
- **US2 (CI/CD Deploy)**: After US1 (needs running service to test workflow)
- **US4 (Smoke Tests)**: After US3 (tests validate auth) + US1 (tests run against deployed service)

### Within Each User Story

- Terraform before manual provisioning steps
- Code changes before deployment
- Unit tests alongside implementation
- Integration/manual verification last

### Parallel Opportunities

- T002, T003 (networking module files) in parallel
- T008, T009, T010 (cicd module files) in parallel
- T018 (auth unit test) can run in parallel with T019-T024 (implementation)
- T030 (health smoke tests) can start independently
- T036, T037 (docs) in parallel

---

## Parallel Example: User Story 3 (WebSocket Auth)

```bash
# Tests and implementation can proceed in parallel:
Task: "Create test_ws_protocol_auth.py in tests/unit/"
Task: "Update ws/auth.py to parse Sec-WebSocket-Protocol"

# Then sequentially:
Task: "Update ws/handler.py (depends on auth.py changes)"
Task: "Add env vars to ECS task definition (depends on config.py changes)"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 3)

1. Complete Phase 1: Setup (VPC + networking)
2. Complete Phase 2: Foundational (OIDC role)
3. Complete Phase 3: US1 — Provision and deploy
4. Complete Phase 4: US3 — Fix WebSocket auth
5. **STOP and VALIDATE**: Frontend connects to deployed backend with auth
6. Deploy auth fix, test end-to-end

### Incremental Delivery

1. Terraform infrastructure → VPC, ECS, ALB running
2. First deploy → Service reachable (MVP!)
3. WebSocket auth → Tokens validated properly
4. CI/CD pipeline → Automated deploys
5. Smoke tests → Automated verification on every deploy

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T013/T014/T015 are interactive (require AWS access and manual verification)
- T025 requires GitHub admin access to set repository secrets
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
