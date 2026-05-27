# Quickstart: DynamoDB Session State Persistence

## Prerequisites

- Python 3.12+
- AWS credentials with DynamoDB access
- WebSocket server running (from issues #1-#3)
- `uv` package manager
- DynamoDB table created (via Terraform or manually)

## Setup

```bash
# Install dependencies (includes boto3/aiobotocore)
uv sync --group dev

# Configure AWS
export AWS_REGION=us-east-1
export DYNAMO_TABLE_NAME=intent-capture-sessions
export SESSION_TTL_SECONDS=86400  # 24 hours (default)
```

## Local Development (DynamoDB Local)

```bash
# Start DynamoDB Local
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local

# Point the service at local DynamoDB
export DYNAMO_ENDPOINT_URL=http://localhost:8000

# Start the voice server
LOCAL_MODE=true uv run uvicorn voice_server.main:app --host 0.0.0.0 --port 8080 --reload
```

## Create Table (Local)

```bash
aws dynamodb create-table \
  --table-name intent-capture-sessions \
  --attribute-definitions \
    AttributeName=session_id,AttributeType=S \
    AttributeName=record_type,AttributeType=S \
    AttributeName=status,AttributeType=S \
    AttributeName=last_activity,AttributeType=N \
  --key-schema \
    AttributeName=session_id,KeyType=HASH \
    AttributeName=record_type,KeyType=RANGE \
  --global-secondary-indexes \
    'IndexName=status-index,KeySchema=[{AttributeName=status,KeyType=HASH},{AttributeName=last_activity,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8000
```

## Verify Persistence

```bash
# 1. Connect and start a voice session
wscat -c ws://localhost:8080/ws/audio
> {"type": "codec_negotiate", "codec": "pcm", "sample_rate": 16000, "bit_depth": 16, "channels": 1}

# 2. Speak some intent (or send test audio)
# 3. Disconnect

# 4. Check DynamoDB for persisted state
aws dynamodb query \
  --table-name intent-capture-sessions \
  --key-condition-expression "session_id = :sid" \
  --expression-attribute-values '{":sid": {"S": "<session-id-from-logs>"}}' \
  --endpoint-url http://localhost:8000

# 5. Reconnect — verify session resumes with full context
```

## Test Session Survival Across Restart

```bash
# 1. Start server, create session, speak some turns
# 2. Stop server (Ctrl+C — sends SIGTERM)
# 3. Check logs for "session_state_persisted" messages
# 4. Restart server
# 5. Reconnect with same session — verify context preserved
```

## Run Tests

```bash
# Unit tests (uses moto mock — no real DynamoDB needed)
uv run python -m pytest tests/unit/test_session_adapter.py tests/unit/test_history_adapter.py tests/unit/test_serializers.py -v

# Integration test (uses moto)
uv run python -m pytest tests/integration/test_dynamo_persistence.py -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DYNAMO_TABLE_NAME` | `intent-capture-sessions` | DynamoDB table name |
| `DYNAMO_ENDPOINT_URL` | (none — uses default AWS) | Override for local DynamoDB |
| `SESSION_TTL_SECONDS` | `86400` | Session expiry (seconds of inactivity) |
| `AWS_REGION` | `us-east-1` | AWS region for DynamoDB |
