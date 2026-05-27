# Tasks: Browser Frontend with Web Audio API

**Input**: Design documents from `specs/005-browser-frontend/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/websocket.md

**Tests**: Included (spec references Vitest + Playwright as testing stack).

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US5)
- Exact file paths included

## User Stories (derived from spec ACs)

| ID | Title | Priority |
|----|-------|----------|
| US1 | Start a capture session | P1 (MVP) |
| US2 | Voice conversation (speak + hear agent) | P1 (MVP) |
| US3 | Session progress tracking | P2 |
| US4 | Session completion & intent display | P1 (MVP) |
| US5 | Error recovery & graceful degradation | P2 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, tooling, dependencies

- [ ] T001 Initialize Vite + React + TypeScript project in frontend/ with `npm create vite@latest`
- [ ] T002 Install production dependencies (react, react-dom, pcm-player, react-window, react-markdown, date-fns) in frontend/package.json
- [ ] T003 [P] Install dev dependencies (vitest, @testing-library/react, playwright, eslint, prettier, tailwindcss, postcss, autoprefixer) in frontend/package.json
- [ ] T004 [P] Configure TypeScript strict mode in frontend/tsconfig.json
- [ ] T005 [P] Configure Tailwind CSS with PostCSS in frontend/tailwind.config.js and frontend/postcss.config.js
- [ ] T006 [P] Configure ESLint + Prettier in frontend/.eslintrc.cjs and frontend/.prettierrc
- [ ] T007 [P] Configure Vitest in frontend/vitest.config.ts
- [ ] T008 Configure Vite with dev proxy (REST + WebSocket → localhost:8080) in frontend/vite.config.ts
- [ ] T009 [P] Create environment files frontend/.env.development and frontend/.env.example
- [ ] T010 [P] Create runtime config frontend/public/config.js with APP_CONFIG pattern
- [ ] T011 Create entry point frontend/index.html and frontend/src/main.tsx

**Checkpoint**: `npm run dev` starts without errors, blank page renders.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Design system, shared components, and contexts that ALL stories depend on

- [ ] T012 Create design tokens in frontend/src/styles/design-tokens.css (all CSS custom properties from spec §7)
- [ ] T013 [P] Create global styles in frontend/src/styles/globals.css (reset, scrollbars, focus states, animations)
- [ ] T014 [P] Create component base styles in frontend/src/styles/components.css (btn, card, input, badge, alert, spinner)
- [ ] T015 Implement ThemeContext in frontend/src/contexts/ThemeContext.tsx (light/dark/system, localStorage persist)
- [ ] T016 [P] Implement ThemeProvider in frontend/src/components/layout/ThemeToggle.tsx
- [ ] T017 Implement MainLayout in frontend/src/components/layout/MainLayout.tsx and MainLayout.css
- [ ] T018 [P] Implement Header in frontend/src/components/layout/Header.tsx and Header.css
- [ ] T019 [P] Implement ErrorBoundary in frontend/src/components/common/ErrorBoundary.tsx
- [ ] T020 [P] Implement LoadingSpinner in frontend/src/components/common/LoadingSpinner.tsx
- [ ] T021 [P] Implement ErrorBanner in frontend/src/components/common/ErrorBanner.tsx
- [ ] T022 [P] Implement ShortcutHelp modal in frontend/src/components/common/ShortcutHelp.tsx
- [ ] T023 Implement useKeyboardShortcuts hook in frontend/src/hooks/useKeyboardShortcuts.ts (Escape, Ctrl+K, Ctrl+Shift+C)
- [ ] T024 Create TypeScript types in frontend/src/types/ (session.ts, conversation.ts, websocket.ts, audio.ts, theme.ts)
- [ ] T025 Create constants in frontend/src/config/constants.ts (audio params, WebSocket URL, feature flags)
- [ ] T026 Wire App.tsx with ErrorBoundary + ThemeContextProvider + MainLayout in frontend/src/App.tsx
- [ ] T027 [P] Create SVG logo placeholder in frontend/public/logo.svg

**Checkpoint**: App renders with Header, dark/light toggle works, keyboard shortcuts fire.

---

## Phase 3: User Story 1 — Start a Capture Session (Priority: P1) 🎯 MVP

**Goal**: User sees landing page, enters project name, clicks "Start Capture", session is created via REST API, WebSocket connects and negotiates codec.

**Independent Test**: Click Start → session appears in `GET /sessions` → WebSocket reaches `session_ready`.

### Tests for US1

- [ ] T028 [P] [US1] Unit test for sessionService in frontend/src/services/sessionService.test.ts (mock fetch: create, get, list, delete)
- [ ] T029 [P] [US1] Component test for LandingView in frontend/src/components/session/LandingView.test.tsx

### Implementation for US1

- [ ] T030 [P] [US1] Implement sessionService in frontend/src/services/sessionService.ts (POST/GET/DELETE /sessions)
- [ ] T031 [US1] Implement SessionContext in frontend/src/contexts/SessionContext.tsx (state machine: idle→creating→connecting→negotiating→active→complete)
- [ ] T032 [US1] Implement useSession hook in frontend/src/hooks/useSession.ts (wraps context, exposes startSession/endSession)
- [ ] T033 [US1] Implement LandingView in frontend/src/components/session/LandingView.tsx (project name input, Start Capture button, previous sessions list)
- [ ] T034 [US1] Implement websocketService in frontend/src/services/websocketService.ts (connect, send codec_negotiate, handle codec_ack + session_ready, heartbeat, reconnect)
- [ ] T035 [US1] Implement WebSocketContext in frontend/src/contexts/WebSocketContext.tsx (connection state, message dispatch)
- [ ] T036 [US1] Implement ConnectionStatus in frontend/src/components/connection/ConnectionStatus.tsx (green/yellow/red dot + label)
- [ ] T037 [US1] Wire session flow in App.tsx: LandingView shown in IDLE state, transition on session create

**Checkpoint**: Full flow: click Start → POST /sessions → WebSocket connects → codec negotiated → session_ready received → UI shows "Active".

---

## Phase 4: User Story 2 — Voice Conversation (Priority: P1) 🎯 MVP

**Goal**: User clicks mic, speaks, audio streams to server. Agent response audio plays back. Real-time transcript appears as chat bubbles.

**Independent Test**: Click mic → speak → see user transcript → hear agent response → see agent transcript.

### Tests for US2

- [ ] T038 [P] [US2] Unit test for audioUtils in frontend/src/utils/audioUtils.test.ts (float32→int16 conversion)
- [ ] T039 [P] [US2] Unit test for base64Utils in frontend/src/utils/base64Utils.test.ts
- [ ] T040 [P] [US2] Component test for ControlPanel in frontend/src/components/controls/ControlPanel.test.tsx

### Implementation for US2

- [ ] T041 [P] [US2] Create audio-processor.js AudioWorklet in frontend/public/audio-processor.js
- [ ] T042 [P] [US2] Implement audioUtils in frontend/src/utils/audioUtils.ts (float32ToInt16, detectWorkletSupport)
- [ ] T043 [P] [US2] Implement base64Utils in frontend/src/utils/base64Utils.ts (encode/decode ArrayBuffer↔base64)
- [ ] T044 [US2] Implement useAudioCapture hook in frontend/src/hooks/useAudioCapture.ts (AudioWorklet + ScriptProcessorNode fallback, level metering)
- [ ] T045 [US2] Implement useAudioPlayback hook in frontend/src/hooks/useAudioPlayback.ts (pcm-player create/feed/destroy, barge-in handling)
- [ ] T046 [US2] Implement ConversationContext in frontend/src/contexts/ConversationContext.tsx (messages array, add/update by role+final)
- [ ] T047 [P] [US2] Implement MicButton in frontend/src/components/controls/MicButton.tsx (green↔red, pulsing animation, disabled state)
- [ ] T048 [P] [US2] Implement AudioMeter in frontend/src/components/controls/AudioMeter.tsx (horizontal bar, 0-100% level)
- [ ] T049 [US2] Implement ControlPanel in frontend/src/components/controls/ControlPanel.tsx and ControlPanel.css (mic + meter + end session)
- [ ] T050 [US2] Implement Message component in frontend/src/components/chat/Message.tsx (user/agent bubble, timestamp, interim/final styling)
- [ ] T051 [US2] Implement MessageList in frontend/src/components/chat/MessageList.tsx (react-window VariableSizeList, auto-scroll, height cache)
- [ ] T052 [US2] Implement useVirtualizedMessages hook in frontend/src/hooks/useVirtualizedMessages.ts (height measurement, resetAfterIndex)
- [ ] T053 [US2] Implement ActiveSessionView in frontend/src/components/session/ActiveSessionView.tsx (MessageList + ControlPanel layout)
- [ ] T054 [US2] Wire audio: WebSocket binary → useAudioPlayback, useAudioCapture → WebSocket binary, transcript messages → ConversationContext

**Checkpoint**: Full voice loop: mic on → speak → user transcript appears → agent audio plays → agent transcript appears.

---

## Phase 5: User Story 3 — Session Progress Tracking (Priority: P2)

**Goal**: Sidebar shows which intent sections are covered, proposal round count, and alignment confidence meter.

**Independent Test**: As conversation progresses, progress panel updates sections ✓, rounds increment, alignment bar fills.

### Tests for US3

- [ ] T055 [P] [US3] Component test for ProgressPanel in frontend/src/components/session/ProgressPanel.test.tsx

### Implementation for US3

- [ ] T056 [P] [US3] Implement ProgressPanel in frontend/src/components/session/ProgressPanel.tsx (sections checklist, proposal counter, alignment meter, status badge)
- [ ] T057 [US3] Handle `progress` WebSocket messages in WebSocketContext → update SessionContext.progress
- [ ] T058 [US3] Handle `intent_preview` WebSocket messages → render live markdown preview in ProgressPanel
- [ ] T059 [US3] Integrate ProgressPanel into ActiveSessionView as collapsible right sidebar

**Checkpoint**: Progress panel shows live updates as server sends `progress` messages.

---

## Phase 6: User Story 4 — Session Completion & Intent Display (Priority: P1) 🎯 MVP

**Goal**: When session completes, show the full rendered intent.md, audit trail, and download button. User can start a new session.

**Independent Test**: Session status = complete → CompletionView renders markdown → download produces .md file.

### Tests for US4

- [ ] T060 [P] [US4] Component test for CompletionView in frontend/src/components/session/CompletionView.test.tsx

### Implementation for US4

- [ ] T061 [US4] Implement EndSessionButton in frontend/src/components/controls/EndSessionButton.tsx (calls DELETE /sessions/:id, transitions to cancelled)
- [ ] T062 [US4] Handle `session_complete` WebSocket message → transition to COMPLETING → poll GET /sessions/:id/result
- [ ] T063 [US4] Implement CompletionView in frontend/src/components/session/CompletionView.tsx (react-markdown render, audit trail collapsible, download button, new session button)
- [ ] T064 [US4] Implement download logic: generate blob from intent_md, trigger download as `intent.md`
- [ ] T065 [US4] Wire completion flow in App.tsx: COMPLETE state shows CompletionView, "New Session" returns to IDLE

**Checkpoint**: End session → completion view appears → intent.md renders beautifully → download works → can start new session.

---

## Phase 7: User Story 5 — Error Recovery & Graceful Degradation (Priority: P2)

**Goal**: Mic permission denied shows text fallback. WebSocket drops reconnect automatically. All error states have clear recovery paths.

**Independent Test**: Deny mic → text input appears → type message → sent to server. Kill WebSocket → "Reconnecting..." → auto-recovers.

### Tests for US5

- [ ] T066 [P] [US5] Unit test for websocketService reconnection logic in frontend/src/services/websocketService.test.ts
- [ ] T067 [P] [US5] Component test for TextInput in frontend/src/components/controls/TextInput.test.tsx

### Implementation for US5

- [ ] T068 [US5] Implement TextInput fallback in frontend/src/components/controls/TextInput.tsx (shown when captureMode = 'unavailable')
- [ ] T069 [US5] Add mic permission error handling in useAudioCapture: detect NotAllowedError, set captureMode to 'unavailable', show ErrorBanner with instructions
- [ ] T070 [US5] Implement WebSocket reconnection with exponential backoff (1s, 2s, 4s, 8s, 16s) in websocketService.ts
- [ ] T071 [US5] Add reconnection UI: "Reconnecting..." toast in ConnectionStatus, counter of attempts
- [ ] T072 [US5] Handle `server_shutdown` message: show banner "Server restarting...", auto-reconnect after drain_seconds
- [ ] T073 [US5] Add `beforeunload` warning when session is active in useSession hook
- [ ] T074 [US5] Wire TextInput: send text as JSON `{ type: "text_input", text }` via WebSocket (server treats as typed user utterance)

**Checkpoint**: All error paths tested: mic denied → text works; disconnect → reconnects; server shutdown → graceful.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Testing, cross-browser, performance, accessibility

- [ ] T075 [P] Write E2E test: full session flow (start → speak → complete) with mocked WebSocket in frontend/tests/e2e/session-flow.spec.ts
- [ ] T076 [P] Write E2E test: text fallback flow in frontend/tests/e2e/text-fallback.spec.ts
- [ ] T077 Configure Playwright for Chrome, Firefox, Safari in frontend/playwright.config.ts
- [ ] T078 Bundle size audit: verify <200KB gzipped (adjust imports if needed)
- [ ] T079 [P] Accessibility pass: add ARIA labels to MicButton, ConnectionStatus, ProgressPanel; manage focus on view transitions
- [ ] T080 [P] Add responsive breakpoints: collapse ProgressPanel on mobile, stack controls vertically
- [ ] T081 Final integration test: run frontend against live backend (manual verification)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — BLOCKS US2, US4 (need WebSocket + session)
- **Phase 4 (US2)**: Depends on US1 (needs WebSocket connection)
- **Phase 5 (US3)**: Depends on US1 (needs WebSocket messages) — can parallel with US2
- **Phase 6 (US4)**: Depends on US1 (needs session lifecycle)
- **Phase 7 (US5)**: Depends on US1 + US2 (adds resilience to existing flows)
- **Phase 8 (Polish)**: Depends on all desired stories complete

### User Story Dependencies

- **US1 (Session Start)**: Foundational only — no story deps — MUST be first
- **US2 (Voice)**: Depends on US1 (WebSocket must be connected)
- **US3 (Progress)**: Depends on US1 (WebSocket messages) — parallel with US2/US4
- **US4 (Completion)**: Depends on US1 (session lifecycle) — parallel with US2/US3
- **US5 (Errors)**: Depends on US1 + US2 (enhances existing)

### Within Each User Story

- Tests written first (must FAIL before implementation)
- Utilities/services before hooks
- Hooks before components
- Components before view orchestration
- View wired into App.tsx last

### Parallel Opportunities

Within Phase 2: T012-T014 (styles) in parallel, T019-T022 (common components) in parallel, T024-T025 (types/config) in parallel.

Within US2: T041-T043 (audio utils/worklet) in parallel, T047-T048 (mic button + meter) in parallel.

US3 and US4 can be worked in parallel once US1 is complete.

---

## Parallel Example: User Story 2

```bash
# Parallel batch 1 (utilities + worklet):
Task T041: "Create audio-processor.js AudioWorklet in frontend/public/audio-processor.js"
Task T042: "Implement audioUtils in frontend/src/utils/audioUtils.ts"
Task T043: "Implement base64Utils in frontend/src/utils/base64Utils.ts"

# Parallel batch 2 (after hooks complete):
Task T047: "Implement MicButton in frontend/src/components/controls/MicButton.tsx"
Task T048: "Implement AudioMeter in frontend/src/components/controls/AudioMeter.tsx"
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US4)

1. Phase 1: Setup → `npm run dev` works
2. Phase 2: Foundational → themed layout renders
3. Phase 3: US1 → can create session + connect WebSocket
4. Phase 4: US2 → full voice conversation works
5. Phase 6: US4 → session completes, intent displayed
6. **STOP**: MVP delivered — user can capture intent via voice

### Incremental Delivery

7. Phase 5: US3 → progress sidebar added
8. Phase 7: US5 → resilience (reconnect, text fallback)
9. Phase 8: Polish → cross-browser, a11y, perf

---

## Notes

- Total tasks: 81
- MVP tasks (US1+US2+US4): 52
- Parallel opportunities: 14 batches identified
- Each user story independently testable at its checkpoint
- `npm run dev` proxies all requests to backend — no CORS issues in development
