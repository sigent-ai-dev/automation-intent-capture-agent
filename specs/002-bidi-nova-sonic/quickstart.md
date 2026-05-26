# Quickstart: BidiAgent Nova Sonic Integration

## Prerequisites

- Python 3.11+
- AWS credentials with Bedrock access (Nova Sonic v2)
- WebSocket server from issue #1 running
- `uv` package manager

## Setup

```bash
# Install dependencies (includes strands-agents)
uv sync --group dev

# Configure AWS region
export AWS_REGION=us-east-1
export AWS_PROFILE=your-bedrock-profile  # or use default credentials
```

## Run Locally

```bash
# Start the voice server (includes Nova Sonic bridge)
LOCAL_MODE=true uv run uvicorn voice_server.main:app --host 0.0.0.0 --port 8080 --reload
```

## Test with WebSocket Client

```bash
# Connect and negotiate codec
wscat -c ws://localhost:8080/ws/audio

# Send codec negotiation
> {"type": "codec_negotiate", "codec": "pcm", "sample_rate": 16000, "bit_depth": 16, "channels": 1}

# Expect: codec_ack, session_ready
# Then send binary audio frames (PCM 16kHz) from microphone
# Expect: binary audio frames back (agent response)
```

## Integration Test (Pre-recorded Audio)

```bash
# Run the integration test that sends a pre-recorded phrase
uv run pytest tests/integration/test_bidi_agent.py -v

# This test:
# 1. Connects WebSocket
# 2. Sends pre-recorded "Hello, I need help" audio
# 3. Verifies agent audio response is received
# 4. Verifies conversation history is tracked
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `NOVA_SONIC_MODEL_ID` | `amazon.nova-sonic-v2:0` | Nova Sonic model ID |
| `RECONNECT_BEFORE_SECONDS` | `60` | Seconds before 8-min limit to start reconnection |
| `HISTORY_WINDOW_SIZE` | `10` | Number of recent turns kept verbatim for replay |
| `BARGE_IN_ENERGY_THRESHOLD` | `0.15` | Audio energy threshold for barge-in detection (0-1) |
| `MAX_VOICE_RETRIES` | `3` | Retry attempts on voice service error |

## Architecture

```
WebSocket Handler (issue #1)
    │
    ├── Binary frames (user audio) → asyncio.Queue → WebSocketBidiInput
    │                                                      │
    │                                                      ▼
    │                                                 BidiAgent
    │                                                 (Strands SDK)
    │                                                      │
    │                                                      ▼
    ├── Binary frames (agent audio) ← WebSocketBidiOutput ←┘
    │
    └── JSON text frames (agent_speaking, agent_done, barge_in_ack, etc.)
```
