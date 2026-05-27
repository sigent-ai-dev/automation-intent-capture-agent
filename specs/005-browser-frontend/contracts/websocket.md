# WebSocket Protocol Contract

**Endpoint**: `ws://{host}:{port}/ws/audio`  
**Subprotocol**: None (raw WebSocket)  
**Frame types**: Text (JSON control messages) + Binary (PCM audio)

---

## Connection Sequence

```
Client                              Server
  │                                    │
  │──── WebSocket CONNECT ────────────→│
  │←─── 101 Switching Protocols ──────│
  │                                    │
  │──── codec_negotiate ──────────────→│
  │←─── codec_ack ────────────────────│
  │←─── session_ready ────────────────│
  │                                    │
  │ ═══ ACTIVE SESSION ═══════════════ │
  │                                    │
  │──── binary (PCM audio) ──────────→│
  │←─── binary (PCM audio) ──────────│
  │←─── transcript ───────────────────│
  │←─── progress ─────────────────────│
  │                                    │
  │──── ping ─────────────────────────→│
  │←─── pong ─────────────────────────│
  │                                    │
  │←─── session_complete ─────────────│
  │──── close ────────────────────────→│
```

---

## Client → Server Messages

### codec_negotiate

Sent immediately after WebSocket connection opens.

```json
{
  "type": "codec_negotiate",
  "codec": "pcm",
  "sample_rate": 16000,
  "bit_depth": 16,
  "channels": 1
}
```

### ping

Heartbeat sent every 30 seconds to keep connection alive.

```json
{
  "type": "ping"
}
```

### Binary Audio Frame

Raw PCM audio data. Int16 little-endian, 16kHz, mono.  
Chunk size: 1600 bytes (50ms of audio per frame).

No JSON wrapper — sent as WebSocket binary frame directly.

---

## Server → Client Messages

### codec_ack

Confirms codec negotiation. Marks session as ready for audio.

```json
{
  "type": "codec_ack",
  "session_id": "uuid-string",
  "codec": "pcm",
  "sample_rate": 16000,
  "bit_depth": 16,
  "channels": 1
}
```

### session_ready

Sent after codec_ack. Session is fully initialized.

```json
{
  "type": "session_ready",
  "session_id": "uuid-string",
  "user_id": "anonymous",
  "timestamp": 1716825600000
}
```

### pong

Response to client ping.

```json
{
  "type": "pong",
  "timestamp": 1716825600000
}
```

### transcript

Real-time speech-to-text transcription.

```json
{
  "type": "transcript",
  "role": "user",
  "text": "I want to build a CLI tool for...",
  "final": true
}
```

- `role`: `"user"` (user speech) or `"agent"` (agent response text)
- `final`: `false` for interim (partial) transcripts, `true` for confirmed final text
- Interim transcripts update in-place (same message bubble); final transcripts are appended

### progress

Session progress update. Sent whenever the agent completes or updates a section.

```json
{
  "type": "progress",
  "sections_covered": ["Context", "Problem Statement"],
  "proposal_rounds": 2,
  "alignment_reached": false
}
```

### intent_preview

Live preview of the intent document being built. Sent periodically during active capture.

```json
{
  "type": "intent_preview",
  "markdown": "# Intent: My Project\n\n## Context\n..."
}
```

### session_complete

Signals that the capture session has finished. Frontend should transition to COMPLETING state and fetch the result via REST API.

```json
{
  "type": "session_complete"
}
```

### error

Error during session.

```json
{
  "type": "error",
  "message": "Human-readable error description",
  "code": "INTERNAL_ERROR"
}
```

Known error codes: `INTERNAL_ERROR`, `CODEC_UNSUPPORTED`, `SESSION_EXPIRED`, `RATE_LIMITED`

### server_shutdown

Graceful shutdown notification. Frontend should prepare for disconnect and auto-reconnect after drain period.

```json
{
  "type": "server_shutdown",
  "drain_seconds": 30,
  "message": "Server is shutting down for deployment"
}
```

### Binary Audio Frame (Server → Client)

Agent speech audio. PCM Int16 little-endian, 24kHz, mono.  
Fed directly to pcm-player for playback.

No JSON wrapper — received as WebSocket binary frame.

---

## Reconnection Protocol

1. WebSocket closes unexpectedly (code != 1000)
2. Frontend waits `2^attempt` seconds (1s, 2s, 4s, 8s, 16s) — max 5 attempts
3. Reconnects to same URL
4. Re-sends `codec_negotiate`
5. Server recognizes session (from connection metadata or session_id param) and resumes
6. Frontend continues from current state — no transcript loss

If all 5 attempts fail → transition to FAILED state with "Connection lost" error.

---

## Message Size Limits

| Direction | Type | Max Size |
|-----------|------|----------|
| Client → Server | Binary (audio) | 1,600 bytes per frame |
| Client → Server | Text (JSON) | 1 KB |
| Server → Client | Binary (audio) | 4,800 bytes per frame |
| Server → Client | Text (JSON) | 64 KB (intent_preview can be large) |
