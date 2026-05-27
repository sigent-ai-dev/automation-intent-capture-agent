# Research: Slack Developer Notifications

## R1: Slack Incoming Webhooks vs Bot API

**Decision**: Use Slack Incoming Webhooks (simple POST to a URL). No bot token, no OAuth flow, no Slack app registration required.

**Rationale**: Incoming Webhooks are the simplest integration — a single URL that accepts JSON payloads. The notification is one-directional (system → Slack), no interaction needed. Bot API would add OAuth complexity for zero benefit.

**Implementation**: Single `httpx.AsyncClient.post(webhook_url, json=payload)` call.

**Alternatives considered**:
- Slack Bot API: Requires app registration, OAuth tokens, token refresh. Over-engineered for fire-and-forget notifications.
- AWS SNS → Slack: Adds infrastructure (SNS topic, Lambda function). Unnecessary indirection.
- Email notifications: Less immediate, developers don't check email for operational events.

## R2: Event-Driven vs Direct Coupling

**Decision**: Use a simple event emitter pattern. Core modules call `notify(event)` which is a module-level function that dispatches to registered adapters. If no adapters registered (notifications disabled), it's a no-op.

**Rationale**: Constitution Principle V requires channel-agnostic core. Direct coupling (`import slack; slack.send()`) would violate this. An event function provides the decoupling — the elicitation tool calls `notify(IntentFinalised(...))` without knowing Slack exists.

**Pattern**:
```python
# notifications/__init__.py
async def notify(event: NotificationEvent) -> None:
    for adapter in _adapters:
        asyncio.create_task(adapter.send(event))

# Called from elicitation/tools.py:
from voice_server.notifications import notify
await notify(IntentFinalised(intent_id=..., project_name=...))
```

**Alternatives considered**:
- Full pub/sub (asyncio queues): Over-engineered for 2 event types and 1 subscriber.
- Direct import: Violates channel-agnostic principle.

## R3: Rate Limiting Strategy

**Decision**: In-memory token bucket per event type. Each error type gets 1 token per minute. If token exhausted, notification is silently dropped (logged at debug level).

**Rationale**: Prevents Slack channel flooding during cascading failures. In-memory is acceptable for single-process ECS task. Resets on deploy (acceptable — if the process restarts, the error storm is likely new anyway).

**Alternatives considered**:
- No rate limiting: Risk flooding channel with 100s of identical error messages during an outage.
- Redis-backed rate limiting: Over-engineered for single-process deployment.
- Aggregation (batch errors): More complex, delays first notification.

## R4: Message Formatting

**Decision**: Use Slack Block Kit for rich formatting. Intent notifications use sections with fields. Error notifications use a header + context block with warning emoji.

**Rationale**: Block Kit provides structured layout that's scannable in busy channels. Plain text would work but looks unprofessional and is harder to parse visually.

**Intent notification format**:
```
🎯 Intent Captured: [Project Name]
Actor: voice | Fields: 5/6 | Clarifications: 1 open

Intent: [single sentence]

Context: [first 200 chars]...
Populated: context, intent, motivation, quality_attributes, success_criteria
Open: CLR-001 (What are the assumptions?)
```

**Error notification format**:
```
⚠️ Voice Service Error
Session: [session_id] | Type: VOICE_SERVICE_UNAVAILABLE
Time: 2026-05-27T10:15:00Z
All retry attempts exhausted. User notified.
```
