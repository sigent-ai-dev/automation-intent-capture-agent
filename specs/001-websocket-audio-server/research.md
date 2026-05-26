# Research: WebSocket Audio Server

## R1: FastAPI Native WebSocket for Audio Streaming

**Decision**: Use FastAPI's built-in WebSocket support (`@app.websocket()`) with Uvicorn's native asyncio WebSocket implementation.

**Rationale**: FastAPI/Starlette WebSocket endpoints natively support both text and binary frame types in the same connection. This lets us send raw PCM bytes as binary frames (zero encoding overhead) while using text frames for JSON control messages. No need for an additional WebSocket library.

**Alternatives considered**:

- `websockets` library directly (as in trainline POC's `server.py`): Would bypass FastAPI's middleware/dependency injection; loses health endpoints sharing the same app.
- `socketio` (Socket.IO): Adds protocol overhead (engine.io handshake, packet framing) unnecessary for a dedicated audio stream.
- API Gateway WebSocket: Forces text-only frames (base64 audio = 33% overhead), adds DynamoDB connection table, `@connections` send-back pattern. Overkill when ALB handles auth.

## R2: ALB WebSocket Authentication with Cognito

**Decision**: ALB authenticate action on the HTTP listener rule, validated before WebSocket upgrade. ALB injects user claims as `x-amzn-oidc-*` headers.

**Rationale**: ALB natively supports OpenID Connect authentication. When configured with a Cognito user pool, it intercepts the initial HTTP request (before WebSocket upgrade), redirects unauthenticated users to Cognito hosted UI, and only forwards authenticated requests to the target. The server receives `x-amzn-oidc-data` (JWT), `x-amzn-oidc-identity` (sub), and `x-amzn-oidc-accesstoken` headers — no custom auth middleware needed.

**Key details**:
- ALB authenticate action runs on the listener rule matching the WebSocket path
- WebSocket upgrade only proceeds after successful auth
- Server extracts user identity from ALB-injected headers (trusted, cannot be spoofed from outside)
- For local development: auth is bypassed (no ALB), server accepts all connections

**Alternatives considered**:

- Cognito JWT validation in FastAPI middleware: Duplicates ALB functionality, adds latency on every connection.
- API Gateway + Cognito authorizer: Forces text-only frames, adds architectural complexity.
- Custom Lambda authorizer: Only works with API Gateway, not ALB.

## R3: Session Management Pattern

**Decision**: In-memory dictionary keyed by connection ID, with asyncio background task for stale session cleanup.

**Rationale**: For an MVP targeting 50 concurrent sessions on a single ECS task, in-memory state is simplest and lowest latency. No need for Redis/DynamoDB session store at this scale. The cleanup task runs every 10 seconds, checking `last_activity` timestamps against the 30-second timeout.

**Key details**:
- `Dict[str, Session]` in the application module
- Session dataclass: id, state enum, connected_at, last_activity, codec_params, user_id
- State machine: CONNECTING → STREAMING → DISCONNECTING → CLOSED
- Cleanup task: `asyncio.create_task()` in lifespan startup, cancelled on shutdown

**Alternatives considered**:

- DynamoDB session table (trainline pattern): Needed for API Gateway multi-instance routing, unnecessary with ALB sticky sessions.
- Redis: Adds infrastructure dependency for 50 sessions.
- No background cleanup (rely on WebSocket close events only): Misses unclean disconnects.

## R4: Graceful Shutdown Strategy

**Decision**: SIGTERM handler sets `accepting_new = False`, sends close frames to all active sessions, waits up to 30 seconds for drain, then force-terminates.

**Rationale**: ECS Fargate sends SIGTERM then waits `stopTimeout` (30s default) before SIGKILL. The server should stop accepting new connections immediately, notify existing clients with a JSON control message (`{"type": "server_shutdown"}`), and wait for them to disconnect gracefully. After 30s, any remaining sessions are force-closed.

**Alternatives considered**:

- No graceful shutdown: Clients see abrupt disconnects, no chance to save state.
- Longer drain (60s+): Would need custom ECS stopTimeout, slows deployments.
- ALB connection draining only: ALB draining prevents new connections but doesn't notify existing WebSocket clients.

## R5: Observability Stack

**Decision**: `structlog` for structured JSON logs, `aws-embedded-metrics` for CloudWatch metrics, `aws-xray-sdk` for distributed tracing.

**Rationale**:
- `structlog`: Produces JSON logs with bound context (session_id, user_id). ECS sends stdout to CloudWatch Logs automatically.
- `aws-embedded-metrics`: EMF format lets us emit metrics directly in log output — CloudWatch extracts them without a metrics agent. Zero additional infrastructure.
- `aws-xray-sdk`: X-Ray daemon is built into Fargate. The SDK patches asyncio and traces requests automatically.
- Any Lambda components use `aws-lambda-powertools` which bundles all three (Logger, Metrics, Tracer).

**Alternatives considered**:

- OpenTelemetry: More portable but heavier setup, requires collector sidecar.
- CloudWatch agent for metrics: Needs sidecar container, more infra to manage.
- Plain `logging` module: No structured output, harder to query in CloudWatch Insights.

## R6: Health Check Implementation

**Decision**: Two endpoints: `/health/live` (liveness) and `/health/ready` (readiness). Readiness reports unhealthy during shutdown drain or when at capacity.

**Rationale**: Standard cloud-native pattern. ALB target group health check points at `/health/ready`. ECS can use `/health/live` for container health check (restart if dead). Separation means a draining instance stops receiving new connections (unready) but isn't killed (still alive).

**Key details**:
- `/health/live`: Always 200 if process is running. Response: `{"status": "alive"}`
- `/health/ready`: 200 if `accepting_new == True`. 503 if shutting down or at capacity. Response: `{"status": "ready"|"draining"|"at_capacity", "active_sessions": N, "uptime_seconds": N}`
- ALB health check interval: 10s, threshold: 2 consecutive failures

**Alternatives considered**:

- Single `/health` endpoint: Can't distinguish "should restart" from "stop sending traffic".
- gRPC health check: Unnecessarily complex for HTTP-based ALB.

## R7: Audio Frame Protocol

**Decision**: Binary WebSocket frames carry raw PCM audio. JSON text frames carry control messages with a `type` field for routing.

**Rationale**: Raw binary avoids base64 encoding overhead (33% size increase). WebSocket protocol natively distinguishes text from binary frames — no additional framing needed. The client and server agree on codec at connection time, so binary frames are unambiguously audio.

**Control message types** (JSON text frames):
- Client → Server: `{"type": "codec_negotiate", "codec": "pcm", "sample_rate": 16000, "bit_depth": 16, "channels": 1}`
- Server → Client: `{"type": "codec_ack", "codec": "pcm", ...}` or `{"type": "codec_reject", "reason": "..."}`
- Server → Client: `{"type": "session_ready", "session_id": "..."}`
- Client → Server: `{"type": "ping"}` / Server → Client: `{"type": "pong"}`
- Server → Client: `{"type": "server_shutdown", "drain_seconds": 30}`
- Server → Client: `{"type": "error", "message": "..."}`

**Alternatives considered**:

- All JSON with base64 audio (trainline pattern): 33% bandwidth overhead on continuous stream.
- Custom binary protocol for control messages too: Harder to debug, no benefit for low-frequency control messages.
- Protobuf framing: Over-engineered for simple control messages.
