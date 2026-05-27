# Tasks: DynamoDB Session State Persistence

**Input**: Design documents from `specs/004-dynamo-session-state/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/dynamo-table-schema.md

**Tests**: Included — spec requires persistence reliability testing.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add dependencies, create package structure, add configuration

- [ ] T001 Add aiobotocore and moto[dynamodb] dependencies to pyproject.toml and run uv lock
- [ ] T002 Create package structure: src/voice_server/persistence/__init__.py
- [ ] T003 [P] Add DynamoDB config variables to src/voice_server/config.py (DYNAMO_TABLE_NAME, DYNAMO_ENDPOINT_URL, SESSION_TTL_SECONDS)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DynamoDB client, serializers, and base adapter protocol — ALL user stories depend on these

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement DynamoDB client singleton (create_client, get_table, ensure_table_exists for local dev) in src/voice_server/persistence/client.py
- [ ] T005 [P] Implement serializers (session→item, item→session, history→item, item→history, elicitation→item, item→elicitation) in src/voice_server/persistence/serializers.py
- [ ] T006 Define PersistenceAdapter protocol (save, load, delete, drain_all) in src/voice_server/persistence/__init__.py

**Checkpoint**: Foundation ready — client connects, serializers round-trip, protocol defined

---

## Phase 3: User Story 1 — Session Survives Deployment (Priority: P1) MVP

**Goal**: Active sessions persist during graceful shutdown and resume on reconnection.

**Independent Test**: Start session, simulate SIGTERM, restart, reconnect — verify session state restored.

### Tests for User Story 1

- [ ] T007 [P] [US1] Unit test for serializers (round-trip all 3 record types, edge cases) in tests/unit/test_serializers.py
- [ ] T008 [P] [US1] Unit test for session adapter (save, load, delete, TTL refresh) in tests/unit/test_session_adapter.py
- [ ] T009 [P] [US1] Integration test for full persist/load cycle with moto in tests/integration/test_dynamo_persistence.py

### Implementation for User Story 1

- [ ] T010 [US1] Implement SessionPersistenceAdapter (save session on create/state-change, load on reconnect, delete on close) in src/voice_server/persistence/session_adapter.py
- [ ] T011 [US1] Modify SessionRegistry to accept optional persistence adapter — call adapter.save() on create/remove, adapter.load() for resume in src/voice_server/sessions/registry.py
- [ ] T012 [US1] Implement drain_all() — batch_write_item for all active sessions with retry loop in src/voice_server/persistence/session_adapter.py
- [ ] T013 [US1] Wire drain_all() into graceful shutdown handler (SIGTERM) — persist all sessions before exit in src/voice_server/main.py
- [ ] T014 [US1] Wire persistence adapter into application startup — create adapter, pass to SessionRegistry in src/voice_server/main.py

**Checkpoint**: Sessions survive container restarts via graceful drain + resume

---

## Phase 4: User Story 2 — Durable Conversation History (Priority: P1)

**Goal**: Conversation history persists across reconnections and crashes.

**Independent Test**: Build 15+ turn history, crash process, restart, verify history intact.

### Tests for User Story 2

- [ ] T015 [P] [US2] Unit test for history adapter (save after turn, load on resume, TTL refresh) in tests/unit/test_history_adapter.py

### Implementation for User Story 2

- [ ] T016 [US2] Implement HistoryPersistenceAdapter (save after each add_turn, load on session resume) in src/voice_server/persistence/history_adapter.py
- [ ] T017 [US2] Modify ConversationHistory to accept optional persistence adapter — call adapter.save() on add_turn in src/voice_server/bidi/history.py
- [ ] T018 [US2] Wire history adapter into AudioBridge — create adapter, pass to ConversationHistory on session start in src/voice_server/bidi/agent.py
- [ ] T019 [US2] Load history from DynamoDB on session resume (when draft session detected) in src/voice_server/bidi/agent.py

**Checkpoint**: Conversation history survives crashes — at most 1 turn lost

---

## Phase 5: User Story 3 — Recoverable Elicitation Progress (Priority: P2)

**Goal**: In-progress intent capture state persists across disconnections.

**Independent Test**: Start intent capture, populate 2 fields, disconnect, reconnect — verify system knows which fields are done.

### Tests for User Story 3

- [ ] T020 [P] [US3] Unit test for elicitation adapter (save after tool invocation, load on resume) in tests/unit/test_elicitation_adapter.py

### Implementation for User Story 3

- [ ] T021 [US3] Implement ElicitationPersistenceAdapter (save after each tool invocation, load on session resume) in src/voice_server/persistence/elicitation_adapter.py
- [ ] T022 [US3] Wire elicitation adapter into tool functions — call adapter.save() after each create/update/finalise in src/voice_server/elicitation/tools.py
- [ ] T023 [US3] Load elicitation state on session resume — pass to system prompt as resume context in src/voice_server/bidi/agent.py

**Checkpoint**: Elicitation progress survives across sessions

---

## Phase 6: User Story 4 — Automatic Session Cleanup (Priority: P2)

**Goal**: Stale sessions expire automatically via DynamoDB TTL.

**Independent Test**: Create session, advance TTL past expiry, verify record gone and load returns None.

### Implementation for User Story 4

- [ ] T024 [US4] Implement TTL refresh on every interaction — update expires_at on session touch in src/voice_server/persistence/session_adapter.py
- [ ] T025 [US4] Add expiry check on load — if expires_at < now, treat as not found even if DynamoDB hasn't deleted yet in src/voice_server/persistence/session_adapter.py
- [ ] T026 [US4] Add TTL refresh to history and elicitation adapters (same expires_at as parent session) in src/voice_server/persistence/history_adapter.py and elicitation_adapter.py

**Checkpoint**: Stale sessions auto-expire, no operator intervention needed

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Observability, error handling, Terraform

- [ ] T027 [P] Add structured logging for persistence operations (save, load, drain, TTL refresh, errors) in src/voice_server/persistence/client.py
- [ ] T028 [P] Add metrics for persistence (writes/reads count, latency, failures, drain success/failure) in src/voice_server/observability/metrics.py
- [ ] T029 [P] Add DynamoDB table Terraform resource to infra/dynamodb.tf (matching contracts/dynamo-table-schema.md)
- [ ] T030 [P] Add graceful degradation — if DynamoDB unreachable, log and continue in-memory only in src/voice_server/persistence/client.py
- [ ] T031 Run quickstart.md validation — verify persist/load cycle works end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — session persistence
- **User Story 2 (Phase 4)**: Depends on US1 (reuses client + serializers, builds on session adapter)
- **User Story 3 (Phase 5)**: Depends on US1 (same pattern, different entity)
- **User Story 4 (Phase 6)**: Depends on US1 + US2 + US3 (TTL applies to all record types)
- **Polish (Phase 7)**: Depends on US1 + US2 + US3

### User Story Dependencies

- **US1** (Session Survival): Independent after Foundational — core MVP
- **US2** (Durable History): Depends on US1 (reuses client, serializers, pattern)
- **US3** (Elicitation State): Depends on US1 (same adapter pattern)
- **US4** (TTL Cleanup): Depends on US1+US2+US3 (TTL on all adapters)

### Within Each User Story

- Tests written FIRST, verify they FAIL
- Adapter implementation before module integration
- Module integration before application wiring

### Parallel Opportunities

- T004, T005, T006 can run in parallel (Foundational — different files)
- T007, T008, T009 can run in parallel (US1 tests)
- T015, T020 can run in parallel (US2/US3 tests — different files)
- T027, T028, T029, T030 can run in parallel (Polish)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Simulate deploy, verify session survives
5. This alone proves DynamoDB integration works end-to-end

### Incremental Delivery

1. Setup + Foundational → Client and serializers ready
2. Add US1 (Session Survival) → Test → **MVP!** Sessions survive deploys
3. Add US2 (Durable History) → Test → Conversations survive crashes
4. Add US3 (Elicitation State) → Test → Multi-session intent capture works
5. Add US4 (TTL Cleanup) → Test → Zero-maintenance expiry
6. Add Polish → Production observability + Terraform

### Suggested MVP Scope

**US1 only** — proves the full persistence pattern: write-through adapter, graceful drain, session resume. History and elicitation adapters follow the exact same pattern once US1 validates the architecture.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- All tests use moto mock — no real DynamoDB needed for unit/integration tests
- Total tasks: 31
