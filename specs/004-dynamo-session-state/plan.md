# Implementation Plan: DynamoDB Session State Persistence

**Branch**: `004-dynamo-session-state` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-dynamo-session-state/spec.md`

## Summary

Add write-through DynamoDB persistence for session state, conversation history, and elicitation progress. Existing in-memory modules (SessionRegistry, ConversationHistory, elicitation storage) gain adapter layers that async-write to DynamoDB on mutation and load on reconnection. Single-table design with composite key (PK=session_id, SK=record_type). TTL-based automatic cleanup.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: boto3 (DynamoDB client), aiobotocore (async DynamoDB operations), structlog

**Storage**: DynamoDB single table — PK: session_id, SK: record_type (SESSION|HISTORY|ELICITATION)

**Testing**: pytest + pytest-asyncio, moto (DynamoDB mock) for unit tests

**Target Platform**: ECS Fargate (same deployment target)

**Project Type**: Web service extension (adds persistence layer to existing modules)

**Performance Goals**: <50ms async write latency; <200ms session load on reconnect (strong consistency)

**Constraints**: DynamoDB 400KB item limit; 30-second drain window for graceful shutdown; single-writer per session

**Scale/Scope**: ~50 concurrent sessions; ~100 writes/minute peak (one per turn + tool invocation)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Runtime: ECS Fargate | PASS | Same deployment target |
| State: DynamoDB | PASS | This feature fulfils the constitution's DynamoDB requirement |
| Agent: Strands Agents SDK | PASS | No changes to agent layer |
| API: FastAPI + Uvicorn | PASS | No API changes |
| IaC: Terraform | PASS | Table provisioned via existing Terraform modules |
| Channel-agnostic core (Principle V) | PASS | Persistence is channel-independent |
| Graceful Degradation (Principle VI) | PASS | Falls back to in-memory if DynamoDB unavailable |
| API responses <200ms | PASS | Async writes don't block request path |
| Tests cover adapter independently | PASS | Moto-based unit tests for persistence layer |

**Post-Phase 1 re-check**: All gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/004-dynamo-session-state/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── dynamo-table-schema.md  # Table design contract
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (extends existing structure)

```text
src/
└── voice_server/
    ├── persistence/             # NEW: DynamoDB persistence layer
    │   ├── __init__.py
    │   ├── client.py            # DynamoDB client singleton + table setup
    │   ├── session_adapter.py   # Write-through adapter for SessionRegistry
    │   ├── history_adapter.py   # Write-through adapter for ConversationHistory
    │   ├── elicitation_adapter.py # Write-through adapter for elicitation state
    │   └── serializers.py       # Marshal/unmarshal between domain objects and DynamoDB items
    ├── sessions/
    │   └── registry.py          # MODIFIED: accept optional persistence adapter
    ├── bidi/
    │   ├── history.py           # MODIFIED: accept optional persistence adapter
    │   └── agent.py             # MODIFIED: wire persistence into AudioBridge
    └── config.py                # MODIFIED: add DynamoDB table name, region config

tests/
├── unit/
│   ├── test_session_adapter.py   # SessionRegistry persistence
│   ├── test_history_adapter.py   # ConversationHistory persistence
│   ├── test_elicitation_adapter.py # Elicitation state persistence
│   └── test_serializers.py       # Serialization round-trips
└── integration/
    └── test_dynamo_persistence.py # Full flow with moto mock
```

**Structure Decision**: New `persistence/` package for all DynamoDB logic. Adapters implement the same patterns as existing modules but add write-through to DynamoDB. Existing modules modified minimally — they accept an optional adapter on construction.

## Complexity Tracking

No constitution violations. Table not applicable.
