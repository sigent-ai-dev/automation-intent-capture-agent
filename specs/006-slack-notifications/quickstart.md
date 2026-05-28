# Quickstart: Slack Developer Notifications

## Prerequisites

- Python 3.12+
- Slack workspace with Incoming Webhooks enabled
- Webhook URL from Slack (Apps → Incoming Webhooks → Add New)

## Setup

```bash
# Install dependencies
uv sync --group dev

# Configure Slack webhook
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxx
export SLACK_CHANNEL="#intent-capture"  # optional, defaults to webhook's channel
export SLACK_ENABLED=true

# Start the voice server
LOCAL_MODE=true uv run uvicorn voice_server.main:app --host 0.0.0.0 --port 8080 --reload
```

## Test Notification

```bash
# Capture and finalise an intent (via voice or directly)
# On finalisation, a Slack message will appear in your channel:
#
# 🎯 Intent Captured: Restaurant Booking System
# Actor: voice | Fields: 5/6 | Clarifications: 1 open
# ...
```

## Disable Notifications

```bash
# Option 1: Unset the webhook URL
unset SLACK_WEBHOOK_URL

# Option 2: Explicitly disable
export SLACK_ENABLED=false
```

## Run Tests

```bash
# Unit tests (no real Slack needed — uses respx mock)
uv run python -m pytest tests/unit/test_slack_notifications.py tests/unit/test_rate_limiter.py -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | (empty) | Incoming Webhook URL — notifications disabled if empty |
| `SLACK_CHANNEL` | (empty) | Override channel (optional — uses webhook default if empty) |
| `SLACK_ENABLED` | `true` | Explicit enable/disable toggle |
