# Data Model: WebSocket Audio Server

## Entities

### Session

Represents a single authenticated client-to-server audio connection.

| Field | Type | Description |
|-------|------|-------------|
| id | str (UUID4) | Unique session identifier, generated on connect |
| user_id | str | Extracted from ALB `x-amzn-oidc-identity` header |
| state | SessionState | Current lifecycle state |
| connected_at | datetime | UTC timestamp of WebSocket upgrade |
| last_activity | datetime | UTC timestamp of last received frame (text or binary) |
| codec | AudioCodec | Negotiated audio parameters |

### SessionState (Enum)

```
CONNECTING → STREAMING → DISCONNECTING → CLOSED
```

| State | Entry Condition | Exit Condition |
|-------|----------------|----------------|
| CONNECTING | WebSocket upgrade accepted | Codec negotiation complete |
| STREAMING | Codec acknowledged | Client close / timeout / shutdown |
| DISCONNECTING | Close initiated (graceful or forced) | Cleanup complete |
| CLOSED | All resources released | Session removed from registry |

**Transitions**:
- CONNECTING → STREAMING: Server sends `codec_ack`
- CONNECTING → CLOSED: Codec rejected or negotiation timeout (5s)
- STREAMING → DISCONNECTING: Client close frame, 30s inactivity timeout, or server shutdown signal
- DISCONNECTING → CLOSED: Buffers flushed, upstream connections closed

### AudioCodec (Value Object)

| Field | Type | Constraint |
|-------|------|-----------|
| format | str | Must be "pcm" (MVP) |
| sample_rate | int | Must be 16000 Hz |
| bit_depth | int | Must be 16 |
| channels | int | Must be 1 (mono) |

### HealthStatus (Read-only View)

| Field | Type | Description |
|-------|------|-------------|
| status | str | "ready", "draining", or "at_capacity" |
| active_sessions | int | Current count of sessions in CONNECTING or STREAMING state |
| uptime_seconds | float | Time since server startup |

## Relationships

```
Server 1 ──── * Session
Session 1 ──── 1 AudioCodec
Session 1 ──── 1 SessionState
```

## Validation Rules

- Session ID must be unique across all active sessions
- User ID is trusted (injected by ALB, not client-supplied)
- Codec negotiation must complete within 5 seconds of connection or session is closed
- Only one active session per `(user_id)` is allowed at a time (new connection replaces old)
- `last_activity` is updated on every received frame (binary or text)
- Sessions in CLOSED state are immediately removed from the registry

## Storage

In-memory only (MVP). No persistent storage for session state.
- `Dict[str, Session]` keyed by session ID
- Background cleanup task scans every 10 seconds for stale sessions
- All state is lost on server restart (acceptable for MVP — clients reconnect)
