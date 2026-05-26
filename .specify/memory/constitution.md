# Intent Capture Agent Constitution

## Core Principles

### I. Meet Them Where They Are

The agent works in stakeholders' existing channels — voice, chat, meetings, documents. Stakeholders never install tools or learn new interfaces. The technology adapts to them, not the reverse.

### II. Propose, Don't Interrogate

The agent forms an interpretation and presents it for correction. Never batch questions. Every interaction is "here's what I think — tell me where I'm wrong." Corrections are the high-value signal.

### III. Structured Output, Unstructured Input

Regardless of how messy the input (rambling call, fragmented Slack thread, dense Confluence page), the output is always a valid 7-section intent document that passes `intent check`.

### IV. Multi-Source Convergence

A single intent can be assembled from multiple conversations across channels. The agent maintains a unified model that integrates inputs from different people and different channels into one coherent intent.

### V. Channel-Agnostic Core

The elicitation engine (propose-and-steer logic, section mapping, coverage tracking) is the same regardless of channel. Channels are adapters, not separate implementations.

### VI. Graceful Degradation

If voice fails, fall back to text. If the agent can't reach Nova Sonic, it can still conduct text-based capture. If a session is interrupted, state persists and can be resumed.

## Quality Standards

- Voice latency: barge-in response <800ms
- All output passes `intent check` validation
- Sessions survive Nova Sonic 8-minute reconnection transparently
- API responses <200ms for session management endpoints
- Tests cover each channel adapter independently

## Technology Decisions

- **Runtime**: ECS Fargate (required for WebSocket/bidirectional streaming)
- **Voice**: Amazon Nova Sonic 2 via Strands Agents SDK (BidiAgent)
- **Agent Framework**: Strands Agents (Python)
- **API**: FastAPI + Uvicorn
- **State**: DynamoDB
- **IaC**: Terraform

## Governance

- Architecture decisions documented as ADRs in `doc/adr/`
- Channel adapters are independent — adding a new channel doesn't modify existing ones
- Breaking API changes require version bump and migration guide

**Version**: 1.0.0 | **Ratified**: 2026-05-26
