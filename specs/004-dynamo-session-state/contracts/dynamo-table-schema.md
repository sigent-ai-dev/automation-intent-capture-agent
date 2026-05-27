# DynamoDB Table Schema Contract

## Table: intent-capture-sessions

### CreateTable Parameters

```json
{
  "TableName": "intent-capture-sessions",
  "KeySchema": [
    {"AttributeName": "session_id", "KeyType": "HASH"},
    {"AttributeName": "record_type", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "session_id", "AttributeType": "S"},
    {"AttributeName": "record_type", "AttributeType": "S"},
    {"AttributeName": "status", "AttributeType": "S"},
    {"AttributeName": "last_activity", "AttributeType": "N"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "status-index",
      "KeySchema": [
        {"AttributeName": "status", "KeyType": "HASH"},
        {"AttributeName": "last_activity", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    }
  ],
  "BillingMode": "PAY_PER_REQUEST",
  "TimeToLiveSpecification": {
    "AttributeName": "expires_at",
    "Enabled": true
  }
}
```

### Terraform Resource

```hcl
resource "aws_dynamodb_table" "sessions" {
  name         = "${var.project_name}-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "record_type"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "record_type"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "last_activity"
    type = "N"
  }

  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "last_activity"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = var.common_tags
}
```

---

## Adapter Interface Contract

### PersistenceAdapter Protocol

Each adapter exposes the same interface pattern:

```
save(entity) → async, fire-and-forget with retry
load(id) → async, strong consistent read, returns entity or None
delete(id) → async, removes record
drain_all() → sync, batch writes all in-memory state, retries for drain window
```

### Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Write fails (transient) | Log warning, retry once, continue (in-memory is authoritative) |
| Write fails (persistent) | Log error, metric emitted, in-memory state continues serving |
| Read fails on reconnection | Return None → session starts fresh (graceful degradation) |
| Batch write fails on drain | Retry with backoff for remaining drain time, log unprocessed items |
| Item exceeds 400KB | Trigger history summarisation to reduce size, retry write |

### TTL Refresh

Every interaction refreshes `expires_at`:
```
expires_at = int(time.time()) + session_ttl_seconds
```

Default `session_ttl_seconds` = 86400 (24 hours). Configurable via `SESSION_TTL_SECONDS` env var.
