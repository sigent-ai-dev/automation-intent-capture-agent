# Spec: Browser Frontend with Web Audio API

**Issue**: #5  
**Status**: Draft  
**Branch**: `5-browser-frontend`

---

## 1. Overview

Single-page voice capture interface for the Intent Capture Agent. Users start a session, speak with the agent via microphone, see real-time transcripts, monitor progress through intent sections, and receive a final intent summary on completion.

**Reference implementation**: `trainline-voice-poc/frontend/` — reuse the same tech stack, styling approach, component architecture, and real-time audio patterns.

---

## Clarifications

### Session 2026-05-27

- Q: When the user denies microphone permission, what should the UI do? → A: Offer text-input fallback so user can type instead of speaking
- Q: Which audio capture API should the frontend use? → A: AudioWorklet (primary) with ScriptProcessorNode fallback for older browsers
- Q: How should barge-in (user speaks while agent audio is playing) be handled? → A: Immediately stop agent playback and begin capturing user speech
- Q: What is the acceptable audio-to-audio round-trip latency target? → A: Under 2 seconds (show "thinking" indicator during gap)
- Q: When the WebSocket drops mid-session, what happens to session state? → A: Auto-reconnect to same session, resume with existing progress (transcript stays, audio restarts)

---

## 2. Tech Stack

| Concern | Choice | Rationale (matching trainline-voice-poc) |
|---------|--------|------------------------------------------|
| Framework | React 18 + TypeScript (strict) | Same as POC |
| Build | Vite 5 | Same as POC |
| Styling | Tailwind CSS 3.4 + CSS custom properties | Same as POC |
| Audio playback | `pcm-player` (Int16, mono, 24kHz) | Same as POC |
| Audio capture | Web Audio API (AudioWorklet primary, ScriptProcessorNode fallback) | Upgraded from POC — AudioWorklet is modern, non-blocking |
| WebSocket | Custom service class with reconnection | Same pattern as POC |
| Virtualization | `react-window` (VariableSizeList) | Same as POC |
| Date formatting | `date-fns` | Same as POC |
| Testing | Vitest + React Testing Library + Playwright | Same as POC |
| Auth | None (deferred to #10) | Out of scope per issue |

---

## 3. Comparison: Trainline POC vs Intent Capture Agent

### 3.1 What we KEEP (identical patterns)

| Area | Trainline POC | Carry Forward |
|------|---------------|---------------|
| **Project structure** | `frontend/src/{components,hooks,services,contexts,types,utils,styles,config}` | Yes — same directory layout |
| **Theme system** | CSS custom properties + `[data-theme="dark"]` + ThemeContext + ThemeProvider | Yes — same approach, different brand colors |
| **Audio capture** | `useAudioCapture` hook → ScriptProcessorNode → Int16 → base64 → WebSocket | Yes — same pipeline, upgraded to AudioWorklet with ScriptProcessorNode fallback |
| **Audio playback** | PCM player (24kHz, Int16, mono) fed from WebSocket `audio_output` messages | Yes — same player config |
| **WebSocket service** | Class with reconnection (max 5 attempts, 3s delay), heartbeat (30s) | Yes — same pattern, different URL/protocol |
| **Message list** | Virtualized with `react-window`, auto-scroll, user/agent bubbles | Yes |
| **Control panel** | Circular mic button (green→red), audio level meter, connection dot | Yes — same visual |
| **Dark/light mode** | Toggle in header, persisted to localStorage, system preference detection | Yes |
| **Keyboard shortcuts** | Escape, Ctrl+K, Ctrl+Shift+C | Yes |
| **Error boundary** | React ErrorBoundary wrapping app | Yes |
| **Loading spinner** | Animated SVG spinner component | Yes |

### 3.2 What we CHANGE

| Area | Trainline POC | Intent Capture Agent | Reason |
|------|---------------|---------------------|--------|
| **Branding** | Trainline green (#00D46A), navy (#1E1E2E), "Trainline Voice Agent" | Neutral brand (indigo #6366F1, slate), "Intent Capture" | Not Trainline-branded |
| **Auth** | AWS Cognito via Amplify (login form, new-password flow) | None (auth disabled, deferred to #10) | Out of scope |
| **WebSocket URL** | API Gateway `wss://...execute-api.../ws?token=...` | Direct to service `ws://host:8080/ws/audio` | Different backend architecture |
| **WebSocket protocol** | Custom messages (`audio_output`, `text_output`, `interrupt`, `tool_use`, `tool_result`) | Our protocol: `codec_negotiate` → `codec_ack` → `session_ready` → binary audio frames | Different server |
| **Tool execution panel** | Right sidebar showing tool executions (ToolExecutionCard, WorkflowProgress) | **Session progress panel** — shows sections covered, alignment score, proposal rounds | Different domain |
| **Message highlighting** | Booking refs, currency, emails, phone numbers | Intent sections, key decisions, action items | Different content |
| **Phonetic read-back** | NATO phonetic alphabet for booking refs | Not needed | Domain-specific to Trainline |
| **Session lifecycle** | No explicit session management — just connect and talk | REST API: `POST /sessions` → join → `DELETE /sessions/:id` → `GET /sessions/:id/result` | Our session API |
| **Final output** | No completion view | Intent summary view: renders `intent_md` as markdown when session completes | Core feature |
| **Runtime config** | `window.APP_CONFIG` injected at deploy | Same pattern (`public/config.js`) | Keep |

### 3.3 What we ADD (new features)

| Feature | Description |
|---------|-------------|
| **Session creation flow** | "Start Capture" → calls `POST /sessions` → receives `join_url` → connects WebSocket |
| **Progress panel** | Real-time display of sections covered (Context, Problem, Constraints, Success Criteria, etc.) with confidence indicators |
| **Intent preview** | Live markdown preview of the intent being captured (updates as agent confirms sections) |
| **Completion view** | Full rendered `intent.md` + audit trail + download button when session status = `complete` |
| **End session button** | Triggers `DELETE /sessions/:id` to stop capture gracefully |

### 3.4 What we REMOVE (not needed)

| Trainline Feature | Reason to Remove |
|-------------------|-----------------|
| Auth (LoginForm, NewPasswordRequired, AuthContext, authService) | Deferred to #10 |
| Tool execution panel & cards | Replace with progress panel |
| Message highlighting (booking refs, currency) | Different domain |
| Phonetic text display | Not applicable |
| `@aws-amplify/auth` dependency | No auth |
| Export/download conversation | Keep export but simplify to intent.md download |

---

## 4. Component Architecture

```
App.tsx
├── ErrorBoundary
└── ThemeContextProvider
    └── ThemeProvider
        └── WebSocketProvider
            └── ConversationProvider
                └── SessionProvider        ← NEW (session REST API state)
                    └── MainLayout
                        ├── Header
                        │   ├── Logo + Title
                        │   ├── ConnectionStatus
                        │   ├── ThemeToggle
                        │   └── ShortcutHelp button
                        ├── ContentArea
                        │   ├── LandingView          ← NEW (pre-session)
                        │   │   └── StartCaptureButton
                        │   ├── ActiveSessionView    ← NEW (during session)
                        │   │   ├── MessageList (virtualized)
                        │   │   │   └── Message (user/agent bubbles)
                        │   │   ├── ProgressPanel     ← NEW (sidebar)
                        │   │   │   ├── SectionsList
                        │   │   │   └── AlignmentMeter
                        │   │   └── ControlPanel
                        │   │       ├── MicButton
                        │   │       ├── AudioMeter
                        │   │       ├── TextInput         ← NEW (fallback when mic denied)
                        │   │       └── EndSessionButton  ← NEW
                        │   └── CompletionView       ← NEW (post-session)
                        │       ├── IntentMarkdownRender
                        │       ├── AuditTrail
                        │       └── DownloadButton
                        └── Footer
```

---

## 5. Session Lifecycle (State Machine)

```
IDLE → CREATING → CONNECTING → NEGOTIATING → ACTIVE → COMPLETING → COMPLETE
  ↑                                              │
  └──────────── CANCELLED ←──────────────────────┘
                    ↑
               FAILED (any state)
```

| State | UI | Actions |
|-------|----|---------|
| IDLE | LandingView with "Start Capture" button | User clicks start |
| CREATING | Button shows spinner, "Creating session..." | `POST /sessions` |
| CONNECTING | "Connecting to voice server..." | WebSocket connect to `join_url` |
| NEGOTIATING | "Negotiating audio..." | Send `codec_negotiate`, wait for `codec_ack` + `session_ready` |
| ACTIVE | Full chat UI + mic controls + progress panel | Streaming audio, showing transcripts |
| COMPLETING | "Finalizing intent..." with spinner | Agent wrapping up, `GET /sessions/:id` polling |
| COMPLETE | CompletionView with rendered intent.md | `GET /sessions/:id/result` |
| CANCELLED | "Session ended" message, back to IDLE | After `DELETE /sessions/:id` |
| FAILED | Error banner with retry button | Any unrecoverable error |

---

## 6. WebSocket Protocol Integration

### 6.1 Connection

```
1. POST /sessions { project_name } → { session_id, join_url, status }
2. WebSocket connect to: ws://{host}/ws/audio?session_id={session_id}
3. Send: { type: "codec_negotiate", codec: "pcm", sample_rate: 16000, bit_depth: 16, channels: 1 }
4. Recv: { type: "codec_ack", session_id, codec, sample_rate, bit_depth, channels }
5. Recv: { type: "session_ready", session_id, user_id, timestamp }
6. → ACTIVE state: begin streaming audio
```

### 6.2 Active Session Messages

| Direction | Type | Payload |
|-----------|------|---------|
| Client → Server | binary | Raw PCM audio frames (Int16, 16kHz, mono) |
| Client → Server | `{ type: "ping" }` | Heartbeat (every 30s) |
| Server → Client | `{ type: "pong" }` | Heartbeat response |
| Server → Client | binary | Agent audio response (PCM Int16, 24kHz, mono) |
| Server → Client | `{ type: "transcript", role: "user"\|"agent", text, final: bool }` | Real-time transcript |
| Server → Client | `{ type: "progress", sections_covered: [...], proposal_rounds, alignment_reached }` | Session progress update |
| Server → Client | `{ type: "intent_preview", markdown }` | Live intent preview |
| Server → Client | `{ type: "session_complete" }` | Capture finished |
| Server → Client | `{ type: "error", message, code }` | Error |
| Server → Client | `{ type: "server_shutdown", drain_seconds, message }` | Graceful shutdown |

### 6.3 Disconnection / Reconnect

- On unexpected close: auto-reconnect to same session (max 5 attempts, exponential backoff starting at 1s). Transcript and progress are preserved; audio streaming resumes from current point.
- On `server_shutdown`: show banner "Server restarting, reconnecting...", auto-reconnect after `drain_seconds`
- On auth error (future): redirect to login
- Session state lives server-side — reconnection resumes seamlessly without data loss

### 6.4 Barge-In Behavior

- When user begins speaking while agent audio is playing: immediately stop PCM playback, destroy player instance, begin capturing user audio
- Frontend sends no explicit interrupt signal — the server detects new user audio and stops generating agent audio
- Clear any buffered agent audio frames to prevent stale playback after interrupt

---

## 7. Styling & Design Tokens

### 7.1 Color Palette (Intent Capture brand)

| Token | Light | Dark |
|-------|-------|------|
| `--color-background` | #FFFFFF | #0F172A |
| `--color-surface` | #F8FAFC | #1E293B |
| `--color-text-primary` | #1E293B | #F1F5F9 |
| `--color-text-secondary` | #64748B | #CBD5E1 |
| `--color-primary` | #6366F1 (indigo) | #818CF8 |
| `--color-primary-hover` | #4F46E5 | #6366F1 |
| `--color-user-bubble` | #6366F1 | #4F46E5 |
| `--color-agent-bubble` | #F1F5F9 | #334155 |
| `--color-success` | #10B981 | #34D399 |
| `--color-error` | #EF4444 | #F87171 |
| `--color-warning` | #F59E0B | #FBBF24 |
| `--color-border` | #E2E8F0 | #334155 |
| `--color-mic-active` | #EF4444 | #DC2626 |
| `--color-mic-inactive` | #10B981 | #059669 |

### 7.2 Typography

```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', monospace;
--font-size-xs: 0.75rem;
--font-size-sm: 0.875rem;
--font-size-base: 1rem;
--font-size-lg: 1.125rem;
--font-size-xl: 1.25rem;
--font-size-2xl: 1.5rem;
```

### 7.3 Spacing & Layout

```css
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
--radius-sm: 0.375rem;
--radius-md: 0.5rem;
--radius-lg: 0.75rem;
--radius-full: 9999px;
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px rgba(0,0,0,0.07);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
```

---

## 8. Key Components (detailed)

### 8.1 MicButton

Identical behavior to trainline POC:
- **Idle**: Green circle (56x56px), microphone SVG icon, tooltip "Press to speak"
- **Recording**: Red circle, stop icon, pulsing ring animation, tooltip "Recording..."
- **Disabled**: Gray, when not connected or session not active
- Click toggles recording on/off
- Audio level meter (horizontal bar) shows real-time input level

### 8.2 ProgressPanel (NEW — replaces Tool Execution Panel)

Right sidebar (collapsible on mobile), shows:
- **Sections checklist**: Context, Problem Statement, Constraints, Success Criteria, Stakeholders, Timeline — each with ✓/○ icon
- **Proposal rounds**: Counter (e.g., "Round 2 of 3")
- **Alignment meter**: Progress bar showing section completion percentage (sections_covered.length / total_sections * 100). When `alignment_reached` = true, bar shows 100% with "Complete" styling.
- **Status badge**: "Eliciting" / "Proposing" / "Aligning" / "Complete"

Updates in real-time from `progress` WebSocket messages.

### 8.3 CompletionView (NEW)

Shown when session status = `complete`:
- Full rendered `intent.md` content (using a markdown renderer like `react-markdown`)
- Collapsible "Audit Trail" section showing the conversation summary
- "Download intent.md" button
- "Start New Session" button to return to IDLE

### 8.4 LandingView (NEW)

Pre-session screen:
- Project name input field (optional, defaults to directory name)
- "Start Capture" button (large, prominent, primary color)
- Brief description: "Start a voice conversation to capture your project intent"
- Previous sessions list (from `GET /sessions`) — if any exist

---

## 9. Audio Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Input sample rate | 16,000 Hz | `VITE_INPUT_SAMPLE_RATE` |
| Input bit depth | 16 | Fixed |
| Input channels | 1 (mono) | Fixed |
| Output sample rate | 24,000 Hz | `VITE_OUTPUT_SAMPLE_RATE` |
| Output codec | Int16 PCM | Fixed |
| Chunk size | 1,600 bytes | `VITE_AUDIO_CHUNK_SIZE` |
| Buffer size | 4,096 samples | Fixed |
| PCM flush time | 100ms | Fixed |

---

## 10. Environment Configuration

```env
# .env.development
VITE_WEBSOCKET_URL=ws://localhost:8080/ws/audio
VITE_API_URL=http://localhost:8080
VITE_INPUT_SAMPLE_RATE=16000
VITE_OUTPUT_SAMPLE_RATE=24000
VITE_AUDIO_CHUNK_SIZE=1600
VITE_ENABLE_AUTH=false
```

```js
// public/config.js (runtime override for production)
window.APP_CONFIG = {
  WEBSOCKET_URL: '',   // injected at deploy
  API_URL: '',         // injected at deploy
  ENABLE_AUTH: false,
};
```

---

## 11. File Structure

```
frontend/
├── index.html
├── public/
│   ├── config.js
│   └── logo.svg
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── Message.tsx
│   │   ├── controls/
│   │   │   ├── ControlPanel.tsx
│   │   │   ├── ControlPanel.css
│   │   │   ├── MicButton.tsx
│   │   │   ├── AudioMeter.tsx
│   │   │   ├── TextInput.tsx
│   │   │   └── EndSessionButton.tsx
│   │   ├── session/
│   │   │   ├── LandingView.tsx
│   │   │   ├── ActiveSessionView.tsx
│   │   │   ├── CompletionView.tsx
│   │   │   └── ProgressPanel.tsx
│   │   ├── connection/
│   │   │   └── ConnectionStatus.tsx
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Header.css
│   │   │   ├── MainLayout.tsx
│   │   │   ├── MainLayout.css
│   │   │   └── ThemeToggle.tsx
│   │   └── common/
│   │       ├── ErrorBoundary.tsx
│   │       ├── ErrorBanner.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ShortcutHelp.tsx
│   ├── contexts/
│   │   ├── ThemeContext.tsx
│   │   ├── WebSocketContext.tsx
│   │   ├── ConversationContext.tsx
│   │   └── SessionContext.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useAudioCapture.ts
│   │   ├── useAudioPlayback.ts
│   │   ├── useSession.ts
│   │   ├── useConnectionMonitor.ts
│   │   ├── useKeyboardShortcuts.ts
│   │   └── useVirtualizedMessages.ts
│   ├── services/
│   │   ├── websocketService.ts
│   │   ├── audioService.ts
│   │   └── sessionService.ts
│   ├── types/
│   │   ├── session.ts
│   │   ├── conversation.ts
│   │   ├── websocket.ts
│   │   ├── audio.ts
│   │   └── theme.ts
│   ├── utils/
│   │   ├── audioUtils.ts
│   │   ├── base64Utils.ts
│   │   └── formatters.ts
│   ├── config/
│   │   └── constants.ts
│   └── styles/
│       ├── globals.css
│       ├── design-tokens.css
│       └── components.css
├── tests/
│   └── e2e/
├── vite.config.ts
├── vitest.config.ts
├── tailwind.config.js
├── tsconfig.json
├── postcss.config.js
├── .eslintrc.cjs
├── .prettierrc
├── .env.development
├── .env.example
└── package.json
```

---

## 12. Acceptance Criteria Mapping

| AC from Issue #5 | Spec Section | Implementation |
|------------------|-------------|----------------|
| Single-page web app with "Start Capture" button | §4, §8.4 | `LandingView.tsx` with StartCaptureButton |
| Web Audio API captures mic, streams via WebSocket | §6, §9 | `useAudioCapture` hook → `websocketService.sendAudio()` |
| Receives and plays agent response audio | §6.2 | PCM player in `ChatContainer`, fed from WebSocket binary messages |
| Visual indicator: recording, speaking, processing | §8.1, §5 | MicButton states, ConnectionStatus, state badges |
| Real-time transcript display | §6.2, §8 | `MessageList` + `Message` components, fed from `transcript` messages |
| Session progress (sections covered, confidence) | §8.2 | `ProgressPanel` sidebar, fed from `progress` messages |
| "End Session" button | §8, §5 | `EndSessionButton` → `DELETE /sessions/:id` |
| Final summary showing captured intent | §8.3 | `CompletionView` rendering `intent_md` from `GET /sessions/:id/result` |
| Works in Chrome, Firefox, Safari | §2 | Standard Web Audio API + WebSocket — tested in Playwright |

---

## 13. Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| react | ^18.2 | UI framework |
| react-dom | ^18.2 | DOM rendering |
| typescript | ^5.3 | Type safety |
| vite | ^5.0 | Build tool |
| tailwindcss | ^3.4 | Utility CSS |
| postcss | ^8 | CSS processing |
| autoprefixer | ^10 | Vendor prefixes |
| pcm-player | ^0.0.18 | Audio playback |
| react-window | ^1.8 | Virtual scrolling |
| react-markdown | ^9 | Render intent.md |
| date-fns | ^4.1 | Date formatting |
| vitest | ^1 | Unit tests |
| @testing-library/react | ^14 | Component tests |
| playwright | ^1.40 | E2E tests |
| eslint | ^8 | Linting |
| prettier | ^3 | Formatting |

---

## 14. Non-Functional Requirements

| Metric | Target |
|--------|--------|
| Audio round-trip latency (user stops → agent plays) | < 2 seconds (includes server inference time) |
| Barge-in response (user speaks → agent playback stops) | < 800ms (frontend-only, per constitution) |
| UI frame rate during audio streaming | 60fps (no jank from audio processing — AudioWorklet ensures this) |
| WebSocket reconnect time | < 5 seconds (first attempt at 1s) |
| Bundle size (gzipped) | < 200KB (excluding audio worklet) |

A "thinking" indicator (animated dots or pulse) MUST display during the latency gap between user speech end and agent response start.

---

## 15. Edge Cases & Error Handling

| Scenario | Behavior |
|----------|----------|
| Mic permission denied | Show error banner with instructions; reveal text input field as fallback for typed conversation |
| Mic permission revoked mid-session | Stop recording, show warning, offer text fallback |
| Browser lacks AudioWorklet support | Fall back to ScriptProcessorNode automatically (detected at capture init) |
| WebSocket drops mid-speech | Auto-reconnect to same session; transcript preserved; show brief "Reconnecting..." toast |
| Server returns 5xx on session create | Show error banner with "Retry" button |
| Session not found (404) on reconnect | Transition to FAILED state, offer "Start New Session" |
| User navigates away mid-session | `beforeunload` warning: "Voice session in progress — leave?" |
| No audio output device | Transcript-only mode; disable audio playback, show all agent responses as text |

---

## 16. Out of Scope (explicit)

- Authentication / login flow (issue #10)
- Mobile-optimized layout
- Offline support
- Tool execution display (no tools in MVP voice flow)
- Message export (keep download intent.md only)
- Message persistence to localStorage (sessions are short-lived)
