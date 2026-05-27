# Tasks: Voice Intent Elicitation

**Input**: Design documents from `specs/003-voice-intent-elicitation/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/intent-tools-contract.md

**Tests**: Included — spec requires tool behaviour testing and intent-kit format compliance.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create package structure and add configuration for elicitation

- [x] T001 Create package structure: src/voice_server/elicitation/__init__.py
- [x] T002 [P] Add INTENT_DIR environment variable to src/voice_server/config.py (default: ".intent")

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: IntentDocument model and filesystem storage — ALL user stories depend on these

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Implement IntentDocument dataclass (parse/render intent-kit markdown format) in src/voice_server/elicitation/intent_doc.py
- [x] T004 [P] Implement filesystem storage (create .intent/ dir, scan for next ID, atomic write via temp+rename, read by ID) in src/voice_server/elicitation/storage.py
- [x] T005 [P] Implement elicitation system prompt (role, behaviour, tool usage, completion instructions) in src/voice_server/elicitation/prompts.py
- [x] T006 Define Strands @tool functions (create_intent, update_intent_section, read_intent, finalise_intent) with docstrings and type hints in src/voice_server/elicitation/tools.py

**Checkpoint**: Foundation ready — tools exist, document model parses/renders, storage reads/writes

---

## Phase 3: User Story 1 — Conversational Intent Capture (Priority: P1) MVP

**Goal**: User speaks their idea, agent produces a valid `.intent/INT-NNN.md` with Context, Intent, Motivation populated.

**Independent Test**: Start voice session, describe a project idea, verify agent creates a valid intent document.

### Tests for User Story 1

- [x] T007 [P] [US1] Unit test for IntentDocument parse/render (round-trip, missing sections, frontmatter) in tests/unit/test_intent_doc.py
- [x] T008 [P] [US1] Unit test for storage (create dir, next ID scan, atomic write, read by ID) in tests/unit/test_storage.py
- [x] T009 [P] [US1] Unit test for tool functions (create_intent happy path, validation errors, update_intent_section append/replace, read_intent, finalise_intent) in tests/unit/test_elicitation_tools.py
- [ ] T010 [P] [US1] Integration test for elicitation flow (mock BidiAgent invokes tools in sequence, produces valid document) in tests/integration/test_elicitation_flow.py

### Implementation for User Story 1

- [x] T011 [US1] Implement create_intent tool — validate inputs, call storage.create(), return intent_id and path in src/voice_server/elicitation/tools.py
- [x] T012 [US1] Implement update_intent_section tool — load doc, replace/append section, save in src/voice_server/elicitation/tools.py
- [x] T013 [US1] Implement read_intent tool — load doc, return content + populated/empty section lists in src/voice_server/elicitation/tools.py
- [x] T014 [US1] Implement finalise_intent tool — validate mandatory fields, set Status: confirmed, save in src/voice_server/elicitation/tools.py
- [x] T015 [US1] Register elicitation tools in BidiAgent — modify create_bidi_agent() to accept and include tools in src/voice_server/bidi/agent.py
- [x] T016 [US1] Wire elicitation system prompt into AudioBridge.start() — prepend elicitation instructions to system prompt in src/voice_server/bidi/agent.py

**Checkpoint**: A user can speak and the agent captures their intent into a valid document

---

## Phase 4: User Story 2 — Iterative Refinement (Priority: P1)

**Goal**: User can correct or add to captured intent without losing existing content.

**Independent Test**: Capture intent, then provide a correction — verify document updates without overwriting other sections.

### Implementation for User Story 2

- [x] T017 [US2] Implement append mode in update_intent_section for list sections (quality_attributes, success_criteria, assumptions, clarifications) with auto-incrementing IDs in src/voice_server/elicitation/tools.py
- [x] T018 [US2] Implement read-back capability — read_intent returns natural-language summary suitable for voice narration in src/voice_server/elicitation/tools.py
- [x] T019 [US2] Add contradiction handling to system prompt — instruct agent to acknowledge changes and update (not duplicate) in src/voice_server/elicitation/prompts.py

**Checkpoint**: User can iteratively refine intent without data loss

---

## Phase 5: User Story 3 — Clarification Elicitation (Priority: P2)

**Goal**: Agent asks targeted questions when description is vague, records unresolved gaps as OPEN clarifications.

**Independent Test**: Describe a vague idea, verify agent asks 2-3 questions and records unanswered ones as CLR-NNN entries.

### Implementation for User Story 3

- [x] T020 [US3] Add clarification recording to update_intent_section — support adding CLR-NNN entries with Prompt and Resolution fields in src/voice_server/elicitation/tools.py
- [x] T021 [US3] Extend system prompt with clarification behaviour — max 3 questions, prioritise by scope impact, record gaps as OPEN in src/voice_server/elicitation/prompts.py
- [x] T022 [US3] Implement early-exit handling in finalise_intent — record empty optional sections as OPEN clarifications before confirming in src/voice_server/elicitation/tools.py

**Checkpoint**: Agent intelligently probes for gaps without over-questioning

---

## Phase 6: User Story 4 — Multi-Session Continuity (Priority: P3)

**Goal**: User returns to a previous session and the agent picks up where it left off.

**Independent Test**: Create a draft intent, start new session, verify agent loads existing document and identifies gaps.

### Implementation for User Story 4

- [x] T023 [US4] Implement session detection — on AudioBridge start, scan .intent/ for draft documents and load most recent in src/voice_server/elicitation/storage.py
- [x] T024 [US4] Add resume logic to system prompt — when draft exists, instruct agent to acknowledge progress and guide toward remaining gaps in src/voice_server/elicitation/prompts.py
- [x] T025 [US4] Wire session detection into AudioBridge.start() — if draft found, pass document state to system prompt context in src/voice_server/bidi/agent.py

**Checkpoint**: Conversations survive across sessions without re-asking answered questions

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, observability, validation

- [x] T026 [P] Implement retry logic in tool functions — silent retry once on filesystem errors, return error on persistent failure in src/voice_server/elicitation/tools.py
- [x] T027 [P] Add structured logging for tool invocations (create, update, read, finalise) in src/voice_server/elicitation/tools.py
- [x] T028 [P] Add metrics for intent capture (documents created, sessions to completion, average fields populated) in src/voice_server/observability/metrics.py
- [ ] T029 Run quickstart.md validation — verify tool invocation produces valid intent-kit document

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — core capture flow
- **User Story 2 (Phase 4)**: Depends on US1 (needs working tools to refine)
- **User Story 3 (Phase 5)**: Depends on US1 (needs working tools to add clarifications)
- **User Story 4 (Phase 6)**: Depends on US1 (needs existing documents to resume)
- **Polish (Phase 7)**: Depends on US1 + US2 + US3

### User Story Dependencies

- **US1** (Capture): Independent after Foundational — core MVP
- **US2** (Refinement): Depends on US1 (needs update_intent_section working)
- **US3** (Clarification): Depends on US1 (needs tools + clarification section format)
- **US4** (Multi-Session): Depends on US1 (needs draft documents to exist)

### Within Each User Story

- Tests written FIRST, verify they FAIL
- Models/storage before tools
- Tools before agent integration
- Agent integration last

### Parallel Opportunities

- T003, T004, T005 can run in parallel (Foundational — different files)
- T007, T008, T009, T010 can run in parallel (US1 tests)
- T026, T027, T028 can run in parallel (Polish)

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests in parallel:
Task: "Unit test for IntentDocument in tests/unit/test_intent_doc.py"
Task: "Unit test for storage in tests/unit/test_storage.py"
Task: "Unit test for tool functions in tests/unit/test_elicitation_tools.py"
Task: "Integration test in tests/integration/test_elicitation_flow.py"

# Then implementation sequentially:
Task: "Implement create_intent tool"
Task: "Implement update_intent_section tool"
Task: "Implement read_intent tool"
Task: "Implement finalise_intent tool"
Task: "Register tools in BidiAgent"
Task: "Wire system prompt into AudioBridge"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Invoke tools manually, verify intent document is valid intent-kit format
5. This alone proves the elicitation tool chain works end-to-end

### Incremental Delivery

1. Setup + Foundational → Document model and storage ready
2. Add US1 (Capture) → Test → **MVP!** Agent produces intent documents from voice
3. Add US2 (Refinement) → Test → Users can iterate on captured intent
4. Add US3 (Clarification) → Test → Agent probes intelligently for gaps
5. Add US4 (Multi-Session) → Test → Sessions survive across connections
6. Add Polish → Production observability

### Suggested MVP Scope

**US1 only** — proves the full tool chain: voice → tool invocation → intent document on disk. Refinement and clarification are important for quality but the core architecture validates with capture alone.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Integration test (T010) requires mocked BidiAgent (no real Nova Sonic needed for tool testing)
- Total tasks: 29
