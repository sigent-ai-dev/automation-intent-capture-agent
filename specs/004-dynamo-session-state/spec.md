# Feature Specification: DynamoDB Session State Persistence

**Feature Branch**: `004-dynamo-session-state`

**Created**: 2026-05-27

**Status**: Draft

**Input**: User description: "Session state persistence using DynamoDB. Currently all session data (WebSocket sessions, conversation history, elicitation state) lives in-memory and is lost on deploy/restart. Persist session state to DynamoDB so that: (1) active sessions survive container restarts/deploys via graceful drain + resume; (2) conversation history from the BidiAgent is durable across reconnections; (3) elicitation progress (which intent fields captured, draft status) is recoverable across sessions; (4) session cleanup runs automatically via DynamoDB TTL. Must integrate with the existing SessionRegistry, ConversationHistory, and elicitation storage modules. Table design should support the access patterns: get session by ID, list active sessions, get history by session ID."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Session Survives Deployment (Priority: P1)

A user is mid-conversation when a new version of the service deploys. The container drains gracefully (saving session state), the new container starts, and the user reconnects. Their session resumes exactly where they left off — no lost context, no repeated questions.

**Why this priority**: Without this, every deploy breaks active conversations. In a CI/CD pipeline deploying multiple times daily, this is unacceptable for production use.

**Independent Test**: Start a voice session, capture some intent fields, simulate a container restart, reconnect, verify the agent picks up where it left off with full context preserved.

**Acceptance Scenarios**:

1. **Given** a user has an active session with conversation history, **When** the service receives a shutdown signal, **Then** all active session state is persisted before the container exits.
2. **Given** a session was persisted during shutdown, **When** the user reconnects to the new container, **Then** the system loads their previous session state and the agent continues with full context.
3. **Given** a session was active less than 30 minutes ago, **When** the user reconnects, **Then** the resume happens within 2 seconds (no perceptible delay beyond WebSocket reconnection).

---

### User Story 2 - Durable Conversation History (Priority: P1)

Conversation history from voice sessions persists across Nova Sonic reconnections (8-minute limit) and service restarts. The sliding window + summary model is backed by durable storage rather than in-memory state.

**Why this priority**: The 8-minute reconnection already uses in-memory history for replay. If that memory is lost (OOM, crash, deploy), the agent loses all conversation context mid-session.

**Independent Test**: Build conversation history over multiple turns, simulate process crash, restart service, verify history is intact and agent can summarise previous turns.

**Acceptance Scenarios**:

1. **Given** a conversation has 15+ turns, **When** the service process crashes and restarts, **Then** conversation history (summary + recent turns) is fully recoverable from persistent storage.
2. **Given** a Nova Sonic reconnection occurs at the 7-minute mark, **When** history is replayed to the new connection, **Then** the history is loaded from durable storage rather than relying solely on in-memory state.
3. **Given** a long conversation spanning multiple reconnections, **When** the user asks for a summary, **Then** the agent can access the complete conversation history including turns from before the most recent reconnection.

---

### User Story 3 - Recoverable Elicitation Progress (Priority: P2)

A user starts capturing intent via voice, disconnects (intentionally or not), and returns later. The system remembers which fields were captured, which are still needed, and which clarifications are outstanding — without re-reading the filesystem.

**Why this priority**: The filesystem-based `.intent/` storage works for the final document, but in-progress elicitation state (which questions asked, which fields confirmed) was ephemeral. This makes multi-session capture reliable.

**Independent Test**: Start intent capture, populate Context and Intent fields, disconnect, reconnect hours later, verify the system knows Motivation is still needed without re-parsing the file.

**Acceptance Scenarios**:

1. **Given** a user has partially completed intent capture, **When** they reconnect after any duration, **Then** the system knows exactly which fields are populated and which are outstanding.
2. **Given** the agent asked a clarification question before disconnection, **When** the user returns, **Then** the system does not re-ask the same question.
3. **Given** elicitation state is stored durably, **When** the filesystem-based intent document is also present, **Then** the durable state is authoritative for session continuity (filesystem document is the final output artifact).

---

### User Story 4 - Automatic Session Cleanup (Priority: P2)

Stale sessions (no activity for a configurable period) are automatically removed without manual intervention or cron jobs. The system doesn't accumulate abandoned session data indefinitely.

**Why this priority**: Without cleanup, the session table grows unbounded. DynamoDB TTL provides zero-cost automatic expiration without application logic.

**Independent Test**: Create a session, wait beyond the TTL period, verify the session record no longer exists and doesn't appear in active session listings.

**Acceptance Scenarios**:

1. **Given** a session has had no activity for the configured timeout period, **When** the TTL expires, **Then** the session record is automatically removed without application intervention.
2. **Given** a session is actively being used, **When** each interaction occurs, **Then** the TTL is refreshed so the session is never prematurely cleaned up.
3. **Given** a session is cleaned up by TTL, **When** the user returns after cleanup, **Then** they get a fresh session (no stale partial state confusing the agent).

---

### Edge Cases

- What happens if DynamoDB is unreachable during session save (deploy drain timeout)?
- How does the system handle split-brain — stale session in DynamoDB but user starts fresh?
- What happens if two containers try to resume the same session simultaneously?
- How does the system handle session data that exceeds DynamoDB's 400KB item limit?
- What happens during a partition (session persisted but cannot be read back)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist session state (connection metadata, session ID, user ID, timestamps) to durable storage on every significant state change
- **FR-002**: System MUST persist conversation history (turns + summary) to durable storage after each completed turn
- **FR-003**: System MUST persist elicitation progress (populated fields, outstanding clarifications, confirmation status) after each tool invocation
- **FR-004**: System MUST load session state on reconnection using strongly consistent reads and restore the session to its previous state within 2 seconds
- **FR-005**: System MUST persist all active sessions during graceful shutdown (SIGTERM handling), retrying for the full drain window duration; if storage remains unavailable, log which sessions could not be persisted and exit gracefully
- **FR-006**: System MUST automatically expire stale sessions after a configurable timeout (default: 24 hours of inactivity)
- **FR-007**: System MUST refresh session expiry on every interaction (TTL reset)
- **FR-008**: System MUST support looking up a session by its ID (primary access pattern)
- **FR-009**: System MUST support listing all active sessions using eventually consistent reads (for admin/monitoring purposes)
- **FR-010**: System MUST support retrieving conversation history by session ID
- **FR-011**: System MUST handle storage unavailability gracefully — continue operating with in-memory state and retry persistence when available
- **FR-012**: System MUST integrate with existing SessionRegistry, ConversationHistory, and elicitation storage modules via write-through adapters — in-memory state stays hot for performance, durable storage is the async backup
- **FR-013**: System MUST use a single-table design with composite key (PK=session_id, SK=record_type) for all session-related data

### Key Entities

- **SessionRecord**: Durable representation of a WebSocket session (ID, user ID, state, connected_at, last_activity, TTL)
- **HistoryRecord**: Conversation turns and summary for a session (session ID, turns, summary, updated_at)
- **ElicitationRecord**: In-progress intent capture state (session ID, intent ID, populated fields, outstanding clarifications, status)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Sessions resume within 2 seconds of reconnection after a deploy (measured from WebSocket handshake to agent response)
- **SC-002**: Zero data loss during planned deployments — 100% of active sessions recoverable after graceful shutdown
- **SC-003**: Stale sessions (no activity for 24 hours) are automatically cleaned up without operator intervention
- **SC-004**: System operates normally when persistent storage is temporarily unavailable (degrades to in-memory, recovers when storage returns)
- **SC-005**: Conversation history survives process crashes — at most 1 turn of history lost (the turn in progress at crash time)
- **SC-006**: Storage operations add less than 50ms latency to request handling (async writes, not blocking the audio stream)

## Clarifications

### Session 2026-05-27

- Q: Single table or multiple tables for DynamoDB? → A: Single table with composite key (PK=session_id, SK=record_type#timestamp).
- Q: Read consistency model for session resume vs listings? → A: Strong consistency for session resume; eventual consistency for admin listings.
- Q: How does persistence integrate with existing modules? → A: Write-through adapter — in-memory stays hot, DynamoDB is async backup.
- Q: Behaviour on DynamoDB unavailability during shutdown drain? → A: Retry for drain window duration, log failures, exit gracefully.

## Assumptions

- The service runs on ECS Fargate with SIGTERM-based graceful shutdown (30-second drain period)
- DynamoDB is available in the same AWS region as the ECS tasks
- Session data per user fits within storage item size limits (conversation history is summarised, not unbounded)
- The existing in-memory interfaces (SessionRegistry, ConversationHistory) can be backed by a persistence layer without changing their public API
- Single-writer per session — only one container handles a given session at a time (load balancer sticky sessions or session routing)
- TTL-based cleanup is sufficient — no need for active garbage collection
