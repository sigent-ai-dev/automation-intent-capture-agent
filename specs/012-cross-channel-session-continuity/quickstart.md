# Quickstart: Cross-Channel Session Continuity

## Prerequisites

- Python 3.12+
- AWS credentials (for DynamoDB — or local DynamoDB for dev)
- Slack workspace with a bot app (for Slack adapter)
- Claude Code (for Claude skill adapter)

## Setup

```bash
# Install dependencies (includes new slack-bolt)
uv sync --group dev

# Configure environment
export LOCAL_MODE=true
export DYNAMO_ENDPOINT_URL=http://localhost:8000  # local DynamoDB
export SLACK_BOT_TOKEN=xoxb-...                   # Slack bot token
export SLACK_SIGNING_SECRET=...                    # Slack app signing secret
export SLACK_ENABLED=true

# Start local DynamoDB (if not running)
docker run -d -p 8000:8000 amazon/dynamodb-local

# Create table with GSI (local dev)
aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name intent-capture-sessions \
  --attribute-definitions \
    AttributeName=session_id,AttributeType=S \
    AttributeName=record_type,AttributeType=S \
    AttributeName=user_email,AttributeType=S \
    AttributeName=last_activity,AttributeType=N \
  --key-schema \
    AttributeName=session_id,KeySchemaType=HASH \
    AttributeName=record_type,KeySchemaType=RANGE \
  --global-secondary-indexes \
    '[{"IndexName":"user-email-index","KeySchema":[{"AttributeName":"user_email","KeyType":"HASH"},{"AttributeName":"last_activity","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
  --billing-mode PAY_PER_REQUEST

# Start the server
uv run uvicorn voice_server.main:app --host 0.0.0.0 --port 8080 --reload
```

## Test Cross-Channel Flow

### 1. Start a voice session (populate some sections)

```bash
# Connect via WebSocket and complete a partial elicitation
# (creates INT-001 with context + intent populated)
```

### 2. Resume via Slack

In your Slack workspace, mention the bot:

```
@IntentBot I'd like to continue my intent capture
```

Expected response (in thread):
```
Resuming Restaurant Booking System (INT-001).

You've captured: context, intent.
Remaining: motivation, quality attributes, success criteria, assumptions.

Let's continue — what's the main motivation behind this project?
```

### 3. Resume via Claude

In Claude Code:

```
Use the intent_capture tool to resume INT-001
```

Expected response:
```
Picking up where you left off on 'Restaurant Booking'. You've covered context
and intent via voice, and motivation via Slack. What quality attributes matter?
```

### 4. Check status

```bash
curl http://localhost:8080/intents/active?user_email=you@example.com
```

## Run Tests

```bash
# Unit tests
uv run python -m pytest tests/unit/test_intent_session.py tests/unit/test_user_lookup.py tests/unit/test_slack_adapter.py tests/unit/test_claude_adapter.py tests/unit/test_intent_history.py -v

# Integration test (requires local DynamoDB)
uv run python -m pytest tests/integration/test_cross_channel_resume.py -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | (empty) | Slack bot OAuth token — Slack adapter disabled if empty |
| `SLACK_SIGNING_SECRET` | (empty) | Slack app signing secret for request verification |
| `SLACK_ENABLED` | `true` | Explicit enable/disable toggle for Slack inbound |
| `DYNAMO_TABLE_NAME` | `intent-capture-sessions` | DynamoDB table name |
| `DYNAMO_ENDPOINT_URL` | (empty) | Override for local DynamoDB |
| `HISTORY_SUMMARISE_THRESHOLD` | `30` | Turns before history summarisation triggers |

## Disable Cross-Channel Features

```bash
# Slack adapter won't start without token
unset SLACK_BOT_TOKEN

# Voice-only mode continues to work exactly as before
```
