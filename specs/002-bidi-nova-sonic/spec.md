# Feature Specification: BidiAgent Nova Sonic Integration

**Feature Branch**: `002-bidi-nova-sonic`

**Created**: 2026-05-26

**Status**: Draft

**Input**: User description: "Connect the WebSocket server to Nova Sonic 2 via the Strands SDK BidiAgent for bidirectional voice — STT + TTS + LLM in a single stream. Must handle 8-minute connection limit, 175-second silence timeout, barge-in under 800ms."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full Voice Conversation (Priority: P1)

A user connected via WebSocket speaks into their microphone. Their audio is forwarded to Nova Sonic, which transcribes it, generates an LLM response, and streams synthesised speech back to the user in real time.

**Why this priority**: This is the core value proposition — without bidirectional audio flowing through Nova Sonic, there is no voice agent.

**Independent Test**: Connect a WebSocket client, stream a pre-recorded audio phrase (e.g., "Hello, I'd like help with my project"), verify that synthesised speech audio is received back within a reasonable time.

**Acceptance Scenarios**:

1. **Given** a connected and streaming WebSocket session, **When** the user sends audio frames containing speech, **Then** the system forwards the audio to Nova Sonic, receives a transcription and LLM response, and streams synthesised audio back to the user.
2. **Given** the user is speaking, **When** Nova Sonic completes transcription and generates a response, **Then** the user begins hearing the response within 2 seconds of finishing speaking.
3. **Given** the agent is responding with audio, **When** the response completes, **Then** the system signals readiness for the next user utterance.

---

### User Story 2 - Barge-In (Priority: P1)

A user interrupts the agent while it is speaking. The agent immediately stops its current audio output and listens to the user's new input.

**Why this priority**: Without barge-in, users must wait for the agent to finish before speaking, which feels unnatural and frustrating in a voice interface.

**Independent Test**: Start a conversation, trigger a long agent response, then send user audio mid-response. Verify agent audio stops within 800ms and the new user input is processed.

**Acceptance Scenarios**:

1. **Given** the agent is streaming synthesised audio to the user, **When** the user begins speaking (detected via voice activity), **Then** the agent stops sending audio within 800ms of the interruption.
2. **Given** a barge-in has occurred, **When** the user finishes their interrupting utterance, **Then** the system processes it as a new input and generates a fresh response.
3. **Given** a barge-in has occurred, **When** the agent was mid-sentence, **Then** the partial response is discarded and does not appear in conversation history.

---

### User Story 3 - Connection Resilience (8-Minute Limit) (Priority: P1)

The underlying voice service has an 8-minute maximum connection duration. The system transparently reconnects before the limit is reached and replays conversation history so the user experiences no interruption.

**Why this priority**: Without auto-reconnect, every conversation longer than 8 minutes would abruptly fail. Most real conversations exceed this limit.

**Independent Test**: Start a session, allow it to approach the 8-minute mark, verify the system reconnects seamlessly (no audible gap, conversation context preserved).

**Acceptance Scenarios**:

1. **Given** an active session approaching the 8-minute limit, **When** the system detects the connection is nearing expiry, **Then** it initiates a new connection and replays conversation history before the old connection drops.
2. **Given** a reconnection is in progress, **When** the user is speaking during reconnection, **Then** their audio is buffered and forwarded once the new connection is established.
3. **Given** a reconnection has completed, **When** the conversation continues, **Then** the agent retains full context from before the reconnection (no amnesia).

---

### User Story 4 - Silence Timeout Handling (Priority: P2)

If no audio activity occurs for an extended period (175 seconds), the voice service disconnects. The system handles this gracefully rather than crashing or leaving the session in a broken state.

**Why this priority**: Users may pause to think, read, or consult others during a session. The system must recover gracefully rather than failing silently.

**Independent Test**: Connect, negotiate codec, stop sending audio for 175+ seconds, verify the system either keeps the connection alive (via keepalive) or cleanly reconnects when the user resumes.

**Acceptance Scenarios**:

1. **Given** an active session with no audio for 175 seconds, **When** the voice service drops the connection, **Then** the system detects the disconnection and transitions to a recoverable state.
2. **Given** the voice connection has timed out, **When** the user resumes speaking, **Then** the system establishes a new voice connection, replays history, and processes the new input.
3. **Given** a silence timeout is approaching, **When** the system detects prolonged silence, **Then** it sends a brief prompt to the user (audio or text notification) indicating the session is still active.

---

### Edge Cases

- What happens if Nova Sonic returns an error mid-conversation (e.g., throttling, model error)?
- How does the system handle overlapping reconnection attempts (race condition)?
- What happens if conversation history exceeds the context window during replay?
- How does the system behave when Nova Sonic is completely unavailable (service outage)?
- What happens if the user disconnects during a reconnection attempt?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST forward user audio from the WebSocket session to the voice service in real time with no perceptible added delay.
- **FR-002**: System MUST receive synthesised audio from the voice service and stream it back to the user via the WebSocket connection.
- **FR-003**: System MUST detect user interruption (barge-in) and halt agent audio output within 800ms.
- **FR-004**: System MUST discard in-progress agent audio on barge-in and process the user's new input.
- **FR-005**: System MUST automatically reconnect to the voice service before the 8-minute connection limit expires, without user-visible interruption.
- **FR-006**: System MUST replay conversation history on reconnection so the agent retains full context.
- **FR-007**: System MUST handle 175-second silence timeout by transitioning to a recoverable state and reconnecting when the user resumes.
- **FR-008**: System MUST buffer user audio during reconnection and forward it once the new connection is established.
- **FR-009**: System MUST handle voice service errors (throttling, model errors, timeouts) gracefully without crashing the session.
- **FR-010**: System MUST convert between WebSocket audio format (PCM 16-bit 16kHz) and the voice service's expected input/output formats.
- **FR-011**: System MUST maintain a conversation transcript (text) for history replay on reconnection.

### Key Entities

- **Voice Connection**: A single bidirectional stream to the voice service. Limited to 8 minutes. Attributes: connection state, started-at timestamp, conversation history reference.
- **Conversation History**: Ordered sequence of user utterances (text) and agent responses (text) accumulated during a session. Used for replay on reconnection.
- **Audio Bridge**: The adapter layer that converts between the WebSocket server's audio format and the voice service's bidirectional protocol.
- **Barge-In Detector**: Monitors user audio activity while the agent is speaking to detect interruptions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive the first audio of the agent's response within 2 seconds of finishing speaking (end-to-end latency).
- **SC-002**: Barge-in halts agent audio within 800ms of user interruption being detected.
- **SC-003**: Reconnection at the 8-minute boundary completes with zero audible gap to the user.
- **SC-004**: Conversations lasting 30+ minutes function without degradation (multiple reconnections handled).
- **SC-005**: Voice service errors result in graceful recovery (session continues) in 95% of cases.
- **SC-006**: Audio quality is maintained during and after reconnection (no artifacts, no gaps, no repeated content).

## Assumptions

- The WebSocket server (from issue #1) is deployed and handling session lifecycle, codec negotiation, and binary audio frames.
- The voice service accepts PCM 16kHz audio as input and produces PCM 24kHz audio as output.
- Conversation history for replay is text-based (transcriptions), not raw audio replay.
- The 8-minute limit is a hard server-side disconnection — the system must reconnect proactively before it triggers.
- Barge-in detection is handled by the voice service's built-in voice activity detection, supplemented by client-side detection for faster response.
- The system prompt and tool definitions are re-sent on each reconnection as part of session setup.
- Only one voice connection exists per user session at a time (no parallel streams).

## Scope Boundaries

### In Scope

- Bidirectional audio bridge between WebSocket server and voice service
- Auto-reconnect before 8-minute connection limit
- Conversation history tracking and replay
- 175-second silence timeout handling and recovery
- Barge-in detection and audio cancellation
- Audio format conversion (16kHz input ↔ 24kHz output)
- Error handling for voice service failures
- Integration test with pre-recorded audio

### Out of Scope

- Elicitation logic (the agent's conversation strategy — what it says)
- Tool definitions and tool execution (separate issue)
- Multi-participant sessions
- Session state persistence to DynamoDB
- Voice selection or voice customisation
- Noise suppression or audio preprocessing
