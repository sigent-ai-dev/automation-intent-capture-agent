# Intent Capture Agent

**Meet stakeholders where they are.** Multi-channel AI agent that captures structured business intent from voice calls, chat messages, meetings, and collaboration tools — producing a valid Intent Kit `.intent/intent.md` regardless of input source.

## The Problem

Business intent lives in people's heads, meeting recordings, Slack threads, Confluence pages, and email chains. Developers need it structured as a 7-section intent document before they can begin architecture and implementation. Today this requires a technical person to manually interview stakeholders and write up the intent.

Intent Capture Agent automates this — it conducts propose-and-steer elicitation across any channel the stakeholder already uses, and produces output compatible with [Intent Kit](https://github.com/sigent-ai-dev/intent-kit).

## Channels

| Channel | How It Works | Best For |
|---------|-------------|----------|
| **Voice** | Real-time conversation via browser, phone, or meeting bot (Nova Sonic 2) | Live stakeholder sessions, workshops |
| **Chat** | Slack/Teams bot conducts async propose-and-steer in a thread | Busy stakeholders, distributed teams |
| **Meeting** | Joins Teams/Zoom as a participant, chairs intent capture session | Group workshops, architecture reviews |
| **Document** | Ingests existing docs (Confluence, Notion, email) and extracts intent | When intent already exists but isn't structured |

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                        Input Channels                              │
├──────────┬──────────┬──────────────┬────────────┬────────────────┤
│  Voice   │  Chat    │  Meeting     │  Document  │  Email         │
│  (Nova   │  (Slack  │  (Teams/Zoom │  (Conflu-  │  (Forward to   │
│  Sonic 2)│  /Teams) │  bot)        │  ence/     │  agent)        │
│          │          │              │  Notion)   │                │
└────┬─────┴────┬─────┴──────┬───────┴─────┬──────┴───────┬────────┘
     │          │            │             │              │
     └──────────┴────────────┴─────────────┴──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Elicitation    │
                    │  Engine         │
                    │                 │
                    │  Propose-and-   │
                    │  Steer across   │
                    │  all channels   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Intent Builder │
                    │                 │
                    │  7-section      │
                    │  schema mapper  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Output         │
                    │                 │
                    │  .intent/       │
                    │  intent.md      │
                    │  state.json     │
                    │  audit.md       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Notify         │
                    │  Developer      │
                    └─────────────────┘
```

## Core Principles

1. **Meet them where they are** — stakeholders shouldn't need to learn new tools. The agent works in their existing channels.
2. **Propose, don't interrogate** — the agent forms an interpretation and presents it for correction, not a batch of questions.
3. **Multi-source convergence** — a single intent can be assembled from multiple conversations across channels (voice session with CTO + Slack thread with product + Confluence doc from architect).
4. **Structured output, unstructured input** — regardless of how messy the input, the output is always a valid 7-section intent document that passes `intent check`.
5. **Developer handoff** — capture completes, developer gets notified, continues with `/intent.steer`.

## Architecture

- **Runtime**: ECS Fargate (long-lived WebSocket connections for voice/meetings)
- **Voice Engine**: Amazon Nova Sonic 2 via Strands Agents SDK (`BidiAgent`)
- **Agent Framework**: Strands Agents (Python) with custom elicitation tools
- **Chat**: Slack Bot SDK / Teams Bot Framework
- **Document Ingestion**: Bedrock (Claude) for extraction + summarisation
- **State**: DynamoDB for session persistence
- **Notification**: Slack webhook / nexctl pattern

See [`doc/design/architecture.md`](./doc/design/architecture.md) for the full architecture document.

## Personas

| Persona | Typical Channel | Interaction Style |
|---------|----------------|-------------------|
| **Business Stakeholder** | Voice, Chat | Non-technical. Describes outcomes, not solutions. Propose-and-steer works best. |
| **Product Owner** | Chat, Document | Has existing artifacts (PRDs, user stories). Agent extracts and structures. |
| **Architect** | Voice (meeting), Document | Technical. Discusses trade-offs. Agent surfaces quality attributes and constraints. |
| **Executive Sponsor** | Voice (brief call) | Time-constrained. Agent confirms interpretation quickly ("2-minute capture"). |

## Status

Early design. See [intent-kit#26](https://github.com/sigent-ai-dev/intent-kit/issues/26) for the design issue and related sub-issues (#29-#38).

## Related Projects

- [Intent Kit](https://github.com/sigent-ai-dev/intent-kit) — CLI tool that consumes the output (`.intent/intent.md`)
- [Spec Kit](https://github.com/github/spec-kit) — downstream specification workflow
- [nexctl](https://github.com/sigent-ai-dev/nexctl) — notification patterns for developer handoff

## License

[MIT](./LICENSE)
