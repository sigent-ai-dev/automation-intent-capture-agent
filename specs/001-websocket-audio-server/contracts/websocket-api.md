# WebSocket API Contract

## Connection

**Endpoint**: `wss://{host}/ws/audio`

**Authentication**: ALB Cognito OIDC (transparent to client — redirect flow before upgrade)

**Upgrade**: Standard WebSocket upgrade. Server accepts if authenticated.

---

## Frame Types

| Direction | Frame Type | Content |
|-----------|-----------|---------|
| Client → Server | Binary | Raw PCM audio bytes |
| Server → Client | Binary | Raw PCM audio bytes |
| Client → Server | Text | JSON control message |
| Server → Client | Text | JSON control message |

---

## Control Messages (JSON Text Frames)

### Client → Server

#### codec_negotiate

Sent immediately after connection upgrade. Must be the first message.

```json
{
  "type": "codec_negotiate",
  "codec": "pcm",
  "sample_rate": 16000,
  "bit_depth": 16,
  "channels": 1
}
```

#### ping

Heartbeat to keep connection alive.

```json
{
  "type": "ping"
}
```

---

### Server → Client

#### codec_ack

Confirms codec negotiation. Session enters STREAMING state.

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

#### codec_reject

Codec not supported. Connection will be closed.

```json
{
  "type": "codec_reject",
  "reason": "Unsupported codec: opus. Supported: pcm (16-bit, 16kHz, mono)"
}
```

#### session_ready

Sent after codec_ack to confirm streaming can begin.

```json
{
  "type": "session_ready",
  "session_id": "uuid-string",
  "user_id": "cognito-sub",
  "timestamp": 1716700800000
}
```

#### pong

Response to client ping.

```json
{
  "type": "pong",
  "timestamp": 1716700800000
}
```

#### error

Non-fatal error during session.

```json
{
  "type": "error",
  "message": "Description of what went wrong",
  "code": "INVALID_FRAME"
}
```

**Error codes**:
- `INVALID_FRAME`: Malformed or unexpected frame
- `CODEC_TIMEOUT`: Codec negotiation not completed within 5 seconds
- `SESSION_TIMEOUT`: No activity for 30 seconds
- `INTERNAL_ERROR`: Unexpected server error

#### server_shutdown

Server is shutting down. Client should reconnect to another instance.

```json
{
  "type": "server_shutdown",
  "drain_seconds": 30,
  "message": "Server is shutting down for deployment"
}
```

---

## Connection Lifecycle

```
1. Client opens WebSocket to /ws/audio (ALB authenticates via Cognito)
2. Server accepts upgrade → state: CONNECTING
3. Client sends codec_negotiate (text frame)
4. Server responds with codec_ack or codec_reject
5. If ack → state: STREAMING, server sends session_ready
6. Client sends raw PCM binary frames (audio from mic)
7. Server sends raw PCM binary frames (audio response)
8. Client sends ping periodically (recommended: every 15s)
9. Either side sends WebSocket close frame → state: DISCONNECTING
10. Server cleans up → state: CLOSED
```

---

## Audio Frame Specification

| Property | Value |
|----------|-------|
| Format | PCM (raw, uncompressed) |
| Sample rate | 16,000 Hz |
| Bit depth | 16-bit signed integer (little-endian) |
| Channels | 1 (mono) |
| Frame size | Variable (recommended: 8192 bytes = 256ms) |
| Byte order | Little-endian |

---

## HTTP Endpoints

### GET /health/live

Liveness check. Returns 200 if process is running.

**Response** (200):
```json
{
  "status": "alive"
}
```

### GET /health/ready

Readiness check. Returns 200 if accepting new sessions.

**Response** (200):
```json
{
  "status": "ready",
  "active_sessions": 12,
  "uptime_seconds": 3600.5
}
```

**Response** (503 — draining or at capacity):
```json
{
  "status": "draining",
  "active_sessions": 45,
  "uptime_seconds": 7200.0
}
```
