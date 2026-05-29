# Implementation Plan: Cross-Channel Session Continuity

**Branch**: `012-cross-channel-session-continuity` | **Date**: 2026-05-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/012-cross-channel-session-continuity/spec.md`

## Summary

Enable intent capture sessions to persist and resume across channels (voice, Slack, Claude). The shared session layer uses DynamoDB with `intent_id` as partition key, email as canonical user identity, and conversation history keyed by intent rather than WebSocket session. Two new inbound adapters (Slack bot, Claude skill) reuse the existing elicitation tools and resume prompt.

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.6+ (frontend — no changes this feature)

**Primary Dependencies**: FastAPI, aiobotocore, strands-agents[bidi], httpx, slack-bolt (new), structlog

**Storage**: DynamoDB (existing table with new GSI + new record types keyed by intent_id)

**Testing**: pytest, pytest-asyncio, moto[dynamodb], respx (HTTP mocking for Slack)

**Target Platform**: ECS Fargate (existing), Slack Events API (new), Claude Code skill (new)

**Project Type**: Web service (FastAPI + WebSocket) with channel adapters

**Performance Goals**: Cross-channel resume <10s, conversation history load <500ms, Slack event response <3s (Slack timeout)

**Constraints**: DynamoDB 400KB item limit (sufficient for 30 verbatim turns + summary), Slack 3-second acknowledgement deadline, single DynamoDB table design

**Scale/Scope**: Single-tenant, <100 concurrent users, <50 turns per intent session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Meet Them Where They Are | PASS | Adds Slack and Claude as channels — expands access to existing workflows |
| II. Propose, Don't Interrogate | PASS | Elicitation engine (propose-and-steer) is unchanged — adapters are input/output layers |
| III. Structured Output | PASS | Intent document format unchanged — channel attribution is metadata |
| IV. Multi-Source Convergence | PASS | This feature directly implements Principle IV |
| V. Channel-Agnostic Core | PASS | Core elicitation tools reused by all adapters without modification |
| VI. Graceful Degradation | PASS | If a channel adapter fails, other channels continue; state persists |

| Quality Standard | Status | Notes |
|-----------------|--------|-------|
| API responses <200ms | PASS | New lookup endpoints are DynamoDB queries (single-digit ms) |
| Tests cover each adapter independently | PASS | Each adapter has independent unit tests |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/012-cross-channel-session-continuity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/voice_server/
├── channels/                    # NEW — channel adapter package
│   ├── __init__.py
│   ├── base.py                  # ChannelAdapter protocol + registry
│   ├── slack/
│   │   ├── __init__.py
│   │   ├── app.py               # Slack Bolt app (Events API handler)
│   │   ├── identity.py          # Slack user → email resolution
│   │   └── elicitation.py       # Slack ↔ elicitation bridge
│   └── claude/
│       ├── __init__.py
│       └── skill.py             # Claude skill adapter (MCP tool)
├── sessions/
│   ├── intent_session.py        # NEW — IntentSession (cross-channel session model)
│   └── user_lookup.py           # NEW — email → active intents lookup
├── persistence/
│   ├── intent_history_adapter.py  # NEW — history keyed by intent_id
│   └── intent_session_adapter.py  # NEW — session keyed by intent_id + user GSI
├── elicitation/
│   ├── intent_doc.py            # MODIFIED — add channel attribution to sections
│   ├── prompts.py               # MODIFIED — enhance resume prompt with channel history context
│   └── tools.py                 # MODIFIED — accept channel parameter in tool calls
├── config.py                    # MODIFIED — add Slack bot token, signing secret config
└── main.py                      # MODIFIED — register Slack adapter on startup

terraform/modules/voice-service/
├── dynamodb.tf                  # MODIFIED — add user_email GSI
└── variables.tf                 # MODIFIED — (no new infra beyond GSI)

tests/
├── unit/
│   ├── test_intent_session.py         # NEW
│   ├── test_user_lookup.py            # NEW
│   ├── test_slack_adapter.py          # NEW
│   ├── test_claude_adapter.py         # NEW
│   └── test_intent_history.py         # NEW
└── integration/
    └── test_cross_channel_resume.py   # NEW — E2E: voice → Slack resume
```

**Structure Decision**: Extends existing `src/voice_server/` with a new `channels/` package. Each channel is a sub-package with its own identity resolution, event handling, and bridge to the core elicitation tools. The persistence layer gets intent-keyed adapters alongside existing session-keyed ones for backward compatibility.
