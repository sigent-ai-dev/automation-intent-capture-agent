# Tasks: Cross-Channel Session Continuity

**Input**: Design documents from `specs/012-cross-channel-session-continuity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — cross-channel resume correctness must be verified.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add new dependencies, create package structure, extend DynamoDB schema

- [x] T001 Add slack-bolt dependency to pyproject.toml and run uv lock
- [x] T002 [P] Create channel adapter package structure: src/voice_server/channels/__init__.py, src/voice_server/channels/base.py
- [x] T003 [P] Create Slack adapter package: src/voice_server/channels/slack/__init__.py
- [x] T004 [P] Create Claude adapter package: src/voice_server/channels/claude/__init__.py
- [x] T005 [P] Add new config variables to src/voice_server/config.py (SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, HISTORY_SUMMARISE_THRESHOLD)
- [x] T006 Add user_email GSI to terraform/modules/voice-service/dynamodb.tf (attribute definition + global_secondary_index block)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Intent-keyed persistence adapters, user lookup, and shared session model that ALL user stories depend on

- [x] T007 [P] Implement IntentSession dataclass in src/voice_server/sessions/intent_session.py (intent_id, user_email, status, active_channels, section_attributions, version)
- [x] T008 [P] Implement IntentSessionAdapter (save/load/query by user_email via GSI) in src/voice_server/persistence/intent_session_adapter.py
- [x] T009 [P] Implement IntentHistoryAdapter (save/load history keyed by intent_id, turns with channel annotation) in src/voice_server/persistence/intent_history_adapter.py
- [x] T010 Implement user_lookup module (query GSI for active intents by email, return sorted list) in src/voice_server/sessions/user_lookup.py
- [x] T011 [P] Add query_gsi_by_email function to src/voice_server/persistence/client.py (query user-email-index with KeyConditionExpression on user_email)
- [x] T012 [P] Extend ConversationHistory.add_turn() to accept channel parameter in src/voice_server/bidi/history.py
- [x] T013 Implement ChannelAdapter protocol and adapter registry in src/voice_server/channels/base.py (protocol with resolve_identity, handle_message methods)
- [x] T014 Add intent lookup REST endpoints (GET /intents/active, POST /intents/{intent_id}/resume, POST /intents/{intent_id}/message) in src/voice_server/channels/endpoints.py

**Checkpoint**: Shared session layer complete — intent-keyed persistence, user lookup, and channel adapter protocol ready

---

## Phase 3: User Story 2 — Discover Active Intent by User Identity (Priority: P1)

**Goal**: Any channel adapter can look up active intents for a user by email.

**Independent Test**: Create an intent session record in DynamoDB with user_email, then query GET /intents/active?user_email=... and verify the correct intent is returned.

### Tests for User Story 2

- [x] T015 [P] [US2] Unit test for user_lookup — single intent, multiple intents, no intents cases in tests/unit/test_user_lookup.py
- [x] T016 [P] [US2] Unit test for IntentSessionAdapter — save, load, query_by_email in tests/unit/test_intent_session.py

### Implementation for User Story 2

- [x] T017 [US2] Wire user_lookup into GET /intents/active endpoint — resolve email from query param, query GSI, return intent list in src/voice_server/channels/endpoints.py
- [x] T018 [US2] Update voice adapter to create IntentSession record when create_intent tool is called in src/voice_server/elicitation/tools.py (write intent_id + user_email + status to DynamoDB)
- [x] T019 [US2] Extract user_email from Cognito token in voice session and pass through to elicitation tools in src/voice_server/ws/auth.py

**Checkpoint**: Channel adapters can discover active intents by email — foundation for cross-channel resume

---

## Phase 4: User Story 1 — Resume Elicitation on a Different Channel (Priority: P1)

**Goal**: User starts on voice, resumes on Slack or Claude — system picks up where it left off.

**Independent Test**: Create a draft intent with 3 populated sections via voice. Call POST /intents/{id}/resume from Slack adapter. Verify agent response acknowledges existing progress and guides remaining sections.

### Tests for User Story 1

- [ ] T020 [P] [US1] Unit test for resume flow — load intent session, build resume context, verify agent response includes progress in tests/unit/test_cross_channel_resume.py
- [ ] T021 [P] [US1] Integration test for voice→Slack resume (mock DynamoDB, verify full flow) in tests/integration/test_cross_channel_resume.py


### Implementation for User Story 1

- [x] T022 [US1] Implement resume logic in POST /intents/{intent_id}/resume — load IntentSession, verify user, load history, build resume prompt, invoke elicitation agent in src/voice_server/channels/endpoints.py
- [x] T023 [US1] Enhance build_resume_context() to include conversation history summary and channel sources in src/voice_server/elicitation/prompts.py
- [x] T024 [US1] Implement message relay in POST /intents/{intent_id}/message — add turn to history, invoke agent, return response in src/voice_server/channels/endpoints.py
- [x] T025 [US1] Update elicitation tools to accept channel parameter and record it on section updates in src/voice_server/elicitation/tools.py

**Checkpoint**: Cross-channel resume works end-to-end — core value proposition delivered

---

## Phase 5: User Story 3 — Conversation History Carries Across Channels (Priority: P2)

**Goal**: New channel gets full cross-channel history with channel annotations and summarisation.

**Independent Test**: Create 35 turns across voice and Slack. Resume on Claude. Verify agent receives summary of first 5 turns + verbatim last 30, each annotated with channel.

### Tests for User Story 3

- [x] T026 [P] [US3] Unit test for IntentHistoryAdapter — save/load turns with channel field, verify ordering in tests/unit/test_intent_history.py
- [x] T027 [P] [US3] Unit test for history summarisation at 30-turn threshold in tests/unit/test_intent_history.py

### Implementation for User Story 3

- [x] T028 [US3] Implement 30-turn summarisation in IntentHistoryAdapter — when turn_count > 30, summarise oldest turns via elicitation agent's model; fallback to simple concatenation if LLM call fails in src/voice_server/persistence/intent_history_adapter.py
- [ ] T029 [US3] Update voice adapter to write turns to intent-keyed history (in addition to session-keyed for backward compat) in src/voice_server/bidi/agent.py
- [x] T030 [US3] Ensure resume endpoint loads intent-keyed history and injects into agent context in src/voice_server/channels/endpoints.py

**Checkpoint**: Full conversation context carries across channels with summarisation

---

## Phase 6: User Story 4 — Channel Attribution on Intent Documents (Priority: P3)

**Goal**: Intent document records which channel contributed each section.

**Independent Test**: Populate context via voice, motivation via Slack. Load IntentSession record. Verify section_attributions map has correct channel and timestamps.

### Implementation for User Story 4

- [x] T031 [P] [US4] Add ChannelContribution dataclass (channel, timestamp) to src/voice_server/sessions/intent_session.py
- [x] T032 [US4] Record channel attribution in IntentSession.section_attributions when update_intent_section is called in src/voice_server/elicitation/tools.py
- [x] T033 [US4] Expose channel attributions in GET /intents/active and status responses in src/voice_server/channels/endpoints.py

**Checkpoint**: Audit trail shows which channel populated each section

---

## Phase 7: Slack Inbound Adapter

**Goal**: Slack bot handles @mentions and DMs, resolves identity, drives elicitation in threads.

**Independent Test**: @mention the bot in Slack, verify it resolves your email, finds your active intent, and replies in a thread with progress summary.

### Tests for Slack Adapter

- [x] T034 [P] Unit test for Slack identity resolution (users.info → email extraction) in tests/unit/test_slack_adapter.py
- [ ] T035 [P] Unit test for Slack event routing (app_mention → resume, message.im → message) in tests/unit/test_slack_adapter.py

### Implementation for Slack Adapter

- [x] T036 Implement Slack Bolt app with event handlers (app_mention, message.im) in src/voice_server/channels/slack/app.py
- [x] T037 Implement Slack identity resolution (user ID → email via users.info) in src/voice_server/channels/slack/identity.py
- [x] T038 Implement Slack elicitation bridge (route events to resume/message endpoints, format responses as Block Kit, reply in thread, handle multi-draft selection prompt) in src/voice_server/channels/slack/elicitation.py
- [x] T039 Register Slack adapter on startup (if SLACK_BOT_TOKEN configured) in src/voice_server/main.py
- [x] T040 Mount Slack event handler route at /slack/events in src/voice_server/main.py

**Checkpoint**: Slack bot conducts full elicitation sessions in threads

---

## Phase 8: Claude Skill Adapter

**Goal**: MCP tool allows Claude to drive intent capture.

**Independent Test**: Call intent_capture tool with action "list", verify it returns active intents. Call with "resume", verify agent response includes progress.

### Tests for Claude Adapter

- [x] T041 [P] Unit test for Claude skill — list, start, resume, message, status actions in tests/unit/test_claude_adapter.py

### Implementation for Claude Adapter

- [x] T042 Implement Claude MCP tool (intent_capture) with action routing (including multi-draft selection on resume, warn if active draft exists on start) in src/voice_server/channels/claude/skill.py
- [x] T043 Implement identity resolution for Claude (CLI: git config email, web: Cognito session, explicit --user-email overrides both) in src/voice_server/channels/claude/skill.py

**Checkpoint**: Claude can drive full elicitation sessions via MCP tool

---

## Phase 9: Polish & Backward Compatibility

**Purpose**: Ensure existing voice-only flow is unaffected, add observability

- [ ] T044 [P] Add metrics for cross-channel operations (resume_count, lookup_count, channel_switch) in src/voice_server/observability/metrics.py
- [ ] T045 Verify backward compatibility — run existing test suite, confirm voice-only sessions work without IntentSession record, verify no regressions in session/elicitation/history flows
- [ ] T046 [P] Update quickstart.md with tested commands and verified output in specs/012-cross-channel-session-continuity/quickstart.md
- [ ] T047 Validate Intent Kit compatibility — produce a multi-channel intent document and run `intent check` against it to confirm SC-004
- [ ] T048 Run full E2E validation: voice session → Slack resume → Claude status check

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 2 (Phase 3)**: Depends on Foundational — user lookup is prerequisite for US1
- **User Story 1 (Phase 4)**: Depends on US2 (needs user lookup to find intents)
- **User Story 3 (Phase 5)**: Depends on US1 (needs resume flow to inject history)
- **User Story 4 (Phase 6)**: Depends on US1 (needs section update flow)
- **Slack Adapter (Phase 7)**: Depends on US1 + US2 (needs resume + lookup)
- **Claude Adapter (Phase 8)**: Depends on US1 + US2 (needs resume + lookup)
- **Polish (Phase 9)**: Depends on all prior phases

### Parallel Opportunities

- T002, T003, T004, T005 can run in parallel (Setup — different files)
- T007, T008, T009, T011, T012, T013 can run in parallel (Foundational — different files)
- T015, T016 can run in parallel (US2 tests)
- T020, T021 can run in parallel (US1 tests)
- T026, T027 can run in parallel (US3 tests)
- T034, T035 can run in parallel (Slack tests)
- Phase 7 (Slack) and Phase 8 (Claude) can run in parallel once US1 + US2 are complete

---

## Implementation Strategy

### MVP First (User Story 2 + User Story 1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 2 (discover active intents)
4. Complete Phase 4: User Story 1 (cross-channel resume)
5. **STOP and VALIDATE**: Resume intent from a different channel via REST API

### Suggested MVP Scope

**US2 + US1** — proves the cross-channel lookup and resume pipeline works end-to-end. Slack and Claude adapters are additive UI layers on top of the proven core.

---

## Notes

- [P] tasks = different files, no dependencies
- slack-bolt handles Slack Events API signature verification and 3-second ack deadline
- Intent-keyed history coexists with session-keyed history (backward compat)
- Voice adapter dual-writes: session-keyed (legacy) + intent-keyed (new)
- Total tasks: 48
