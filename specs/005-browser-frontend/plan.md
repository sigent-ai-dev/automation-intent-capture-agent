# Implementation Plan: Browser Frontend with Web Audio API

**Branch**: `5-browser-frontend` | **Date**: 2026-05-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-browser-frontend/spec.md`

## Summary

React 18 + TypeScript single-page app for voice-based intent capture. Reuses trainline-voice-poc patterns (Vite, Tailwind, PCM audio, WebSocket service class) with a new session lifecycle, AudioWorklet-based capture, progress tracking sidebar, and intent completion view. Connects to the existing FastAPI backend (WebSocket at `/ws/audio`, REST at `/sessions`).

## Technical Context

**Language/Version**: TypeScript 5.3+ (strict mode), targeting ES2022

**Primary Dependencies**: React 18, Vite 5, Tailwind CSS 3.4, pcm-player, react-window, react-markdown, date-fns

**Storage**: None (session state lives server-side; localStorage for theme preference only)

**Testing**: Vitest + React Testing Library (unit/component), Playwright (E2E)

**Target Platform**: Modern browsers — Chrome 90+, Firefox 90+, Safari 14.5+ (AudioWorklet support)

**Project Type**: Single-page web application (frontend only)

**Performance Goals**: <2s audio round-trip latency, 60fps during streaming, <200KB gzipped bundle

**Constraints**: No auth in MVP (deferred #10), must work without mic (text fallback), AudioWorklet primary with ScriptProcessorNode fallback

**Scale/Scope**: Single user per session, one session at a time per browser tab

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Meet Them Where They Are | ✓ PASS | Browser voice UI — no tool installation needed |
| II. Propose, Don't Interrogate | ✓ PASS | UI shows progress panel tracking propose-and-steer flow |
| III. Structured Output | ✓ PASS | CompletionView renders `intent.md` (7-section format) |
| IV. Multi-Source Convergence | N/A | Single-channel (voice browser) for this issue |
| V. Channel-Agnostic Core | ✓ PASS | Frontend is a channel adapter — doesn't embed elicitation logic |
| VI. Graceful Degradation | ✓ PASS | Text fallback when mic denied; reconnect on drop; AudioWorklet→ScriptProcessor fallback |

| Quality Standard | Status | Evidence |
|-----------------|--------|----------|
| Voice latency <800ms barge-in | ✓ PASS | Immediate playback stop on user speech (§6.4) |
| API responses <200ms | ✓ PASS | Frontend displays loading states; backend already meets this |
| Sessions survive reconnection | ✓ PASS | Auto-reconnect to same session, progress preserved (§6.3) |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-browser-frontend/
├── spec.md              ← feature specification
├── plan.md              ← this file
├── research.md          ← Phase 0 research findings
├── data-model.md        ← Phase 1 data model
└── contracts/
    └── websocket.md     ← WebSocket message contract
```

### Implementation

```text
frontend/
├── index.html
├── public/
│   ├── config.js
│   ├── logo.svg
│   └── audio-processor.js    ← AudioWorklet processor
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── chat/
│   │   ├── controls/
│   │   ├── session/
│   │   ├── connection/
│   │   ├── layout/
│   │   └── common/
│   ├── contexts/
│   ├── hooks/
│   ├── services/
│   ├── types/
│   ├── utils/
│   ├── config/
│   └── styles/
├── tests/
├── vite.config.ts
├── vitest.config.ts
├── tailwind.config.js
├── tsconfig.json
├── postcss.config.js
└── package.json
```

---

## Phase 0: Research

### Research Tasks

1. **AudioWorklet implementation** — How to implement PCM capture with AudioWorklet + ScriptProcessorNode fallback detection
2. **pcm-player integration** — Best patterns for feeding PCM from WebSocket binary messages, interrupt/destroy lifecycle
3. **react-window dynamic sizing** — Variable height message bubbles with auto-scroll in VariableSizeList
4. **Vite proxy configuration** — Dev server proxy to backend (WebSocket + REST) for local development

### Findings → research.md

---

## Phase 1: Design & Contracts

### Data Model

Primary entities managed in frontend state:

| Entity | Location | Purpose |
|--------|----------|---------|
| Session | SessionContext | REST API session lifecycle (id, status, progress) |
| Message | ConversationContext | Chat transcript entries (role, text, timestamp, final) |
| AudioState | useAudioCapture | Recording state, level, worklet/fallback mode |
| ConnectionState | WebSocketContext | Connected/disconnected/reconnecting |
| Theme | ThemeContext | light/dark/system preference |

### Interface Contracts

1. **REST API** (consumed, not produced):
   - `POST /sessions` → `{ session_id, join_url, status, created_at }`
   - `GET /sessions` → `{ sessions: [...] }`
   - `GET /sessions/:id` → `{ session_id, status, progress, participants }`
   - `GET /sessions/:id/result` → `{ intent_md, state, audit_md }`
   - `DELETE /sessions/:id` → 204

2. **WebSocket Protocol** (see contracts/websocket.md):
   - Client sends: `codec_negotiate`, `ping`, binary audio
   - Server sends: `codec_ack`, `session_ready`, `pong`, `transcript`, `progress`, `intent_preview`, `session_complete`, `error`, `server_shutdown`, binary audio

---

## Phase 2: Implementation Phases

### Phase 2A — Project Scaffolding
- Vite + React + TypeScript project setup
- Tailwind CSS + design tokens + PostCSS
- ESLint + Prettier configuration
- Vitest + Playwright setup
- Package.json with all dependencies
- Dev proxy config (WebSocket + REST → localhost:8080)

### Phase 2B — Layout & Theme
- MainLayout, Header, Footer components
- ThemeContext + ThemeProvider + ThemeToggle
- Design tokens (CSS custom properties, light/dark)
- ErrorBoundary + LoadingSpinner + ErrorBanner
- Keyboard shortcuts (Escape, Ctrl+K)

### Phase 2C — Session Lifecycle
- SessionContext + SessionProvider
- sessionService.ts (REST API calls)
- LandingView (start button, project name input)
- Session state machine (IDLE → CREATING → ... → COMPLETE)
- CompletionView (markdown render, download, new session)

### Phase 2D — WebSocket & Audio
- websocketService.ts (connect, reconnect, heartbeat, message routing)
- WebSocketContext + WebSocketProvider
- useAudioCapture hook (AudioWorklet + ScriptProcessorNode fallback)
- audio-processor.js (AudioWorklet processor file)
- useAudioPlayback hook (pcm-player lifecycle, barge-in destroy)
- ConnectionStatus component

### Phase 2E — Chat UI
- ConversationContext + ConversationProvider
- MessageList (react-window VariableSizeList, auto-scroll)
- Message component (user/agent bubbles, timestamps)
- ControlPanel (MicButton, AudioMeter, EndSessionButton)
- TextInput fallback (shown when mic unavailable)
- ActiveSessionView (orchestrates chat + controls)

### Phase 2F — Progress & Integration
- ProgressPanel sidebar (sections, alignment meter, proposal rounds)
- Intent preview (live markdown during session)
- Wire all contexts together in App.tsx
- Full E2E flow: start → talk → complete → download

### Phase 2G — Testing & Polish
- Unit tests for hooks (useAudioCapture, useSession, useWebSocket)
- Component tests for key views (Landing, Active, Completion)
- E2E tests with Playwright (mock WebSocket)
- Cross-browser verification (Chrome, Firefox, Safari)
- Bundle size audit (<200KB gzipped)
- Accessibility pass (focus management, ARIA labels, screen reader)

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| AudioWorklet not supported in older Safari | Medium | ScriptProcessorNode fallback auto-detected |
| pcm-player library unmaintained | Low | Simple library, easy to inline/fork if needed |
| WebSocket binary frame ordering | Medium | Sequence numbers in protocol if needed (server-side) |
| Large transcript causes jank | Low | react-window virtualization handles 1000+ messages |
| Backend not ready for all message types | Medium | Frontend handles unknown message types gracefully (ignore + log) |
