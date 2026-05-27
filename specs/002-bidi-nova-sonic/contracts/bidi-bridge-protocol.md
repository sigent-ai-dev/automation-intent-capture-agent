# BidiInput/BidiOutput Bridge Protocol Contract

## Overview

The voice bridge implements the Strands SDK `BidiInput` and `BidiOutput` protocols to connect the WebSocket audio server (issue #1) with the BidiAgent running Nova Sonic.

---

## BidiInput Protocol (WebSocket → Agent)

### Input Source

Audio binary frames from the WebSocket handler, buffered in an asyncio queue.

### Yielded Events

| Event | Format | When |
|-------|--------|------|
| Audio chunk | Raw PCM bytes (16kHz, 16-bit, mono) | Every frame received from WebSocket |
| End of speech | Signal | When user stops speaking (VAD silence detected) |

### Behaviour

- Reads from `asyncio.Queue[bytes]` populated by the WebSocket handler
- Yields audio chunks as they arrive (no batching)
- Blocks (awaits) when queue is empty
- Stops yielding when session is closed or connection swapped

---

## BidiOutput Protocol (Agent → WebSocket)

### Output Sink

Binary frames pushed back through the WebSocket connection + conversation history updates.

### Received Events

| Event | Type | Action |
|-------|------|--------|
| Audio output | bytes (PCM 24kHz) | Downsample to 16kHz, send as binary WebSocket frame |
| Text transcript (user) | str | Append to ConversationHistory as user turn |
| Text transcript (assistant) | str | Append to ConversationHistory as assistant turn |
| Speech end | signal | Set `is_agent_speaking = False`, send `{"type": "agent_done"}` text frame |
| Error | str | Send `{"type": "error", "code": "VOICE_ERROR"}` text frame |
| Barge-in confirmed | signal | Flush output buffer, set `barge_in_detected = True` |

### Behaviour

- Receives events from the BidiAgent's output stream
- Audio output: downsample 24kHz → 16kHz, then `websocket.send_bytes()`
- Text events: update ConversationHistory (used for reconnection replay)
- Errors: notify client via JSON text frame, trigger retry logic

---

## WebSocket Control Messages (Added by this feature)

### Server → Client (new message types)

#### agent_speaking

Signals that the agent has begun its audio response.

```json
{
  "type": "agent_speaking"
}
```

#### agent_done

Signals that the agent has finished speaking.

```json
{
  "type": "agent_done"
}
```

#### barge_in_ack

Confirms the server detected the user's interruption and stopped agent audio.

```json
{
  "type": "barge_in_ack"
}
```

#### voice_reconnecting

Informational: the system is performing a transparent reconnection.

```json
{
  "type": "voice_reconnecting"
}
```

#### voice_reconnected

Informational: reconnection complete, audio flowing normally.

```json
{
  "type": "voice_reconnected"
}
```

---

## Audio Format Conversion

| Direction | Source Format | Target Format | Conversion |
|-----------|-------------|---------------|------------|
| User → Nova Sonic | PCM 16kHz 16-bit mono | PCM 16kHz 16-bit mono | None (passthrough) |
| Nova Sonic → User | PCM 24kHz 16-bit mono | PCM 16kHz 16-bit mono | Downsample 3:2 ratio |

---

## Reconnection Sequence

```
1. Timer fires at T+7min
2. Server sends {"type": "voice_reconnecting"} to client (informational)
3. New BidiAgent session created with:
   - System prompt + tool definitions
   - Conversation summary + last 10 turns as context
4. New session confirms ready
5. AudioBridge atomically swaps input/output to new session
6. Old session drains and closes
7. Server sends {"type": "voice_reconnected"} to client
8. Audio continues flowing through new session
```

---

## Error Recovery Sequence

```
1. Nova Sonic returns error (throttle, timeout, internal)
2. Immediate retry #1 (same session if still open, new session if closed)
3. If fail → immediate retry #2
4. If fail → immediate retry #3
5. If all fail → send {"type": "error", "code": "VOICE_SERVICE_UNAVAILABLE"} to client
6. Session stays alive — user can resume speaking to trigger fresh connection
```
