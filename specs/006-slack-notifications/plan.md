# Implementation Plan: Slack Developer Notifications

**Branch**: `006-slack-notifications` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-slack-notifications/spec.md`

## Summary

Add a Slack notification adapter that fires async webhooks when intents are finalised or unrecoverable errors occur. The adapter is independent of core logic — it subscribes to events and sends formatted messages via Slack Incoming Webhooks. Configurable via environment variables, silently disabled when unconfigured.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: httpx (async HTTP client, already in dev deps)

**Storage**: None — rate-limit state is in-memory only

**Testing**: pytest + pytest-asyncio, respx (httpx mock) for webhook tests

**Target Platform**: ECS Fargate (same deployment)

**Project Type**: Web service extension (adds notification adapter alongside existing modules)

**Performance Goals**: Notification delivery <5s; zero latency added to session path (fire-and-forget async)

**Constraints**: Slack webhook payload max 40KB; rate limit 1/min per error type; no blocking of audio stream

**Scale/Scope**: ~5-10 notifications/day (intent finalisations); ~0-5 error alerts/day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Runtime: ECS Fargate | PASS | Same deployment |
| Channel-agnostic core (Principle V) | PASS | Slack is an adapter, not core |
| Graceful Degradation (Principle VI) | PASS | System works without notifications |
| Tests cover adapter independently | PASS | Webhook mocked, no real Slack needed |

**Post-Phase 1 re-check**: All gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/006-slack-notifications/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (extends existing structure)

```text
src/
└── voice_server/
    ├── notifications/           # NEW: notification adapter package
    │   ├── __init__.py
    │   ├── slack.py             # Slack webhook client + message formatting
    │   ├── events.py            # Event types (IntentFinalised, ErrorOccurred)
    │   └── rate_limiter.py      # In-memory per-type rate limiting
    ├── elicitation/
    │   └── tools.py             # MODIFIED: emit IntentFinalised event after finalise_intent
    ├── bidi/
    │   └── agent.py             # MODIFIED: emit ErrorOccurred event on unrecoverable error
    └── config.py                # MODIFIED: add SLACK_WEBHOOK_URL, SLACK_CHANNEL, SLACK_ENABLED

tests/
├── unit/
│   ├── test_slack_notifications.py  # Message formatting, rate limiting
│   └── test_rate_limiter.py         # Rate limit logic
└── integration/
    └── test_slack_delivery.py       # Full flow with respx mock
```

**Structure Decision**: New `notifications/` package. Event-driven: elicitation tools and agent error handler emit events, the Slack adapter subscribes. No direct coupling between core modules and Slack.

## Complexity Tracking

No constitution violations. Table not applicable.
