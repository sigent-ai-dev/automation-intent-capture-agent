# Implementation Plan: BidiAgent Nova Sonic Integration

**Branch**: `002-bidi-nova-sonic` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-bidi-nova-sonic/spec.md`

## Summary

Integrate the Strands SDK BidiAgent with Nova Sonic 2 to provide bidirectional voice (STT + TTS + LLM) through the WebSocket server built in issue #1. Custom BidiInput/BidiOutput protocol implementations bridge WebSocket audio frames to the agent. Handles 8-minute connection limit via proactive hot-swap reconnection, 175s silence timeout recovery, and barge-in within 800ms.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: strands-agents (BidiAgent, BidiNovaSonicModel), structlog, aws-embedded-metrics, aws-xray-sdk

**Storage**: In-memory conversation history (list of Turn objects) — no persistent store for MVP

**Testing**: pytest + pytest-asyncio, mocked BidiAgent for unit tests, real Nova Sonic for integration tests (requires AWS credentials)

**Target Platform**: ECS Fargate behind ALB (same as issue #1)

**Project Type**: Web service extension (adds voice AI layer to existing WebSocket server)

**Performance Goals**: <2s end-to-end response latency, <800ms barge-in, zero-gap reconnection

**Constraints**: 8-minute hard connection limit, 175s silence timeout, PCM 16kHz input / 24kHz output conversion

**Scale/Scope**: Single ECS task, ~50 concurrent voice sessions (same as WebSocket server)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Runtime: ECS Fargate | PASS | Same deployment target as issue #1 |
| API: FastAPI + Uvicorn | PASS | Extends existing WebSocket server |
| Agent: Strands Agents SDK | PASS | BidiAgent is the primary integration |
| Voice: Nova Sonic 2 | PASS | Core of this feature |
| State: DynamoDB | DEFERRED | Out of scope — in-memory history only |
| IaC: Terraform | DEFERRED | No infra changes in this issue |
| Channel-agnostic core | PASS | Voice bridge is an adapter; elicitation logic separate |
| Graceful degradation | PASS | Error retry, silence timeout recovery, reconnection |
| Voice latency <800ms | PASS | Barge-in target explicitly addressed |
| Tests cover adapter independently | PASS | Unit + integration tests for bridge layer |

**Post-Phase 1 re-check**: All gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/002-bidi-nova-sonic/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── bidi-bridge-protocol.md  # BidiInput/BidiOutput + WebSocket events
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (extends existing structure from issue #1)

```text
src/
└── voice_server/
    ├── main.py                  # Wire BidiAgent into session lifecycle
    ├── bidi/                    # NEW: BidiAgent integration layer
    │   ├── __init__.py
    │   ├── agent.py             # BidiAgent factory, session setup, tool wiring
    │   ├── input.py             # WebSocketBidiInput protocol implementation
    │   ├── output.py            # WebSocketBidiOutput protocol implementation
    │   ├── connection.py        # VoiceConnection state machine, timer management
    │   ├── reconnect.py         # Proactive hot-swap reconnection logic
    │   ├── history.py           # ConversationHistory, sliding window + summary
    │   └── barge_in.py          # Barge-in detection (energy threshold + flush)
    ├── audio/                   # NEW: Audio processing utilities
    │   ├── __init__.py
    │   └── resample.py          # 24kHz → 16kHz downsampling
    ├── ws/
    │   └── handler.py           # MODIFIED: integrate AudioBridge into stream loop
    └── observability/
        └── metrics.py           # MODIFIED: add reconnection/barge-in metrics

tests/
├── unit/
│   ├── test_bidi_input.py       # BidiInput queue behaviour
│   ├── test_bidi_output.py      # BidiOutput event routing
│   ├── test_connection.py       # VoiceConnection state machine
│   ├── test_reconnect.py        # Timer-based reconnection logic
│   ├── test_history.py          # Sliding window + summarisation
│   ├── test_barge_in.py         # Energy detection, flush behaviour
│   └── test_resample.py         # 24kHz → 16kHz conversion
└── integration/
    └── test_bidi_agent.py       # Full flow: connect → speak → response → disconnect
```

**Structure Decision**: New `bidi/` package under `voice_server/` for all BidiAgent-related code. Separate `audio/` package for format conversion utilities. Existing WebSocket handler modified to wire the bridge.

## Complexity Tracking

No constitution violations. Table not applicable.
