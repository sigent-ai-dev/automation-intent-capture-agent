# Tasks: BidiAgent Nova Sonic Integration

**Input**: Design documents from `specs/002-bidi-nova-sonic/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/bidi-bridge-protocol.md

**Tests**: Included — spec explicitly requires integration test for voice flow.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add strands-agents dependency, create package structure for bidi and audio modules

- [x] T001 Add strands-agents dependency to pyproject.toml and run uv lock
- [x] T002 Create package structure: src/voice_server/bidi/__init__.py, src/voice_server/audio/__init__.py
- [x] T003 [P] Add new environment variables to src/voice_server/config.py (NOVA_SONIC_MODEL_ID, RECONNECT_BEFORE_SECONDS, HISTORY_WINDOW_SIZE, BARGE_IN_ENERGY_THRESHOLD, MAX_VOICE_RETRIES)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and utilities that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Implement VoiceConnection dataclass and VoiceConnectionState enum in src/voice_server/bidi/connection.py
- [x] T005 [P] Implement Turn dataclass and ConversationHistory class (add_turn, get_recent, get_summary_and_recent) in src/voice_server/bidi/history.py
- [x] T006 [P] Implement audio downsampling (24kHz → 16kHz PCM) in src/voice_server/audio/resample.py
- [x] T007 [P] Implement WebSocketBidiInput protocol (asyncio.Queue consumer, yields audio chunks) in src/voice_server/bidi/input.py
- [x] T008 [P] Implement WebSocketBidiOutput protocol (receives agent events, routes audio/text/signals) in src/voice_server/bidi/output.py
- [x] T009 Implement BidiAgent factory and AudioBridge skeleton (create agent with model + config, AudioBridge class that owns BidiInput/BidiOutput/agent lifecycle) in src/voice_server/bidi/agent.py

**Checkpoint**: Foundation ready — all bridge components exist independently

---

## Phase 3: User Story 1 — Full Voice Conversation (Priority: P1) MVP

**Goal**: User speaks via WebSocket, audio flows through Nova Sonic (STT → LLM → TTS), synthesised response streams back to user.

**Independent Test**: Send pre-recorded audio via WebSocket, receive synthesised audio back.

### Tests for User Story 1

- [x] T010 [P] [US1] Unit test for WebSocketBidiInput (queue push/yield, empty queue blocks, close stops iteration) in tests/unit/test_bidi_input.py
- [x] T011 [P] [US1] Unit test for WebSocketBidiOutput (audio downsample+send, text→history, error→notify) in tests/unit/test_bidi_output.py
- [x] T012 [P] [US1] Unit test for audio resample (24kHz→16kHz correctness, empty input, odd-length input) in tests/unit/test_resample.py
- [x] T013 [P] [US1] Integration test for full voice flow (connect→negotiate→send audio→receive response→disconnect) in tests/integration/test_bidi_agent.py

### Implementation for User Story 1

- [x] T014 [US1] Wire BidiInput queue into WebSocket handler — binary frames push to input queue instead of no-op in src/voice_server/ws/handler.py
- [x] T015 [US1] Wire BidiOutput to WebSocket — agent audio (downsampled) sent as binary frames, text events logged, agent_speaking/agent_done control messages sent in src/voice_server/bidi/output.py
- [x] T016 [US1] Create AudioBridge class that owns BidiInput, BidiOutput, BidiAgent lifecycle for a session in src/voice_server/bidi/agent.py
- [x] T017 [US1] Integrate AudioBridge into session lifecycle — create on session start, destroy on session close in src/voice_server/ws/handler.py
- [x] T018 [US1] Start BidiAgent.run() as asyncio task when session enters STREAMING state in src/voice_server/bidi/agent.py

**Checkpoint**: A user can speak and hear the agent respond through the WebSocket

---

## Phase 4: User Story 2 — Barge-In (Priority: P1)

**Goal**: User interrupts agent mid-speech, agent audio stops within 800ms, user's new input is processed.

**Independent Test**: Trigger long agent response, send user audio mid-response, verify agent audio stops and new response arrives.

### Tests for User Story 2

- [x] T019 [P] [US2] Unit test for barge-in detector (energy threshold, debounce, reset) in tests/unit/test_barge_in.py

### Implementation for User Story 2

- [x] T020 [US2] Implement barge-in energy detector — monitor incoming audio energy while is_agent_speaking is True in src/voice_server/bidi/barge_in.py
- [x] T021 [US2] Wire barge-in into BidiOutput — when barge-in detected, flush pending agent audio buffer, set barge_in_detected flag, send barge_in_ack control message in src/voice_server/bidi/output.py
- [x] T022 [US2] Wire barge-in into WebSocket handler — stop sending agent binary frames on barge_in_detected until new agent response begins in src/voice_server/ws/handler.py

**Checkpoint**: User can interrupt the agent and hear a fresh response

---

## Phase 5: User Story 3 — Connection Resilience / 8-Minute Reconnect (Priority: P1)

**Goal**: Proactive hot-swap at 7 minutes — new connection established in parallel, history replayed, zero audible gap.

**Independent Test**: Start session, advance time to 7-min mark (mocked timer), verify new connection is created, history replayed, audio continues.

### Tests for User Story 3

- [x] T023 [P] [US3] Unit test for VoiceConnection state machine (CONNECTING→ACTIVE→RECONNECTING→DRAINING→CLOSED) in tests/unit/test_connection.py
- [x] T024 [P] [US3] Unit test for reconnection logic (timer fires, new session created, swap occurs, old closes) in tests/unit/test_reconnect.py
- [x] T025 [P] [US3] Unit test for ConversationHistory sliding window (add turns, summary generation, replay output, overflow beyond window_size triggers summarisation) in tests/unit/test_history.py

### Implementation for User Story 3

- [x] T026 [US3] Implement reconnection timer — asyncio timer fires at reconnect_at, triggers swap logic in src/voice_server/bidi/reconnect.py
- [x] T027 [US3] Implement hot-swap — create new BidiAgent in parallel, feed history as system context, swap input/output atomically in src/voice_server/bidi/reconnect.py
- [x] T028 [US3] Implement history summarisation — when turns > window_size, summarise oldest turns into a paragraph in src/voice_server/bidi/history.py
- [x] T029 [US3] Buffer user audio during RECONNECTING state — queue frames, flush to new session once ACTIVE in src/voice_server/bidi/input.py
- [x] T030 [US3] Send voice_reconnecting/voice_reconnected control messages to client during swap in src/voice_server/bidi/reconnect.py
- [x] T031 [US3] Wire reconnection into AudioBridge — start timer on session creation, handle swap lifecycle in src/voice_server/bidi/agent.py

**Checkpoint**: Conversations survive past 8 minutes with no audible interruption

---

## Phase 6: User Story 4 — Silence Timeout Handling (Priority: P2)

**Goal**: When voice service disconnects after 175s silence, system recovers gracefully and reconnects when user resumes.

**Independent Test**: Connect, stop sending audio for 175s (mocked), verify timeout detected, then send audio again and verify new connection established.

### Tests for User Story 4

- [x] T032 [P] [US4] Unit test for silence timeout detection and recovery state transition in tests/unit/test_connection.py

### Implementation for User Story 4

- [x] T033 [US4] Detect voice service disconnect (stream closed unexpectedly) and transition to recoverable state in src/voice_server/bidi/connection.py
- [x] T034 [US4] On user audio resumption after timeout, trigger reconnection with history replay (reuse reconnect.py logic) in src/voice_server/bidi/agent.py
- [x] T035 [US4] Send informational control message to client when silence timeout occurs and when recovery completes in src/voice_server/bidi/output.py

**Checkpoint**: Sessions survive extended silence periods and recover automatically

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Observability, error retry, metrics, final hardening

- [x] T036 [P] Implement immediate retry logic (3 attempts, no delay) on voice service errors in src/voice_server/bidi/agent.py
- [x] T037 [P] Add CloudWatch metrics for reconnection count/duration, barge-in latency, audio round-trip time, errors by type in src/voice_server/observability/metrics.py
- [x] T038 [P] Add X-Ray trace spans for voice connection lifecycle (connect, stream, reconnect, disconnect) in src/voice_server/bidi/agent.py
- [x] T039 [P] Add structured log events for all voice connection state transitions in src/voice_server/bidi/connection.py
- [x] T040 Update pyproject.toml with strands-agents version pin and verify uv lock resolves
- [ ] T041 Run quickstart.md validation — verify all commands work end-to-end with real Nova Sonic (requires AWS Bedrock credentials)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — core audio flow
- **User Story 2 (Phase 4)**: Depends on US1 (needs audio flowing to detect interruptions)
- **User Story 3 (Phase 5)**: Depends on US1 (needs working session to reconnect)
- **User Story 4 (Phase 6)**: Depends on US3 (reuses reconnection logic)
- **Polish (Phase 7)**: Depends on US1 + US2 + US3

### User Story Dependencies

- **US1** (Voice Conversation): Independent after Foundational — core MVP
- **US2** (Barge-In): Depends on US1 (must have audio flowing)
- **US3** (Reconnection): Depends on US1 (must have working session)
- **US4** (Silence Timeout): Depends on US3 (reuses reconnect logic)

### Within Each User Story

- Tests written FIRST, verify they FAIL
- Models/protocols before integration
- Integration into handler last

### Parallel Opportunities

- T004, T005, T006, T007, T008 can run in parallel (Foundational)
- T010, T011, T012, T013 can run in parallel (US1 tests)
- T019 independent (US2 test)
- T023, T024, T025 can run in parallel (US3 tests)
- T036, T037, T038, T039 can run in parallel (Polish)

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests in parallel:
Task: "Unit test for BidiInput in tests/unit/test_bidi_input.py"
Task: "Unit test for BidiOutput in tests/unit/test_bidi_output.py"
Task: "Unit test for resample in tests/unit/test_resample.py"
Task: "Integration test in tests/integration/test_bidi_agent.py"

# Then implementation sequentially:
Task: "Wire BidiInput queue into handler"
Task: "Wire BidiOutput to WebSocket"
Task: "Create AudioBridge class"
Task: "Integrate into session lifecycle"
Task: "Start BidiAgent.run() task"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Send audio, hear response back
5. This alone proves the Strands BidiAgent integration works end-to-end

### Incremental Delivery

1. Setup + Foundational → Bridge components ready
2. Add US1 (Voice Conversation) → Test → **MVP!** Audio flows bidirectionally
3. Add US2 (Barge-In) → Test → Natural conversation feel
4. Add US3 (Reconnection) → Test → Long conversations work
5. Add US4 (Silence Timeout) → Test → Robust session management
6. Add Polish → Production observability

### Suggested MVP Scope

**US1 only** — proves audio flows through Strands BidiAgent end-to-end. Barge-in and reconnection are essential for production but the core integration validates the architecture.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Integration test (T013) requires real AWS credentials with Bedrock access
- Total tasks: 41
