<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/003-voice-intent-elicitation/plan.md
<!-- SPECKIT END -->

## Project Context

This is the **Intent Capture Agent** — a multi-channel AI service that captures
structured business intent from voice, chat, meetings, and documents.

- Runtime: ECS Fargate (WebSocket + Nova Sonic 2 bidirectional streaming)
- Agent: Strands Agents SDK (BidiAgent for voice, standard Agent for text)
- API: FastAPI + Uvicorn
- State: DynamoDB
- Output: `.intent/intent.md` compatible with intent-kit CLI

See README.md for full architecture and `doc/design/` for detailed designs.
