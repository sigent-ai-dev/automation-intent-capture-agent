# Data Model: DynamoDB Session State Persistence

## DynamoDB Table Design

**Table Name**: `intent-capture-sessions`

### Key Schema

| Key | Attribute | Type | Description |
|-----|-----------|------|-------------|
| PK | session_id | String | WebSocket session UUID |
| SK | record_type | String | "SESSION", "HISTORY", or "ELICITATION" |

### Global Secondary Index

**GSI1: status-index**

| Key | Attribute | Type | Description |
|-----|-----------|------|-------------|
| GSI1PK | status | String | "active" or "closed" |
| GSI1SK | last_activity | Number | Epoch seconds (for sorting) |

### TTL

| Attribute | Type | Description |
|-----------|------|-------------|
| expires_at | Number | Epoch seconds — DynamoDB auto-deletes after this time |

---

## Record Types

### SESSION Record (SK = "SESSION")

| Attribute | Type | Description |
|-----------|------|-------------|
| session_id | String | PK — WebSocket session UUID |
| record_type | String | SK — always "SESSION" |
| user_id | String | Authenticated user identifier |
| state | String | "connecting", "streaming", "disconnecting", "closed" |
| connected_at | String | ISO 8601 timestamp |
| last_activity | Number | Epoch seconds (also GSI1SK) |
| status | String | "active" or "closed" (GSI1PK) |
| codec | Map | {format, sample_rate, bit_depth, channels} |
| expires_at | Number | TTL — last_activity + 24h |

### HISTORY Record (SK = "HISTORY")

| Attribute | Type | Description |
|-----------|------|-------------|
| session_id | String | PK — parent session |
| record_type | String | SK — always "HISTORY" |
| summary | String | Condensed summary of older turns |
| turns | List[Map] | Recent turns: [{role, text, timestamp}] |
| window_size | Number | Configured sliding window size |
| updated_at | String | ISO 8601 timestamp of last update |
| expires_at | Number | TTL — same as parent session |

### ELICITATION Record (SK = "ELICITATION")

| Attribute | Type | Description |
|-----------|------|-------------|
| session_id | String | PK — parent session |
| record_type | String | SK — always "ELICITATION" |
| intent_id | String | Currently active intent document ID (e.g., "INT-001") |
| populated_fields | List[String] | Fields that have content |
| outstanding_clarifications | List[String] | CLR-NNN IDs still OPEN |
| elicitation_status | String | "in_progress" or "confirmed" |
| updated_at | String | ISO 8601 timestamp |
| expires_at | Number | TTL — same as parent session |

---

## Access Patterns

| Pattern | Operation | Key Condition | Consistency |
|---------|-----------|---------------|-------------|
| Get session by ID | GetItem | PK=session_id, SK="SESSION" | Strong |
| Load full session state | Query | PK=session_id | Strong |
| List active sessions | Query GSI1 | GSI1PK="active" | Eventual |
| Get history by session | GetItem | PK=session_id, SK="HISTORY" | Strong |
| Get elicitation state | GetItem | PK=session_id, SK="ELICITATION" | Strong |
| Batch save on shutdown | BatchWriteItem | Multiple PKs | N/A (write) |

---

## Relationships

```
Session (PK=sid, SK=SESSION)
    │
    ├── History (PK=sid, SK=HISTORY)
    │
    └── Elicitation (PK=sid, SK=ELICITATION)
```

All three records share the same PK (session_id) and same TTL (expires_at). A single `Query` by PK returns all related records for a session.

---

## Validation Rules

- `session_id` must be a valid UUID4 string
- `state` must be one of: connecting, streaming, disconnecting, closed
- `status` must be one of: active, closed
- `expires_at` must always be > current time (refreshed on every interaction)
- `turns` list capped at `window_size` entries (older turns summarised)
- Total item size must not exceed 400KB (enforced by summarising history)

## Capacity Planning

- **Write capacity**: ~100 WCU peak (50 sessions × 2 writes/session/minute)
- **Read capacity**: ~10 RCU (reconnections are rare events, not steady-state)
- **Storage**: ~50KB per session × 50 sessions = 2.5MB active (negligible)
- **Recommendation**: On-demand capacity mode (pay-per-request) — traffic is bursty
