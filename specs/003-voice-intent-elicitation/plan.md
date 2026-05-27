# Implementation Plan: Voice Intent Elicitation

**Branch**: `003-voice-intent-elicitation` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-voice-intent-elicitation/spec.md`

## Summary

Wire Strands tools into the BidiAgent so the voice assistant can capture structured intent documents during conversation. The agent uses tools to create/update `.intent/INT-NNN.md` files in intent-kit format, ask targeted clarifications, and confirm with the user before finalising. Tools integrate with the existing AudioBridge from issue #2 — registered at agent creation time.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: strands-agents (BidiAgent tool registration), structlog, pathlib

**Storage**: Local filesystem (`.intent/` directory) — no database for intent documents

**Testing**: pytest + pytest-asyncio, mocked BidiAgent tool calls for unit tests

**Target Platform**: ECS Fargate (same as issues #1/#2)

**Project Type**: Web service extension (adds elicitation tools to existing voice agent)

**Performance Goals**: Tool invocations complete within 100ms (filesystem writes); no perceptible pause in conversation

**Constraints**: Tools must not block the audio stream; Nova Sonic context window must accommodate system prompt + elicitation instructions + conversation history

**Scale/Scope**: Single session captures one intent at a time; `.intent/` directory accumulates documents over project lifetime

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Runtime: ECS Fargate | PASS | Same deployment target |
| Voice: Nova Sonic 2 via Strands BidiAgent | PASS | Tools registered on existing agent |
| Agent: Strands Agents SDK | PASS | Tool registration is a core SDK feature |
| Channel-agnostic core (Principle V) | PASS | Elicitation tools are channel-independent; voice is just the first adapter |
| Propose, Don't Interrogate (Principle II) | PASS | Agent forms interpretation and presents for correction |
| Structured Output (Principle III) | PASS | Output is always valid intent-kit format |
| Graceful Degradation (Principle VI) | PASS | Tool failures retry once, then notify user conversationally |
| All output passes `intent check` | PASS | FR-002 ensures intent-kit format compliance |
| Tests cover adapter independently | PASS | Tool unit tests independent of voice layer |

**Post-Phase 1 re-check**: All gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/003-voice-intent-elicitation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── intent-tools-contract.md  # Tool schemas and behaviour
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (extends existing structure)

```text
src/
└── voice_server/
    ├── bidi/
    │   └── agent.py             # MODIFIED: register elicitation tools
    ├── elicitation/             # NEW: intent elicitation package
    │   ├── __init__.py
    │   ├── tools.py             # Strands tool definitions (create, update, read, finalise)
    │   ├── intent_doc.py        # IntentDocument model (parse/render intent-kit format)
    │   ├── prompts.py           # System prompt extensions for elicitation behaviour
    │   └── storage.py           # Filesystem operations (.intent/ directory management)
    └── config.py                # MODIFIED: add INTENT_DIR config

tests/
├── unit/
│   ├── test_intent_doc.py       # IntentDocument parse/render
│   ├── test_elicitation_tools.py # Tool function behaviour
│   └── test_storage.py          # Filesystem read/write
└── integration/
    └── test_elicitation_flow.py  # Full tool invocation via mocked BidiAgent
```

**Structure Decision**: New `elicitation/` package under `voice_server/` for all intent capture logic. Tools are pure functions registered on the BidiAgent — they don't know about WebSocket or audio. The existing `bidi/agent.py` is modified only to pass tools during agent creation.

## Complexity Tracking

No constitution violations. Table not applicable.
