# Research: Cross-Channel Session Continuity

## R1: DynamoDB Single-Table Design for Intent-Keyed Records

**Decision**: Add intent-keyed records to the existing single table (`intent-capture-sessions`) with a new `user_email` GSI.

**Rationale**: The existing table uses `session_id` (PK) + `record_type` (SK). Intent-keyed records use `intent_id` (PK) + `record_type` (SK) in the same table. A new GSI on `user_email` + `last_activity` enables "find active intents for user" queries. Single-table design avoids operational overhead of a second table.

**Alternatives considered**:
- Separate table for intent state: rejected — doubles operational surface, no benefit at this scale
- Overloading existing session_id PK with intent_id: rejected — confuses semantics; cleaner to have intent_id as a distinct PK value in the same table

**Key detail**: DynamoDB allows heterogeneous items in one table. Items with `session_id` PK (existing) coexist with items using `intent_id` PK (new). The GSI projects `user_email`, `intent_id`, `last_activity`, `elicitation_status` for the lookup query.

## R2: Slack Bolt for Python — Events API Integration

**Decision**: Use `slack-bolt` (official Slack SDK) for handling inbound messages via Events API.

**Rationale**: Slack Bolt handles signature verification, event parsing, acknowledgement within 3-second deadline, and retry logic. It integrates with FastAPI via the `SlackRequestHandler` async adapter. No need for raw HTTP parsing.

**Alternatives considered**:
- Raw webhook handling with httpx: rejected — must manually handle signature verification, retry headers, URL verification challenge
- Slack Socket Mode: rejected — requires persistent WebSocket connection from server to Slack; adds complexity for ECS deployment and doesn't scale well with multiple tasks

**Key detail**: Slack Bolt runs alongside FastAPI on the same Uvicorn process. Events are routed to `/slack/events`. The bot responds in threads for conversational continuity. User email is resolved via `client.users_info(user=event["user"])`.

## R3: Identity Resolution via Email

**Decision**: Use email as canonical cross-channel identity. Extract from Cognito `email` claim (voice/web) and Slack `users.info` API (Slack).

**Rationale**: Email is the only identifier that naturally spans both Cognito and Slack without requiring an external identity service. The project is single-tenant, so email collisions across organizations are not a concern.

**Alternatives considered**:
- Separate identity mapping table: rejected — over-engineering for single-tenant; adds a write path on every session start
- Cognito sub as canonical: rejected — Slack users don't have Cognito accounts; would require all channels to auth through Cognito

**Key detail**: Slack email requires the `users:read.email` OAuth scope. Claude skill identity resolution uses the same Cognito token as voice (same user, different interface). If email is unavailable from Slack (user has it hidden), fall back to Slack `user_id` with a warning log — cross-channel continuity won't work for that user until email is available.

## R4: Conversation History Migration Strategy

**Decision**: New history records keyed by `intent_id` coexist with old records keyed by `session_id`. Voice adapter writes to both during transition; new adapters write only to intent-keyed history.

**Rationale**: Backward compatibility — existing voice sessions continue writing session-keyed history (no breaking change). The intent-keyed history is the source of truth for cross-channel resume. Voice adapter additionally writes to intent-keyed history once an intent is created (after `create_intent` tool call).

**Alternatives considered**:
- Migrate all history to intent-keyed immediately: rejected — voice sessions that haven't created an intent yet have no intent_id to key on
- Only use filesystem for history: rejected — filesystem isn't available across ECS tasks; DynamoDB is the shared state layer

**Key detail**: The 30-turn summarisation threshold applies to intent-keyed history. Each turn includes `channel` field ("voice", "slack", "claude") and timestamp. The `ConversationHistory` class is extended with a `channel` parameter on `add_turn()`.

## R5: Claude Skill Adapter Design

**Decision**: Claude skill exposes intent capture as an MCP tool that Claude Code (or other Claude interfaces) can invoke. The tool wraps the existing elicitation tools with session resolution.

**Rationale**: Claude Code already supports MCP tools. Exposing intent capture as a tool means any Claude session can drive elicitation without a custom UI. The tool handles: (1) resolve user email from Claude session context, (2) look up active intent, (3) relay messages to/from the elicitation engine.

**Alternatives considered**:
- REST API that Claude calls: rejected — adds network hop and auth complexity; MCP tool is direct
- Standalone Claude skill package: rejected — elicitation tools are in the voice_server package; better to keep adapters co-located

**Key detail**: The Claude adapter is a thin wrapper that creates a text-based elicitation session (no audio). It reuses `build_system_prompt()` + `build_resume_context()` and calls the same tools (`create_intent`, `update_intent_section`, `finalise_intent`). Session state is managed via the intent-keyed persistence, not in-memory.

## R6: Concurrency — Section-Level Last-Write-Wins

**Decision**: No distributed locking. DynamoDB conditional writes protect item integrity. Section updates use `UpdateExpression` with `SET` on individual section attributes, so concurrent updates to different sections don't conflict.

**Rationale**: At single-tenant scale with <100 users, true simultaneous updates to the same section are extremely rare. The cost of implementing distributed locks (Redis, DynamoDB lock table) far exceeds the risk. If two channels update the same section within seconds, the last write wins — acceptable for an elicitation tool where the user confirms the final document.

**Alternatives considered**:
- Optimistic locking with version counter: rejected — adds retry logic for a conflict that rarely happens
- Queue-based serialisation: rejected — adds latency and complexity for minimal benefit

**Key detail**: The `IntentDocument` already has per-section fields. DynamoDB `UpdateExpression` like `SET #section = :val, #updated_at = :ts` at the item level means concurrent writes to different items (different sections stored in the elicitation record) don't conflict at all.
