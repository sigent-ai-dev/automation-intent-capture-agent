# Tasks: WebSocket Audio Server

**Input**: Design documents from `specs/001-websocket-audio-server/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/websocket-api.md

**Tests**: Included — spec explicitly requires unit tests for connection handling and session management.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and tooling

- [ ] T001 Create project directory structure per plan.md layout (src/voice_server/, tests/unit/, tests/integration/)
- [ ] T002 Initialize Python project with pyproject.toml — FastAPI, uvicorn, structlog, aws-embedded-metrics, aws-xray-sdk, pytest, pytest-asyncio, httpx, websockets
- [ ] T003 [P] Configure structlog with JSON output in src/voice_server/observability/logging.py
- [ ] T004 [P] Create environment configuration module in src/voice_server/config.py (PORT, LOG_LEVEL, STALE_SESSION_TIMEOUT_SECONDS, SHUTDOWN_DRAIN_SECONDS, LOCAL_MODE)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement AudioCodec value object in src/voice_server/models/codec.py and SessionState enum in src/voice_server/models/session.py
- [ ] T006 [P] Implement Session dataclass with lifecycle state in src/voice_server/models/session.py
- [ ] T007 Implement SessionRegistry (Dict-based CRUD, lookup by id/user_id, enforce single active session per user_id — close existing session if new connection from same user) in src/voice_server/sessions/registry.py
- [ ] T008 [P] Implement control message protocol (parse/serialize JSON text frames) in src/voice_server/ws/protocol.py
- [ ] T009 [P] Implement ALB auth header extraction (x-amzn-oidc-identity, LOCAL_MODE bypass) in src/voice_server/ws/auth.py
- [ ] T010 Create FastAPI app skeleton with lifespan handler in src/voice_server/main.py
- [ ] T011 [P] Create shared test fixtures (mock sessions, test client, WebSocket test helper) in tests/conftest.py

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Establish Audio Connection (Priority: P1) MVP

**Goal**: Browser client connects via WebSocket, negotiates PCM codec, and streams audio bidirectionally using binary frames for audio and JSON text frames for control.

**Independent Test**: Connect a WebSocket client, send codec_negotiate, receive codec_ack, send binary audio frames, receive binary audio frames back.

### Tests for User Story 1

- [ ] T012 [P] [US1] Unit test for codec negotiation (accept PCM, reject unsupported) in tests/unit/test_codec.py
- [ ] T013 [P] [US1] Unit test for control message protocol parsing/serialization in tests/unit/test_protocol.py
- [ ] T014 [P] [US1] Integration test for full WebSocket connection flow (upgrade → negotiate → stream → close) in tests/integration/test_websocket.py

### Implementation for User Story 1

- [ ] T015 [US1] Implement WebSocket endpoint handler at /ws/audio in src/voice_server/ws/handler.py — accept connection, route text/binary frames
- [ ] T016 [US1] Implement codec negotiation logic in handler — validate codec_negotiate message, respond with codec_ack or codec_reject, transition session to STREAMING. Enforce 5-second negotiation timeout (close with CODEC_TIMEOUT error if no codec_negotiate received after upgrade)
- [ ] T017 [US1] Implement binary frame forwarding — receive client audio binary frames, update last_activity; send server audio binary frames back to client
- [ ] T018 [US1] Wire WebSocket endpoint into FastAPI app in src/voice_server/main.py

**Checkpoint**: A client can connect, negotiate codec, and exchange binary audio frames

---

## Phase 4: User Story 2 — Session Lifecycle Management (Priority: P1)

**Goal**: Server tracks sessions, detects stale connections (30s timeout), performs cleanup on disconnect, handles concurrent sessions independently.

**Independent Test**: Connect multiple clients, disconnect one (graceful and forced), verify cleanup occurs and other sessions continue unaffected. Wait 30s idle and verify timeout triggers cleanup.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for session registry (create, get, remove, list) in tests/unit/test_registry.py
- [ ] T020 [P] [US2] Unit test for stale session cleanup (30s timeout detection) in tests/unit/test_cleanup.py
- [ ] T021 [P] [US2] Integration test for session timeout and concurrent session isolation in tests/integration/test_websocket.py

### Implementation for User Story 2

- [ ] T022 [US2] Implement background stale-session cleanup task (10s scan interval, 30s timeout) in src/voice_server/sessions/cleanup.py
- [ ] T023 [US2] Integrate session creation/removal into WebSocket handler — create session on connect, remove on disconnect, update last_activity on every frame in src/voice_server/ws/handler.py
- [ ] T024 [US2] Implement graceful disconnect handling — send close frame, transition STREAMING → DISCONNECTING → CLOSED, release resources in src/voice_server/ws/handler.py
- [ ] T025 [US2] Start cleanup task in lifespan startup, cancel on shutdown in src/voice_server/main.py

**Checkpoint**: Sessions are tracked, stale connections are cleaned up, concurrent sessions are isolated

---

## Phase 5: User Story 3 — Health Check for Load Balancer (Priority: P2)

**Goal**: Expose /health/live (liveness, always 200) and /health/ready (readiness, capacity-aware) endpoints for ALB target group health checks.

**Independent Test**: Hit /health/live (expect 200), hit /health/ready (expect 200 with session count), trigger shutdown drain and verify /health/ready returns 503.

### Tests for User Story 3

- [ ] T026 [P] [US3] Integration test for health endpoints (live, ready, ready-during-drain) in tests/integration/test_health.py

### Implementation for User Story 3

- [ ] T027 [US3] Implement /health/live and /health/ready endpoints in src/voice_server/health/endpoints.py — readiness checks accepting_new flag and reports active session count
- [ ] T028 [US3] Register health router in FastAPI app in src/voice_server/main.py

**Checkpoint**: ALB can determine server liveness and readiness

---

## Phase 6: User Story 4 — Local Development Experience (Priority: P2)

**Goal**: Developer starts server with single uvicorn command, auto-reload works, auth is bypassed in local mode.

**Independent Test**: Run `uvicorn src.voice_server.main:app --reload`, connect WebSocket client without auth headers, verify audio flows.

### Implementation for User Story 4

- [ ] T029 [US4] Ensure LOCAL_MODE=true bypasses ALB header validation in src/voice_server/ws/auth.py (already scaffolded in T009, verify integration)
- [ ] T030 [US4] Add `if __name__ == "__main__"` uvicorn runner in src/voice_server/main.py with configurable host/port
- [ ] T031 [US4] Verify auto-reload works with uvicorn --reload flag (manual validation, document in quickstart)

**Checkpoint**: Developer can run and iterate locally with zero infrastructure

---

## Phase 7: User Story 5 — Container Deployment (Priority: P3)

**Goal**: Dockerfile produces a runnable container image for ECS Fargate deployment.

**Independent Test**: Build image, run container, connect WebSocket client, verify audio streaming works identically to local mode.

### Implementation for User Story 5

- [ ] T032 [US5] Create Dockerfile — Python 3.11 slim base, copy src, install deps, expose port 8080, CMD uvicorn
- [ ] T033 [US5] Add .dockerignore (tests/, specs/, .specify/, .git/, __pycache__/)

**Checkpoint**: Container image builds and runs the voice server correctly

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Observability, graceful shutdown, auth integration, final hardening

- [ ] T034 [P] Implement CloudWatch embedded metrics helper (active_sessions, connection_duration, error_count) in src/voice_server/observability/metrics.py
- [ ] T035 [P] Configure X-Ray SDK tracing in src/voice_server/main.py (patch asyncio, add middleware)
- [ ] T036 Implement graceful shutdown — SIGTERM handler, set accepting_new=False, send server_shutdown control message to all clients, 30s drain, force close in src/voice_server/main.py
- [ ] T037 [P] Integration test for graceful shutdown behaviour in tests/integration/test_shutdown.py
- [ ] T038 [P] Unit test for ALB auth header extraction and LOCAL_MODE bypass in tests/unit/test_auth.py
- [ ] T041 [P] Integration test verifying unauthenticated WebSocket connections are rejected when LOCAL_MODE=false in tests/integration/test_websocket.py
- [ ] T039 Wire metrics emission into session lifecycle events (connect, disconnect, timeout, error) in src/voice_server/ws/handler.py
- [ ] T040 Run quickstart.md validation — verify all commands work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational + US1 (handler exists)
- **User Story 3 (Phase 5)**: Depends on Foundational only (independent of US1/US2)
- **User Story 4 (Phase 6)**: Depends on US1 (need working server to test)
- **User Story 5 (Phase 7)**: Depends on US1 (need working server to containerise)
- **Polish (Phase 8)**: Depends on US1 + US2 (session lifecycle must exist for observability/shutdown)

### User Story Dependencies

- **US1** (Audio Connection): Independent — core WebSocket flow
- **US2** (Session Lifecycle): Builds on US1's handler (needs existing connection flow)
- **US3** (Health Check): Independent — only reads server state
- **US4** (Local Dev): Independent — config/auth bypass only
- **US5** (Container): Independent — packaging only

### Within Each User Story

- Tests written FIRST, verify they FAIL
- Models/value objects before services
- Services before endpoint integration
- Wire into main app last

### Parallel Opportunities

- T003, T004 can run in parallel (Setup)
- T005, T006, T008, T009, T011 can run in parallel (Foundational)
- T012, T013, T014 can run in parallel (US1 tests)
- T019, T020, T021 can run in parallel (US2 tests)
- US3, US4, US5 can all proceed in parallel after US1 completes
- T034, T035, T037, T038 can run in parallel (Polish)

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests in parallel:
Task: "Unit test for codec negotiation in tests/unit/test_codec.py"
Task: "Unit test for control message protocol in tests/unit/test_protocol.py"
Task: "Integration test for WebSocket flow in tests/integration/test_websocket.py"

# Then implementation sequentially:
Task: "WebSocket endpoint handler in src/voice_server/ws/handler.py"
Task: "Codec negotiation logic in handler"
Task: "Binary frame forwarding"
Task: "Wire into FastAPI app"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Connect WebSocket client, negotiate codec, exchange audio
5. Deploy/demo if ready — this alone proves the architecture works

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Audio Connection) → Test → **MVP!**
3. Add US2 (Session Lifecycle) → Test → Production-grade connection management
4. Add US3 (Health Check) → Test → ALB integration ready
5. Add US4 + US5 (Local Dev + Container) → Test → Deployment-ready
6. Add Polish → Observability, shutdown, auth hardening

### Suggested MVP Scope

**US1 only** — proves WebSocket audio streaming works end-to-end. Takes ~60% less effort than full scope and validates the core architectural choice (direct WebSocket + binary frames).

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 41
