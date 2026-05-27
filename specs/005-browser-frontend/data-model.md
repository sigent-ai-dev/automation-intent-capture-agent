# Data Model: Browser Frontend

## Frontend State Entities

### Session

Managed by `SessionContext`. Represents the capture session lifecycle.

```typescript
interface Session {
  id: string;                    // UUID from POST /sessions
  projectName: string;           // User-provided or "unnamed"
  status: SessionStatus;         // State machine state
  joinUrl: string;               // WebSocket join URL
  createdAt: string;             // ISO 8601
  progress: SessionProgress;     // Live progress from server
  result: SessionResult | null;  // Available when status = COMPLETE
  error: string | null;          // Set on FAILED state
}

type SessionStatus =
  | 'idle'
  | 'creating'
  | 'connecting'
  | 'negotiating'
  | 'active'
  | 'completing'
  | 'complete'
  | 'cancelled'
  | 'failed';

interface SessionProgress {
  sectionsCovered: string[];     // e.g. ["Context", "Problem Statement"]
  proposalRounds: number;
  alignmentReached: boolean;
}

interface SessionResult {
  intentMd: string;              // Full intent.md content
  state: Record<string, unknown>;
  auditMd: string;               // Audit trail markdown
}
```

### Message

Managed by `ConversationContext`. Transcript entries from the voice conversation.

```typescript
interface Message {
  id: string;                    // Client-generated UUID
  role: 'user' | 'agent';
  text: string;
  timestamp: Date;
  isFinal: boolean;              // false = interim transcript, true = confirmed
}
```

### AudioState

Managed by `useAudioCapture` hook. Not stored in context — local to the hook.

```typescript
interface AudioState {
  isRecording: boolean;
  level: number;                 // 0-1 normalized input level
  captureMode: 'worklet' | 'script-processor' | 'unavailable';
  error: string | null;          // "Permission denied", etc.
}
```

### ConnectionState

Managed by `WebSocketContext`.

```typescript
interface ConnectionState {
  status: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';
  sessionId: string | null;      // From codec_ack
  userId: string | null;         // From session_ready
  reconnectAttempt: number;      // 0 when connected
}
```

### ThemeState

Managed by `ThemeContext`.

```typescript
interface ThemeState {
  mode: 'light' | 'dark' | 'system';
  effective: 'light' | 'dark';   // Resolved from mode + system preference
}
```

## State Transitions

### Session State Machine

```
idle ──[user clicks start]──→ creating
creating ──[POST /sessions 201]──→ connecting
creating ──[POST /sessions fail]──→ failed
connecting ──[WebSocket open]──→ negotiating
connecting ──[WebSocket fail]──→ failed
negotiating ──[codec_ack + session_ready]──→ active
negotiating ──[codec_reject]──→ failed
active ──[session_complete msg]──→ completing
active ──[user clicks end]──→ cancelled
active ──[WebSocket close]──→ connecting (auto-reconnect)
completing ──[GET /result 200]──→ complete
completing ──[GET /result fail]──→ failed
failed ──[user clicks retry]──→ idle
cancelled ──[auto after 2s]──→ idle
complete ──[user clicks new session]──→ idle
```

### Audio State

```
unavailable (mic denied) ──[user grants later]──→ idle (unlikely mid-session)
idle ──[user clicks mic]──→ recording
recording ──[user clicks mic]──→ idle
recording ──[session ends]──→ idle
recording ──[error]──→ unavailable
```

## Persistence

| Data | Storage | Lifetime |
|------|---------|----------|
| Theme preference | localStorage `theme-mode` | Permanent |
| Session state | React context (memory) | Tab lifetime |
| Messages | React context (memory) | Tab lifetime |
| Audio buffers | Web Audio API internal | Frame lifetime |

No data persists across page reloads (sessions are server-side; user reconnects or starts fresh).
