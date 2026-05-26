# Implementation Plan: WebSocket Audio Server

**Branch**: `001-websocket-audio-server` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-websocket-audio-server/spec.md`

## Summary

A FastAPI WebSocket server that accepts bidirectional audio connections from browser clients, manages session lifecycle (connect → stream → disconnect), and serves as the bridge layer for the Strands BidiAgent. Uses binary WebSocket frames for PCM audio and JSON text frames for control signalling. Authentication via ALB + Cognito OIDC on WebSocket upgrade. Observability via structlog, CloudWatch embedded metrics, and X-Ray tracing.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Uvicorn, structlog, aws-embedded-metrics, aws-xray-sdk

**Storage**: In-memory (Dict[str, Session]) — no persistent store for MVP

**Testing**: pytest + pytest-asyncio, httpx (for HTTP endpoint tests), websockets (for WebSocket client tests)

**Target Platform**: ECS Fargate (Linux/amd64) behind Application Load Balancer

**Project Type**: Web service (WebSocket server)

**Performance Goals**: 50 concurrent sessions, <2s connection establishment, health check <100ms

**Constraints**: 30s stale timeout, 30s shutdown drain, PCM 16-bit 16kHz mono only

**Scale/Scope**: Single ECS task (MVP), ~50 concurrent audio sessions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Runtime: ECS Fargate | PASS | Matches constitution technology decision |
| API: FastAPI + Uvicorn | PASS | Matches constitution technology decision |
| Agent: Strands Agents SDK | PASS | Bridge only — BidiAgent integration is out of scope for this issue |
| Voice: Nova Sonic 2 | N/A | Out of scope (separate issue) |
| State: DynamoDB | DEFERRED | Not needed for in-memory session MVP; will be used when session persistence is added |
| IaC: Terraform | DEFERRED | Dockerfile only; Terraform deployment is separate issue |
| Channel-agnostic core | PASS | WebSocket server is a channel adapter, not the elicitation engine |
| Graceful degradation | PASS | Server handles disconnects, timeouts, shutdown gracefully |
| Voice latency <800ms | N/A | Applies to barge-in with Nova Sonic, not this layer |
| Tests cover adapter independently | PASS | Unit tests for connection handling and session management specified |

**Post-Phase 1 re-check**: All gates pass. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-websocket-audio-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── websocket-api.md # WebSocket + HTTP API contract
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/
└── voice_server/
    ├── __init__.py
    ├── main.py              # FastAPI app, lifespan, signal handlers
    ├── config.py            # Environment variable configuration
    ├── models/
    │   ├── __init__.py
    │   ├── session.py       # Session dataclass, SessionState enum
    │   └── codec.py         # AudioCodec value object
    ├── ws/
    │   ├── __init__.py
    │   ├── handler.py       # WebSocket endpoint, frame routing
    │   ├── protocol.py      # Control message parsing/serialization
    │   └── auth.py          # ALB header extraction (user_id from x-amzn-oidc-identity)
    ├── sessions/
    │   ├── __init__.py
    │   ├── registry.py      # Session store (Dict), CRUD operations
    │   └── cleanup.py       # Background stale-session cleanup task
    ├── health/
    │   ├── __init__.py
    │   └── endpoints.py     # /health/live, /health/ready
    └── observability/
        ├── __init__.py
        ├── logging.py       # structlog configuration
        └── metrics.py       # CloudWatch embedded metrics helpers

tests/
├── conftest.py              # Shared fixtures (test client, mock sessions)
├── unit/
│   ├── test_session.py      # Session lifecycle state machine
│   ├── test_protocol.py     # Control message parsing
│   ├── test_registry.py     # Session registry CRUD
│   ├── test_cleanup.py      # Stale session detection
│   ├── test_auth.py         # ALB header extraction
│   └── test_codec.py        # Codec negotiation logic
└── integration/
    ├── test_websocket.py    # Full WebSocket connection flow
    ├── test_health.py       # Health endpoint responses
    └── test_shutdown.py     # Graceful shutdown behaviour

Dockerfile
pyproject.toml
```

**Structure Decision**: Single Python package (`src/voice_server/`) with flat module organisation. No monorepo — this is one service. Tests split into unit (fast, no I/O) and integration (WebSocket client tests against running app).

## Complexity Tracking

No constitution violations. Table not applicable.
