# Data Model: Cross-Channel Session Continuity

## DynamoDB Table: `intent-capture-sessions` (existing, extended)

Single-table design. Existing items (PK=`session_id`) coexist with new items (PK=`intent_id`).

### New Record Types

#### INTENT_SESSION (PK: intent_id, SK: "INTENT_SESSION")

Tracks cross-channel session state for a single intent capture.

| Attribute | Type | Description |
|-----------|------|-------------|
| intent_id | S (PK) | Intent identifier (e.g., "INT-001") |
| record_type | S (SK) | "INTENT_SESSION" |
| user_email | S | Canonical user identity (GSI PK) |
| project_name | S | Project name from intent document |
| elicitation_status | S | "in_progress" / "confirmed" / "abandoned" |
| active_channels | SS | Set of channels currently connected (e.g., {"voice", "slack"}) |
| last_activity | N | Unix timestamp of most recent interaction (GSI SK) |
| created_at | S | ISO timestamp of session creation |
| section_attributions | M | Map of section_name → {channel, timestamp} |
| version | N | Optimistic concurrency version (incremented on write) |
| expires_at | N | TTL attribute (24h after last_activity) |

#### INTENT_HISTORY (PK: intent_id, SK: "INTENT_HISTORY")

Conversation history keyed by intent, shared across all channels.

| Attribute | Type | Description |
|-----------|------|-------------|
| intent_id | S (PK) | Intent identifier |
| record_type | S (SK) | "INTENT_HISTORY" |
| turns | L | List of turn objects (max 30 recent) |
| summary | S | Summarised text of overflow turns |
| turn_count | N | Total turns across all channels |
| updated_at | S | ISO timestamp |
| expires_at | N | TTL attribute |

**Turn object** (within `turns` list):

| Attribute | Type | Description |
|-----------|------|-------------|
| role | S | "user" / "agent" |
| text | S | Message content |
| channel | S | "voice" / "slack" / "claude" |
| timestamp | S | ISO timestamp |

### New GSI: `user-email-index`

| Key | Attribute | Type |
|-----|-----------|------|
| PK | user_email | S |
| SK | last_activity | N |

**Projection**: ALL

**Purpose**: Query "find all active intents for this user" — returns INTENT_SESSION records for a given email, sorted by most recent activity.

**Filter**: Apply `elicitation_status = "in_progress"` filter expression on query results.

## Entity Relationships

```text
┌─────────────┐         ┌──────────────────┐
│ UnifiedUser │ 1─────* │ IntentSession    │
│ (email)     │         │ (intent_id)      │
└─────────────┘         └────────┬─────────┘
                                 │ 1
                                 │
                        ┌────────▼─────────┐
                        │ IntentHistory    │
                        │ (turns, summary) │
                        └────────┬─────────┘
                                 │ *
                        ┌────────▼─────────┐
                        │ ConversationTurn │
                        │ (role, text,     │
                        │  channel, ts)    │
                        └──────────────────┘
```

## State Transitions: IntentSession

```text
                    create_intent()
    [not exists] ─────────────────────► in_progress
                                             │
                           ┌─────────────────┤
                           │                 │
                     finalise_intent()   abandon (TTL / explicit)
                           │                 │
                           ▼                 ▼
                       confirmed         abandoned
```

## Backward Compatibility

- Existing SESSION, HISTORY, ELICITATION records (PK=`session_id`) remain unchanged
- Voice adapter writes to BOTH session-keyed (legacy) and intent-keyed (new) records
- New adapters (Slack, Claude) write ONLY to intent-keyed records
- The `user-email-index` GSI only indexes items that have `user_email` attribute (sparse index)

## IntentDocument Extension

The existing `IntentDocument` dataclass gains:

| Field | Type | Description |
|-------|------|-------------|
| channel_attributions | dict[str, ChannelContribution] | Maps section name → contributing channel + timestamp |

`ChannelContribution` structure:
- `channel`: str ("voice" / "slack" / "claude")
- `timestamp`: datetime

Attribution is metadata — not rendered in the 7-section markdown output (preserves Intent Kit compatibility). Stored in the INTENT_SESSION DynamoDB record under `section_attributions`.
