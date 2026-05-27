# Research: BidiAgent Nova Sonic Integration

## R1: Strands SDK BidiAgent vs Raw Nova Sonic Client

**Decision**: Use Strands SDK `BidiAgent` with `BidiNovaSonicModel` as the primary integration path.

**Rationale**: The Strands SDK provides a higher-level abstraction that handles session setup, audio streaming protocol, tool use, and event dispatching. The trainline POC used a custom `SimpleNovaSonic` wrapper because Strands didn't exist at the time — that approach required 500+ lines of low-level WebSocket management, event parsing, and state tracking that Strands handles internally.

**Key Strands API**:
```python
from strands.experimental.bidi import BidiAgent, BidiNovaSonicModel, BidiInput, BidiOutput

model = BidiNovaSonicModel(model_id="amazon.nova-sonic-v2:0")
agent = BidiAgent(model=model, tools=[...])
# agent.run() manages the bidirectional stream
```

**Alternatives considered**:
- `SimpleNovaSonic` (trainline pattern): Direct Bedrock streaming WebSocket. More control but massive implementation burden and no tool-use support built in.
- Raw Bedrock `InvokeModelWithResponseStream`: Even lower level, no bidirectional support.

## R2: BidiInput/BidiOutput Bridge Pattern

**Decision**: Implement custom `BidiInput` and `BidiOutput` protocol classes that bridge between the WebSocket session's audio frames and the Strands BidiAgent stream.

**Rationale**: The Strands SDK defines `BidiInput` and `BidiOutput` as abstract protocols. By implementing these, we can feed audio from the WebSocket handler directly into the agent and route agent audio back to the client — without the agent knowing anything about WebSocket transport.

**Design**:
- `WebSocketBidiInput`: Reads audio from an asyncio queue (fed by the WebSocket handler's binary frames). Yields audio chunks to the agent.
- `WebSocketBidiOutput`: Receives audio/text events from the agent. Pushes binary frames back through the WebSocket and updates conversation history.

**Alternatives considered**:
- Callback-based bridge (trainline pattern): Works but creates tight coupling between transport and voice service. Protocol-based approach is cleaner and testable.
- Shared memory buffer: Over-engineered for single-process architecture.

## R3: Proactive Reconnection Strategy (Hot-Swap)

**Decision**: Timer-based reconnection at 7 minutes. New BidiAgent session established in parallel, history replayed, then audio stream atomically switched.

**Rationale**: The 8-minute limit is a hard server-side disconnect. Starting at 7 minutes gives 60 seconds to establish the new session and replay history. During the overlap window, user audio goes to both old and new sessions (old is draining, new is warming up). Once the new session confirms ready, the swap is atomic.

**Implementation sketch**:
1. `asyncio.create_task()` at T+7min → start new BidiAgent session
2. Feed conversation history (summarised + recent turns) as system context
3. New session signals ready → swap input/output references atomically
4. Old session disconnects gracefully

**Alternatives considered**:
- Reactive reconnect (after failure): Causes audible gap of 2-5 seconds while new session starts.
- AWS-managed reconnection: Nova Sonic doesn't support this natively.
- Pre-emptive at 7:30 (30s overlap): Too tight — history replay for long conversations may take 10-20s.

## R4: Conversation History — Sliding Window with Summary

**Decision**: Keep last 10 turns verbatim. When turns exceed 10, summarise turns 1..N-10 into a single paragraph prepended as system context.

**Rationale**: Nova Sonic v2's context window is ~128K tokens. A typical voice turn is 50-200 tokens (short utterances). 10 turns ≈ 1000-2000 tokens verbatim. The summary adds another ~200-500 tokens. This leaves ample room for system prompt + tool definitions while preserving recent conversational flow.

**Summarisation approach**: Use a lightweight summarisation prompt fed through the agent itself during the reconnection window (not a separate LLM call — reuse the same model).

**Alternatives considered**:
- Full history always: Would work for short conversations but risks context overflow at 30+ minutes (300+ turns).
- Fixed token budget with truncation: Loses context coherence at boundaries.
- External summarisation service: Adds latency and infrastructure complexity.

## R5: Barge-In Detection

**Decision**: Rely on Nova Sonic's built-in VAD (Voice Activity Detection) for barge-in. Supplement with client-side audio energy detection for faster initial signal.

**Rationale**: Nova Sonic v2 has native barge-in support — when it detects user speech while generating output, it emits a `contentEnd` event and stops TTS. The trainline POC's `EnhancedStreamHandler` added client-side energy detection (threshold 0.15) as a faster first-pass signal, then confirmed with Nova's server-side detection. This dual approach achieves the <800ms target.

**Implementation**:
- Audio energy threshold check on incoming user frames while agent is speaking
- If energy exceeds threshold → immediately stop forwarding agent audio to client (local flush)
- Nova Sonic confirms barge-in server-side → discard remaining buffered agent output

**Alternatives considered**:
- Server-side only (Nova Sonic VAD): Adds round-trip latency (~200ms), pushing close to 800ms budget.
- Client-side only (WebSocket server VAD): May miss speech in noisy environments.

## R6: Audio Format Conversion

**Decision**: Input stays at PCM 16kHz 16-bit (matches WebSocket and Nova Sonic input). Output from Nova Sonic is PCM 24kHz 16-bit — downsample to 16kHz before sending to client.

**Rationale**: The trainline POC's `AudioTranscoder` handles this conversion. Nova Sonic accepts 16kHz input natively but outputs at 24kHz for higher quality TTS. Since our WebSocket contract specifies 16kHz bidirectional, we need to downsample output.

**Implementation**: Simple linear interpolation downsampling (24kHz → 16kHz = drop every 3rd sample pair, or use proper resampling). The `audioop` stdlib module or numpy-based approach works.

**Alternatives considered**:
- Send 24kHz to client (change WebSocket contract): Breaks existing contract from issue #1.
- Let client handle resampling: Adds client complexity, inconsistent across browsers.

## R7: Error Recovery (Immediate Retry x3)

**Decision**: On voice service error, immediately retry up to 3 times with no delay. If all fail, notify user via WebSocket text frame and keep session in recoverable state.

**Rationale**: Transient errors (throttling bursts, network blips) typically resolve within milliseconds. Immediate retry maximises chance of seamless recovery. The trainline POC's `_is_restarting` flag prevents concurrent restart attempts.

**Recovery states**:
- Retry 1-3: Transparent to user (audio buffered during retry)
- All retries exhausted: Send `{"type": "error", "code": "VOICE_SERVICE_UNAVAILABLE"}` to client, session remains active for text fallback
- User resumes speaking: Triggers fresh connection attempt

**Alternatives considered**:
- Exponential backoff: Adds seconds of silence for a service that typically recovers in <100ms.
- Circuit breaker: Appropriate for sustained outages but over-engineered for MVP.
