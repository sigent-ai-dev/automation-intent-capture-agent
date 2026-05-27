# Data Model: BidiAgent Nova Sonic Integration

## Entities

### VoiceConnection

Represents a single bidirectional stream to Nova Sonic. Limited to 8 minutes.

| Field | Type | Description |
|-------|------|-------------|
| id | str (UUID4) | Unique connection identifier |
| session_id | str | Parent WebSocket session ID (from issue #1) |
| state | VoiceConnectionState | Current lifecycle state |
| started_at | datetime | UTC timestamp of connection establishment |
| expires_at | datetime | started_at + 8 minutes (hard limit) |
| reconnect_at | datetime | started_at + 7 minutes (proactive swap trigger) |

### VoiceConnectionState (Enum)

```
CONNECTING → ACTIVE → DRAINING → CLOSED
                ↓
           RECONNECTING → ACTIVE (new connection)
```

| State | Entry Condition | Exit Condition |
|-------|----------------|----------------|
| CONNECTING | New BidiAgent session requested | Session ready confirmed |
| ACTIVE | Session ready, audio flowing | Timer hits 7min, error, or user disconnect |
| RECONNECTING | Proactive swap initiated at 7min | New connection confirmed ACTIVE |
| DRAINING | Old connection being replaced | Audio drained, connection closed |
| CLOSED | Connection terminated | Removed from tracking |

### ConversationHistory

Ordered log of the conversation, used for replay on reconnection.

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | Parent WebSocket session ID |
| turns | list[Turn] | Ordered list of conversational turns |
| summary | str | Condensed summary of turns beyond the sliding window |
| window_size | int | Number of recent turns kept verbatim (default: 10) |

### Turn

A single conversational exchange.

| Field | Type | Description |
|-------|------|-------------|
| role | str | "user" or "assistant" |
| text | str | Transcribed text of the utterance |
| timestamp | datetime | When the turn was completed |

### AudioBridge

The adapter layer managing audio flow between WebSocket and BidiAgent.

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | Parent WebSocket session ID |
| input_queue | asyncio.Queue | Audio frames from WebSocket waiting to be sent to Nova Sonic |
| is_agent_speaking | bool | Whether the agent is currently outputting audio |
| barge_in_detected | bool | Whether a user interruption is in progress |

## Relationships

```
WebSocket Session 1 ──── 1 AudioBridge
AudioBridge 1 ──── 1 VoiceConnection (active at a time)
AudioBridge 1 ──── 1 ConversationHistory
ConversationHistory 1 ──── * Turn
```

## State Transitions: Reconnection Flow

```
T=0min:   VoiceConnection[1] → ACTIVE
T=7min:   VoiceConnection[2] → CONNECTING (parallel)
          VoiceConnection[1] remains ACTIVE (still serving audio)
T=7min+Ns: VoiceConnection[2] → ACTIVE (history replayed)
           VoiceConnection[1] → DRAINING (stop sending new audio)
           AudioBridge swaps to VoiceConnection[2]
T=7min+Ns+1s: VoiceConnection[1] → CLOSED
```

## Validation Rules

- Only one VoiceConnection in ACTIVE state per session at a time (except during the overlap window of reconnection)
- ConversationHistory.turns beyond window_size must be summarised before replay
- Audio frames received during RECONNECTING state are buffered in input_queue (not dropped)
- Barge-in flag resets when user stops speaking and new agent response begins
- VoiceConnection must never exceed 8 minutes — force-close if still active at 7:55
