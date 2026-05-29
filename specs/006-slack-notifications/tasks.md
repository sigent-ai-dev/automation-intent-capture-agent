# Tasks: Slack Developer Notifications

**Input**: Design documents from `specs/006-slack-notifications/`

**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Included — notification delivery must be verified.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create package structure, add config, add httpx dependency

- [x] T001 Create package structure: src/voice_server/notifications/__init__.py
- [x] T002 [P] Add Slack config variables to src/voice_server/config.py (SLACK_WEBHOOK_URL, SLACK_CHANNEL, SLACK_ENABLED)
- [ ] T003 [P] Add respx to dev dependencies in pyproject.toml and run uv lock

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Event types, rate limiter, and notification dispatcher

- [x] T004 [P] Define notification event types (IntentFinalised, ErrorOccurred) in src/voice_server/notifications/events.py
- [x] T005 [P] Implement in-memory rate limiter (token bucket per event type, 1/min) in src/voice_server/notifications/rate_limiter.py
- [x] T006 Implement notification dispatcher (register adapters, dispatch async, no-op when empty) in src/voice_server/notifications/__init__.py

**Checkpoint**: Event types defined, rate limiter working, dispatcher dispatches to registered adapters

---

## Phase 3: User Story 1 — Intent Finalisation Notification (Priority: P1) MVP

**Goal**: Slack message sent when intent is finalised.

**Independent Test**: Finalise intent, verify Slack webhook receives correctly formatted payload.

### Tests for User Story 1

- [x] T007 [P] [US1] Unit test for Slack message formatting (intent notification, short doc inline, long doc summary only) in tests/unit/test_slack_notifications.py
- [x] T008 [P] [US1] Unit test for rate limiter (allow first, block within window, allow after window) in tests/unit/test_rate_limiter.py

### Implementation for User Story 1

- [x] T009 [US1] Implement Slack webhook client (async POST with httpx, format intent notification as Block Kit) in src/voice_server/notifications/slack.py
- [x] T010 [US1] Emit IntentFinalised event from finalise_intent tool after successful finalisation in src/voice_server/elicitation/tools.py
- [x] T011 [US1] Register Slack adapter on application startup (if configured) in src/voice_server/main.py

**Checkpoint**: Finalising an intent triggers a Slack message

---

## Phase 4: User Story 2 — Error Notification (Priority: P2)

**Goal**: Slack alert sent on unrecoverable errors.

**Independent Test**: Trigger voice service unavailable, verify error notification sent with rate limiting.

### Implementation for User Story 2

- [x] T012 [US2] Implement error notification formatting (Block Kit with warning emoji, session context) in src/voice_server/notifications/slack.py
- [x] T013 [US2] Emit ErrorOccurred event from AudioBridge._handle_agent_error when all retries exhausted in src/voice_server/bidi/agent.py
- [x] T014 [US2] Wire rate limiter into Slack adapter — check before sending, skip if rate-limited in src/voice_server/notifications/slack.py

**Checkpoint**: Errors trigger rate-limited Slack alerts

---

## Phase 5: User Story 3 — Configuration and Disabling (Priority: P3)

**Goal**: Notifications configurable and safely disabled.

### Implementation for User Story 3

- [x] T015 [US3] Implement graceful no-op when webhook URL is empty — adapter skips silently in src/voice_server/notifications/slack.py
- [x] T016 [US3] Log delivery failures as warnings without raising exceptions in src/voice_server/notifications/slack.py

**Checkpoint**: System works identically with or without notifications configured

---

## Phase 6: Polish

**Purpose**: Observability and validation

- [x] T017 [P] Add metrics for notifications (sent count, delivery failures, rate-limited drops) in src/voice_server/observability/metrics.py
- [x] T018 Run quickstart.md validation — verify notification flow end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — core notification
- **User Story 2 (Phase 4)**: Depends on US1 (reuses Slack client + dispatcher)
- **User Story 3 (Phase 5)**: Depends on US1 (config disable needs working adapter)
- **Polish (Phase 6)**: Depends on US1 + US2

### Parallel Opportunities

- T002, T003 can run in parallel (Setup)
- T004, T005 can run in parallel (Foundational)
- T007, T008 can run in parallel (US1 tests)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Finalise intent, verify Slack message arrives

### Suggested MVP Scope

**US1 only** — proves the notification pipeline works end-to-end. Error notifications and configuration are additive.

---

## Notes

- [P] tasks = different files, no dependencies
- httpx is already in dev deps — may already be available as a prod dep via another package
- Total tasks: 18
