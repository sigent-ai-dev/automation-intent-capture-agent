# Design Document: Voice Streaming End-to-End Fix

**Status**: Draft
**Date**: 2026-05-29
**Author**: AICA Team
**Reference**: Trainline Voice Agent POC (gitlab.aws.dev/sigent/trainline-voice-agent-poc)

## Problem Statement

The voice interface captures audio from the microphone and sends it over WebSocket, but no voice response is heard from the agent. The root cause is a combination of configuration mismatches, incorrect frontend audio handling logic, and missing message handling that together prevent the bidirectional audio pipeline from functioning.

## Architecture (Current — Correct)

```
Browser (Web Audio API) ──► WebSocket ──► FastAPI ──► AudioBridge ──► BidiAgent ──► Nova Sonic
Browser (PCM Player)    ◄── WebSocket ◄── FastAPI ◄── AudioBridge ◄── BidiAgent ◄── Nova Sonic
```

The architecture is sound. The Strands SDK handles the Nova Sonic bidirectional protocol correctly. The issues are in configuration and frontend logic.

## Root Causes

### Issue 1: Audio Sample Rate Mismatch (CRITICAL)

**Location**: `src/voice_server/bidi/agent.py` + `frontend/.env.example`

Nova Sonic outputs audio at **16kHz** by default. The frontend PCM player is configured for **24kHz** (`OUTPUT_SAMPLE_RATE=24000`). This means:
- Audio plays too fast and too high-pitched (1.5x speed)
- Or the PCM player rejects/silently drops the frames

**Fix**: Change frontend to expect 16kHz output, or configure Nova Sonic for 24kHz via `provider_config`.

**Recommended**: Change frontend to 16kHz (simpler, no SDK config changes needed).

### Issue 2: Frontend Discards Agent Audio When Mic Is Active (CRITICAL)

**Location**: `frontend/src/components/controls/ControlPanel.tsx` (lines 33-37)

```typescript
onBinary: (data) => {
  if (isRecordingRef.current) {
    handleBargeIn();  // Destroys the player, discards audio!
  } else {
    feed(data);       // Only feeds audio when NOT recording
  }
}
```

During a voice conversation, the microphone is always active. Every incoming audio frame from the agent triggers `handleBargeIn()` which destroys the player. The agent's response is **never played**.

**Fix**: Always feed incoming audio to the player. Only trigger barge-in when the user is actually speaking (detected via audio energy level exceeding a threshold while agent is speaking).

### Issue 3: Frontend Ignores Voice Lifecycle Messages (HIGH)

**Location**: `frontend/src/types/websocket.ts` + `frontend/src/contexts/SessionContext.tsx`

The `ServerMessage` type does not include:
- `agent_speaking` — agent has started responding
- `agent_done` — agent response complete
- `barge_in_ack` — interruption acknowledged
- `voice_timeout` — silence timeout
- `voice_reconnecting` / `voice_reconnected` — reconnection lifecycle

Without these, the frontend cannot track conversation state properly.

**Fix**: Add message types and handle them in session context. Use `isAgentSpeaking` state to drive barge-in logic.

### Issue 4: `LOCAL_MODE` Gate Prevents Voice in Development (MEDIUM)

**Location**: `src/voice_server/ws/handler.py` (line 58)

```python
if not settings.local_mode:
    bridge = AudioBridge(...)
```

When running locally with `LOCAL_MODE=true`, no AudioBridge is created. Audio goes nowhere. Developers must run with `LOCAL_MODE=false` and valid AWS credentials to test voice.

**Fix**: Document this clearly. Optionally, add a mock/echo bridge for local development that plays back captured audio.

### Issue 5: BargeInDetector Exists But Is Unused (LOW)

**Location**: `src/voice_server/bidi/barge_in.py`

The energy-threshold barge-in detector is implemented but not wired into the stream loop. Currently relies entirely on Nova Sonic's server-side detection (which works but is slower — doesn't meet the 800ms target in the constitution).

**Fix**: Wire the detector into `_handle_binary_frame` to send early interruption signals.

## Proposed Solution

### Phase A: Make Voice Work (Critical Path)

1. **Fix sample rate** — Change `VITE_OUTPUT_SAMPLE_RATE` to `16000` in frontend config
2. **Fix audio playback logic** — Always feed agent audio to player; use energy-based barge-in detection instead of `isRecording` flag
3. **Add voice lifecycle messages** — Extend `ServerMessage` type, handle `agent_speaking`/`agent_done` in session context
4. **Track `isAgentSpeaking` state** — Use it to decide when barge-in is appropriate

### Phase B: Developer Experience

5. **Document LOCAL_MODE voice requirements** — Add to quickstart
6. **Consider echo bridge for local dev** — Optional mock that echoes audio back

### Phase C: Performance (Constitution Target: <800ms)

7. **Wire BargeInDetector** — Client-side energy detection for faster interruption
8. **Optimize audio chunking** — Ensure 50ms chunks are sent without buffering delays

## Audio Format Specification

| Direction | Format | Sample Rate | Bit Depth | Channels | Chunk Size |
|-----------|--------|-------------|-----------|----------|------------|
| User → Nova Sonic | PCM | 16,000 Hz | 16-bit signed LE | 1 (mono) | 1600 bytes (50ms) |
| Nova Sonic → User | PCM | 16,000 Hz | 16-bit signed LE | 1 (mono) | Variable |

## WebSocket Protocol (Full)

### Client → Server
| Type | Format | Purpose |
|------|--------|---------|
| `codec_negotiate` | JSON | First message: declare audio format |
| Binary frames | Raw PCM | Audio chunks from microphone |
| `ping` | JSON | Heartbeat (every 30s) |
| `text_input` | JSON | Fallback text input |

### Server → Client
| Type | Format | Purpose |
|------|--------|---------|
| `codec_ack` | JSON | Confirm codec accepted |
| `session_ready` | JSON | Session active, bridge started |
| Binary frames | Raw PCM | Audio from agent |
| `agent_speaking` | JSON | Agent response starting |
| `agent_done` | JSON | Agent response complete |
| `barge_in_ack` | JSON | User interruption acknowledged |
| `voice_reconnecting` | JSON | Nova Sonic session reconnecting |
| `voice_reconnected` | JSON | Reconnection complete |
| `voice_timeout` | JSON | Silence timeout (175s) |
| `error` | JSON | Error with code |

## Nova Sonic Integration Notes

- **Model**: `amazon.nova-sonic-v2:0`
- **Connection limit**: 8 minutes hard limit; reconnect at 7 minutes
- **Silence timeout**: 175 seconds; Nova Sonic disconnects
- **Barge-in**: Server-side detection built into Nova Sonic (sends `INTERRUPTED` stop reason)
- **SDK**: Strands `BidiAgent` + `BidiNovaSonicModel` handles the protocol automatically
- **Retry**: 3 attempts on agent error with history replay

## Success Criteria

- User speaks → Agent responds with audible voice within 2 seconds
- Barge-in works: user can interrupt agent mid-response
- 8-minute reconnection is transparent to the user
- Frontend shows conversation state (agent speaking, listening, etc.)
- Works in deployed environment (LOCAL_MODE=false + AWS creds)

## Files to Modify

| File | Change |
|------|--------|
| `frontend/.env.example` | `VITE_OUTPUT_SAMPLE_RATE=16000` |
| `frontend/src/config/constants.ts` | Verify OUTPUT_SAMPLE_RATE reads from env |
| `frontend/src/components/controls/ControlPanel.tsx` | Fix binary handler to always feed audio |
| `frontend/src/types/websocket.ts` | Add missing server message types |
| `frontend/src/contexts/SessionContext.tsx` | Handle voice lifecycle messages |
| `frontend/src/contexts/ConversationContext.tsx` | Add `isAgentSpeaking` state |
| `src/voice_server/ws/handler.py` | Document LOCAL_MODE behavior |
| `src/voice_server/bidi/barge_in.py` | Wire into stream loop (Phase C) |
