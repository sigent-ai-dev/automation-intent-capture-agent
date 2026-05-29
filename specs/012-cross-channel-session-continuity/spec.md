# Feature Specification: Cross-Channel Session Continuity

**Feature Branch**: `012-cross-channel-session-continuity`

**Created**: 2026-05-29

**Status**: Draft

**Input**: User description: "Cross-channel session continuity. When a user starts an intent capture session on one channel (e.g., voice via web browser), they should be able to continue that same elicitation on another channel (Slack bot, Claude skill) without losing context. The system needs: (1) a user_id-to-intent_id mapping in DynamoDB so any channel can discover the user's active intent capture; (2) conversation history stored per intent_id (not per WebSocket session) so new channels inherit prior context; (3) a channel field on intent documents tracking which channel(s) contributed; (4) inbound channel adapters (Slack bot, Claude skill) that reuse the existing elicitation tools and resume prompt. The intent document on the filesystem is already shared, but DynamoDB state, conversation history, and session identity are all scoped to a single WebSocket connection today. See issue #25 for full details."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resume Elicitation on a Different Channel (Priority: P1)

A stakeholder begins an intent capture session via voice in the browser, covering context and motivation. Later, they open Slack and continue the same session — the system picks up where they left off without re-asking completed questions.

**Why this priority**: This is the core value proposition — multi-source convergence (Constitution IV). Without it, each channel is an isolated silo and stakeholders must repeat themselves.

**Independent Test**: Start a voice session, populate 3 of 6 sections, end the session. Open a Slack thread with the bot, verify it greets you with awareness of the existing draft and guides you through the remaining 3 sections.

**Acceptance Scenarios**:

1. **Given** a user has an in-progress intent capture (status "draft") from a voice session, **When** they initiate a conversation on Slack, **Then** the system identifies their active draft and resumes from the current state.
2. **Given** the system resumes on a new channel, **When** it presents the current progress, **Then** it shows which sections are populated and which remain, without re-asking questions already answered.
3. **Given** sections were captured on voice, **When** the user adds detail on Slack, **Then** the intent document reflects contributions from both channels.

---

### User Story 2 - Discover Active Intent by User Identity (Priority: P1)

Any channel adapter can look up whether a given user has an active (draft) intent capture session, enabling seamless handoff without the user needing to provide an intent ID manually.

**Why this priority**: Cross-channel continuity depends entirely on this lookup — without it, the user would need to remember and type their intent ID on every new channel.

**Independent Test**: Create a draft intent via voice for user "alice@example.com". Query the system from a different adapter with only the user identity. Verify the system returns the correct in-progress intent ID and its current state.

**Acceptance Scenarios**:

1. **Given** a user has exactly one draft intent, **When** a channel adapter queries by user identity, **Then** the system returns that intent's ID, project name, and progress summary.
2. **Given** a user has multiple draft intents, **When** a channel adapter queries by user identity, **Then** the system returns all drafts sorted by most recently active, and prompts the user to select one.
3. **Given** a user has no active intents, **When** a channel adapter queries by user identity, **Then** the system indicates no active capture exists and offers to start a new one.

---

### User Story 3 - Conversation History Carries Across Channels (Priority: P2)

When a user resumes on a new channel, the elicitation agent has access to the full conversation history from prior channels, enabling it to avoid redundant questions and build on prior context.

**Why this priority**: Without shared history, the agent can only see the intent document state (which sections are filled) but not the nuance of the conversation — why certain decisions were made, what alternatives were discussed, or what the user's tone suggested.

**Independent Test**: Conduct a 5-turn voice conversation populating context and intent sections. Resume on Slack. Verify the agent's first message references specific details from the voice conversation, not just generic awareness of populated fields.

**Acceptance Scenarios**:

1. **Given** a voice session produced 10 conversation turns, **When** a Slack session resumes the same intent, **Then** the agent has access to all 10 prior turns as conversation history.
2. **Given** conversation history exists from multiple channels, **When** the history is loaded, **Then** each turn is annotated with its source channel and timestamp.
3. **Given** conversation history is long (over 30 turns), **When** a new channel resumes, **Then** the system provides a summarised context window (oldest turns condensed, most recent 30 verbatim) to stay within agent context limits.

---

### User Story 4 - Channel Attribution on Intent Documents (Priority: P3)

The intent document records which channel(s) contributed to each section, providing an audit trail of how the intent was assembled across sources.

**Why this priority**: Supports traceability and helps developers understand the provenance of each piece of captured intent. Lower priority because it's informational rather than functional.

**Independent Test**: Capture context via voice and motivation via Slack. Render the intent document. Verify each section has a channel attribution annotation.

**Acceptance Scenarios**:

1. **Given** a section is populated via voice, **When** the intent document is rendered, **Then** the section includes a channel attribution (e.g., "via voice, 2026-05-29").
2. **Given** a section is updated across multiple channels, **When** the document is rendered, **Then** the attribution shows the most recent contributing channel.
3. **Given** the intent document is exported for Intent Kit, **When** it is validated, **Then** it passes `intent check` regardless of channel attributions (attributions are metadata, not content).

---

### Edge Cases

- What happens when two channels attempt to update the same section simultaneously? (Last-write-wins at section level — no locking between channels)
- How does the system behave when a voice session is active and a Slack message arrives for the same intent? (Both proceed concurrently; section-level last-write-wins resolves conflicts)
- What happens when the conversation history exceeds 30 turns? (Older turns are summarised; most recent 30 turns are provided verbatim to the agent)
- How does the system handle a user whose identity differs across channels? (Email is canonical — extracted from Cognito claims and Slack profile; channels without email cannot participate in cross-channel continuity)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow any channel adapter to discover a user's active (draft) intent captures by user identity
- **FR-002**: System MUST store conversation history keyed by intent ID as the partition key (migrating from session_id keying), with all turns stored in a single item
- **FR-003**: System MUST annotate each conversation turn with its source channel and timestamp
- **FR-004**: System MUST provide the full cross-channel conversation history to the elicitation agent when resuming on a new channel
- **FR-005**: System MUST summarise conversation history when it exceeds 30 turns — recent turns are provided verbatim while older turns are condensed into a structured summary
- **FR-006**: System MUST track which channel contributed to each intent document section
- **FR-007**: System MUST support concurrent intent captures (multiple drafts per user) with user selection when ambiguous
- **FR-008**: System MUST handle simultaneous access from multiple channels to the same intent using last-write-wins at the section level — concurrent channels operate independently and the most recent section update prevails
- **FR-009**: System MUST resolve user identity across channels using email address as the canonical key — extracted from Cognito token claims and Slack user profile
- **FR-010**: System MUST maintain backward compatibility — existing voice-only sessions continue to work without requiring cross-channel features
- **FR-011**: System MUST allow channel adapters to register independently — adding a new channel does not require modifying existing adapters. This feature delivers both Slack inbound and Claude skill adapters alongside the shared session layer
- **FR-012**: Intent documents produced with cross-channel contributions MUST pass `intent check` validation (Intent Kit compatibility)

### Key Entities

- **UnifiedUser**: A user identified by email address, resolved from channel-specific auth (Cognito token email claim, Slack profile email)
- **IntentSession**: A cross-channel session tied to an intent ID, tracking state, participants, and active channel
- **ConversationTurn**: A single message in the elicitation conversation, annotated with channel, timestamp, and role (user/agent)
- **ChannelContribution**: Metadata recording which channel populated or last updated a given intent section

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can resume an in-progress intent capture on a different channel within 10 seconds of identifying themselves
- **SC-002**: Cross-channel resume retains full conversation context — the agent does not re-ask questions already answered on another channel
- **SC-003**: System delivers all 3 channel types (voice, Slack inbound, Claude skill) in this feature without requiring changes to the core elicitation engine
- **SC-004**: Intent documents produced via multiple channels pass `intent check` validation with 100% compatibility
- **SC-005**: Simultaneous access from two channels does not result in data loss or corruption
- **SC-006**: Adding a new channel adapter requires no modifications to existing adapters or the core elicitation logic

## Assumptions

- Email address is the canonical user identifier across all channels — Cognito tokens contain email claims, Slack profiles expose verified email via `users.info` API
- DynamoDB is the persistence layer for cross-channel state — conversation history uses intent_id as partition key with all turns in a single item (400KB limit is sufficient for 30 verbatim turns + summaries of older turns)
- Conversation history summarisation uses the same LLM that powers elicitation (no additional model dependency); threshold is 30 turns — older turns are summarised, most recent 30 preserved verbatim
- Intent Kit `.intent/intent.md` format does not change — channel attribution is stored as metadata alongside the document, not within the 7-section schema
- The existing elicitation tools (`create_intent`, `update_intent_section`, `finalise_intent`) are reused by all channel adapters without modification
- Slack inbound integration uses Slack Events API (bot mentions or DMs), not slash commands
- Concurrent access uses last-write-wins at section granularity — no distributed locking required; DynamoDB conditional writes protect against item-level corruption but section conflicts resolve by timestamp

## Clarifications

### Session 2026-05-29

- Q: How should simultaneous access from multiple channels be handled? → A: Allow concurrent access with last-write-wins at section level
- Q: How should user identity be resolved across channels? → A: Email address as canonical key — extracted from Cognito token claims and Slack profile
- Q: At what threshold should conversation history be summarised? → A: After 30 turns — recent verbatim, older summarised
- Q: Which inbound channel adapters are in scope for this feature? → A: Both Slack inbound and Claude skill — full 3-channel support
- Q: Where should intent-keyed conversation history be stored? → A: DynamoDB with intent_id as partition key (single item per intent)
