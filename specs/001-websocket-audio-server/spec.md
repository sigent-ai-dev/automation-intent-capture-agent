# Feature Specification: WebSocket Audio Server

**Feature Branch**: `001-websocket-audio-server`

**Created**: 2026-05-26

**Status**: Draft

**Input**: User description: "Voice MVP: WebSocket server with FastAPI + Uvicorn that accepts browser audio connections, manages session lifecycle, and provides the bridge between client audio and the Strands BidiAgent."

## Clarifications

### Session 2026-05-26

- Q: What wire format should the WebSocket use for audio vs control messages? → A: Binary frames for audio, JSON text frames for control messages (codec-ack, session events, errors, ping/pong)
- Q: What authentication approach should the server use, and should auth be in scope? → A: ALB + Cognito OAuth2/OIDC. ALB authenticates on WebSocket upgrade request using Cognito user pool. Auth is in scope for MVP.
- Q: What should the default stale connection timeout be? → A: 30 seconds — no audio frames within this period triggers cleanup.
- Q: What observability signals should the server emit? → A: Structured logs + key metrics. Use AWS Lambda Powertools for any Lambda components and X-Ray for distributed tracing. ECS server emits structured JSON logs with session correlation IDs and CloudWatch metrics (active sessions, connection duration, errors).
- Q: How long should the graceful shutdown drain period be? → A: 30 seconds — matches ECS Fargate default stopTimeout, then force-terminate remaining sessions.
- Q: What should the health check semantics be? → A: Both liveness and readiness — `/health/live` (process alive, always 200) and `/health/ready` (accepting new sessions, capacity-aware). ALB target group uses the readiness endpoint.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish Audio Connection (Priority: P1)

A browser client connects to the WebSocket server to begin a voice interaction session. The client opens a WebSocket connection, negotiates the audio codec (PCM 16-bit, 16kHz mono), and begins streaming audio bidirectionally.

**Why this priority**: Without a working connection and codec agreement, no audio can flow — this is the foundation for all other functionality.

**Independent Test**: Can be fully tested by connecting a WebSocket client, performing the handshake, and confirming the server acknowledges the codec parameters and is ready to receive/send audio frames.

**Acceptance Scenarios**:

1. **Given** a browser client with microphone access, **When** it opens a WebSocket connection to the server, **Then** the server upgrades the connection, acknowledges codec parameters (PCM 16-bit 16kHz), and enters the streaming state.
2. **Given** a connected client, **When** it sends audio frames in the agreed codec, **Then** the server receives and buffers the frames without error.
3. **Given** a connected client, **When** the server has audio to send back, **Then** it transmits frames in the same agreed codec format.

---

### User Story 2 - Session Lifecycle Management (Priority: P1)

The server manages the full lifecycle of each audio session: tracking connected clients, handling graceful disconnections, and cleaning up resources when sessions end (whether by client close, timeout, or error).

**Why this priority**: Resource leaks and orphaned sessions would degrade the system rapidly under real usage. Lifecycle management is essential for production reliability.

**Independent Test**: Can be tested by connecting multiple clients, disconnecting them under various conditions (graceful close, network drop, timeout), and verifying that all associated resources are released.

**Acceptance Scenarios**:

1. **Given** a client connected and streaming, **When** the client sends a close frame, **Then** the server performs cleanup (releases buffers, closes upstream connections) and confirms disconnection.
2. **Given** a client connected and streaming, **When** the client disappears without sending a close frame, **Then** the server detects the stale connection within a reasonable timeout and performs cleanup.
3. **Given** multiple concurrent sessions, **When** one session disconnects, **Then** other sessions continue unaffected.

---

### User Story 3 - Health Check for Load Balancer (Priority: P2)

An infrastructure load balancer periodically checks whether the server is healthy and able to accept new connections. The server exposes an HTTP health check endpoint that returns status information.

**Why this priority**: Required for production deployment behind a load balancer, but the core audio functionality works without it.

**Independent Test**: Can be tested by sending an HTTP GET request to the health endpoint and verifying a 200 response with status payload.

**Acceptance Scenarios**:

1. **Given** the server is running and ready, **When** the load balancer sends an HTTP GET to the health endpoint, **Then** it receives a 200 response indicating healthy status.
2. **Given** the server is overloaded or unhealthy, **When** the load balancer sends an HTTP GET to the health endpoint, **Then** it receives a non-200 response indicating the server should be removed from rotation.

---

### User Story 4 - Local Development Experience (Priority: P2)

A developer working on the voice agent can start the WebSocket server locally with a single command, connect test clients, and iterate quickly without needing containerised infrastructure.

**Why this priority**: Fast local iteration accelerates development but is not required for production operation.

**Independent Test**: Can be tested by running the server directly with `uvicorn`, connecting a local WebSocket client, and verifying audio flows.

**Acceptance Scenarios**:

1. **Given** a developer with the project checked out, **When** they run the server via `uvicorn`, **Then** it starts on a configurable local port and accepts WebSocket connections.
2. **Given** the server running locally, **When** a developer makes a code change, **Then** uvicorn's reload picks up the change without manual restart.

---

### User Story 5 - Container Deployment (Priority: P3)

The server can be packaged into a container image suitable for deployment on a managed container service, with appropriate resource configuration and startup behaviour.

**Why this priority**: Deployment packaging is needed for production but does not affect core server functionality.

**Independent Test**: Can be tested by building the container image and running it locally, then connecting a WebSocket client and verifying audio handling.

**Acceptance Scenarios**:

1. **Given** the Dockerfile in the project, **When** a developer builds the image, **Then** it produces a runnable container that starts the server on the expected port.
2. **Given** a running container, **When** a client connects via WebSocket, **Then** audio streaming works identically to local development mode.

---

### Edge Cases

- What happens when a client attempts to connect with an unsupported audio codec?
- How does the system handle a client that connects but never sends audio (idle connection)?
- What happens when the server reaches maximum concurrent session capacity?
- How does the system respond to malformed WebSocket frames or non-audio data?
- What happens during server shutdown while active sessions exist?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept WebSocket connections from browser clients for bidirectional audio streaming, using binary frames for audio data and JSON text frames for control messages.
- **FR-002**: System MUST negotiate audio codec on connection, supporting PCM 16-bit at 16kHz sample rate (mono).
- **FR-003**: System MUST reject connections that request unsupported audio codecs with an appropriate error message.
- **FR-012**: System MUST require authenticated users via ALB-enforced Cognito OAuth2/OIDC validation on WebSocket upgrade. Unauthenticated requests MUST be rejected before reaching the application.
- **FR-004**: System MUST track each connected client as a distinct session with its own lifecycle state (connecting → streaming → disconnecting → closed).
- **FR-005**: System MUST clean up all resources associated with a session upon disconnection (graceful or forced).
- **FR-006**: System MUST detect stale connections that have not communicated within a configurable timeout period (default: 30 seconds) and terminate them.
- **FR-007**: System MUST expose a liveness endpoint (`/health/live` — process alive, always 200) and a readiness endpoint (`/health/ready` — capacity-aware, returns non-200 when unable to accept new sessions). ALB target group health check uses the readiness endpoint.
- **FR-008**: System MUST support running directly via uvicorn for local development with auto-reload capability.
- **FR-009**: System MUST include a container definition suitable for managed container service deployment.
- **FR-010**: System MUST handle concurrent sessions independently without cross-session interference.
- **FR-011**: System MUST perform graceful shutdown with a 30-second drain period, notifying connected clients and allowing active sessions to complete before force-terminating.
- **FR-013**: System MUST emit structured JSON logs with session correlation IDs for all connection lifecycle events and errors.
- **FR-014**: System MUST publish key operational metrics (active session count, connection duration, error rate) to CloudWatch.
- **FR-015**: System MUST support X-Ray tracing for distributed request correlation across ECS and any Lambda components. Lambda components MUST use AWS Lambda Powertools for structured logging, metrics, and tracing.

### Key Entities

- **Session**: Represents a single client-to-server audio connection. Attributes: unique identifier, lifecycle state, connected-at timestamp, last-activity timestamp, negotiated codec parameters.
- **Audio Frame**: A discrete unit of audio data exchanged between client and server. Attributes: codec format, sample rate, bit depth, payload.
- **Health Status**: The server's self-reported ability to accept new connections. Attributes: status (healthy/unhealthy), active session count, uptime.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A browser client can establish a bidirectional audio session within 2 seconds of initiating connection.
- **SC-002**: The server handles at least 50 concurrent audio sessions without degradation in audio frame delivery.
- **SC-003**: Disconnected sessions release all associated resources within 5 seconds of disconnection detection.
- **SC-004**: Health check endpoint responds within 100 milliseconds under normal operation.
- **SC-005**: Server starts and becomes ready to accept connections within 5 seconds in both local and container modes.
- **SC-006**: All connection and session management paths are covered by automated tests.

## Assumptions

- Clients are modern web browsers with WebSocket and Web Audio API support.
- Audio is mono channel (single channel) — stereo is out of scope for this MVP.
- The server acts as a bridge/relay; audio processing (transcription, synthesis) happens in a downstream service (Strands BidiAgent), which is out of scope for this issue.
- Authentication is handled at the ALB layer via Cognito OAuth2/OIDC; the server trusts that any connection forwarded by the ALB is authenticated and can extract user identity from ALB-injected headers.
- The container deployment target is ECS Fargate, but the Dockerfile does not include Fargate-specific infrastructure (task definitions, service config) — only the image itself.
- The server will sit behind an Application Load Balancer that handles TLS termination; the server itself communicates over plain WebSocket (ws://) internally.
- Maximum concurrent sessions will be bounded by container resources rather than an application-level hard limit in the MVP.

## Scope Boundaries

### In Scope

- WebSocket server accepting audio connections
- Audio codec negotiation (PCM 16-bit 16kHz)
- Binary frames for audio, JSON text frames for control messages
- Session lifecycle management
- ALB + Cognito OAuth2/OIDC authentication on WebSocket upgrade
- Health check endpoint
- Dockerfile for containerisation
- Local development mode
- Unit tests for connection and session management

### Out of Scope

- Nova Sonic integration
- Elicitation logic
- Terraform/infrastructure deployment
- Cognito user pool provisioning (assumes existing pool)
- Audio transcription or synthesis
- Client-side implementation
- Load testing infrastructure
