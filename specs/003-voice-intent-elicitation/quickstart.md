# Quickstart: Voice Intent Elicitation

## Prerequisites

- Python 3.12+
- AWS credentials with Bedrock access (Nova Sonic v2)
- WebSocket server running (from issue #1 + #2)
- `uv` package manager

## Setup

```bash
# Install dependencies
uv sync --group dev

# Configure AWS
export AWS_REGION=us-east-1
export AWS_PROFILE=your-bedrock-profile
```

## Run Locally

```bash
# Start the voice server (includes elicitation tools)
LOCAL_MODE=true uv run uvicorn voice_server.main:app --host 0.0.0.0 --port 8080 --reload
```

## Capture Intent via Voice

```bash
# Connect via WebSocket client
wscat -c ws://localhost:8080/ws/audio

# Negotiate codec
> {"type": "codec_negotiate", "codec": "pcm", "sample_rate": 16000, "bit_depth": 16, "channels": 1}

# Expect: codec_ack, session_ready
# Then speak your idea into the microphone
# The agent will:
#   1. Listen and form an interpretation
#   2. Present what it understood back to you
#   3. Ask 1-3 clarification questions if needed
#   4. Summarise and ask for confirmation
#   5. Write .intent/INT-001.md on confirmation
```

## Verify Output

```bash
# Check the generated intent document
cat .intent/INT-001.md

# Validate with intent-kit (if installed)
intent check
```

## Expected Output

After a successful voice session, `.intent/INT-001.md` will contain:

```markdown
# Intent: [Your Project Name]

**Intent ID**: INT-001
**Captured**: 2026-05-27
**Actor**: voice
**Status**: confirmed

## Context
[Problem space extracted from your description]

## Intent
[Single sentence capturing the big idea]

## Motivation
[Why now — extracted from your explanation]

## Quality Attributes
- **QA-001**: [Any non-functional requirements you mentioned]

## Success Criteria
- **SC-001**: [Observable outcomes you described]

## Assumptions
- **ASM-001** [medium]: [Things the agent inferred]

## Clarifications
### CLR-001
**Prompt:** [Any question the agent couldn't resolve]
**Resolution:** OPEN
```

## Run Unit Tests

```bash
uv run python -m pytest tests/unit/test_intent_doc.py tests/unit/test_elicitation_tools.py tests/unit/test_storage.py -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INTENT_DIR` | `.intent` | Directory for intent documents (relative to project root) |
