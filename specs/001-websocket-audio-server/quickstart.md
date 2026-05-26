# Quickstart: WebSocket Audio Server

## Prerequisites

- Python 3.11+
- `uv` (recommended) or `pip`

## Local Development

```bash
# Install dependencies
uv sync

# Start server with auto-reload
uvicorn src.voice_server.main:app --host 0.0.0.0 --port 8080 --reload
```

Server starts at `ws://localhost:8080/ws/audio` (no auth in local mode).

## Test Connection

```bash
# Health check
curl http://localhost:8080/health/ready

# WebSocket test (requires wscat or similar)
wscat -c ws://localhost:8080/ws/audio
# Send: {"type": "codec_negotiate", "codec": "pcm", "sample_rate": 16000, "bit_depth": 16, "channels": 1}
# Expect: {"type": "codec_ack", ...}
```

## Docker

```bash
# Build
docker build -t voice-server .

# Run
docker run -p 8080:8080 voice-server
```

## Run Tests

```bash
# All tests
pytest

# Unit only
pytest tests/unit/

# With coverage
pytest --cov=src/voice_server
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server listen port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `STALE_SESSION_TIMEOUT_SECONDS` | `30` | Inactivity timeout before session cleanup |
| `SHUTDOWN_DRAIN_SECONDS` | `30` | Graceful shutdown wait period |
| `LOCAL_MODE` | `false` | Skip ALB auth header validation |
