# Feature Specification: Slack Developer Notifications

**Feature Branch**: `006-slack-notifications`

**Created**: 2026-05-27

**Status**: Draft

**Input**: User description: "Developer notification via Slack. When an intent capture session completes (intent finalised), notify the development team via a Slack channel. The notification should include: (1) the project name and intent summary; (2) which fields were captured vs left as open clarifications; (3) a link to the intent document (or its content inline if short); (4) who captured it (actor). Must support configurable webhook URL and channel. Should also notify on session errors that require attention (e.g., voice service unavailable after retries). Follow the channel-adapter pattern from the constitution — Slack is a notification adapter, not a core system."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Intent Finalisation Notification (Priority: P1)

When an intent capture session successfully completes (user confirms and the document is finalised), the development team receives a Slack message summarising what was captured so they can begin downstream work.

**Why this priority**: This is the primary value — developers learn about newly captured intent without checking the filesystem manually. Enables the "capture → notify → act" pipeline.

**Independent Test**: Finalise an intent document, verify a Slack message arrives in the configured channel within 30 seconds containing the project name, intent summary, and actor.

**Acceptance Scenarios**:

1. **Given** an intent document is finalised via the `finalise_intent` tool, **When** the status changes to "confirmed", **Then** a notification is sent to the configured Slack channel within 30 seconds.
2. **Given** a notification is sent, **When** a developer reads it, **Then** they can see the project name, the one-sentence intent, which fields are populated, which have open clarifications, and who captured it.
3. **Given** the intent document is short (under 2000 characters), **When** the notification is composed, **Then** the full document content is included inline in the message.
4. **Given** the intent document is long (over 2000 characters), **When** the notification is composed, **Then** only the summary is included with a note indicating where to find the full document.

---

### User Story 2 - Error Notification (Priority: P2)

When a session encounters an unrecoverable error (voice service unavailable after all retries, critical persistence failure), the team receives an alert-style notification so they can investigate.

**Why this priority**: Errors left unnoticed in logs delay incident response. A Slack alert ensures the team knows immediately when something needs attention.

**Independent Test**: Trigger a voice service unavailable error (all retries exhausted), verify a Slack message arrives with error details and session context.

**Acceptance Scenarios**:

1. **Given** the voice service is unavailable after all retry attempts, **When** the system sends an error to the client, **Then** a Slack notification is also sent to the configured channel with error type, session ID, and timestamp.
2. **Given** an error notification is sent, **When** a developer reads it, **Then** they can identify the affected session and the nature of the error without checking logs.
3. **Given** multiple errors occur in rapid succession, **When** notifications are sent, **Then** they are rate-limited to avoid flooding the channel (maximum 1 error notification per minute per error type).

---

### User Story 3 - Configuration and Disabling (Priority: P3)

Operators can configure the Slack webhook URL, target channel, and notification preferences via environment variables. Notifications can be disabled entirely without code changes.

**Why this priority**: Different environments (dev, staging, prod) need different channels or may not want notifications at all.

**Independent Test**: Set the webhook URL to empty, verify no notifications are sent and no errors occur. Set to a valid URL, verify notifications flow.

**Acceptance Scenarios**:

1. **Given** the webhook URL is not configured (empty or absent), **When** an event that would trigger a notification occurs, **Then** the system silently skips the notification without errors or warnings.
2. **Given** a valid webhook URL is configured, **When** a notification is triggered, **Then** it is delivered to the specified channel.
3. **Given** the notification system encounters a delivery failure (webhook returns error), **When** the failure occurs, **Then** it is logged as a warning but does not affect the core session flow.

---

### Edge Cases

- What happens if the Slack webhook returns a rate-limit response (429)?
- How does the system behave if the webhook URL becomes invalid after deployment?
- What happens if notification delivery is slow (>5 seconds) — does it block the session?
- How are notifications handled during graceful shutdown (intent finalised during drain)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST send a Slack notification when an intent document is finalised (Status changes to "confirmed")
- **FR-002**: Notification MUST include: project name, intent summary (one sentence), populated fields list, open clarifications count, actor name
- **FR-003**: System MUST include full document content inline when under 2000 characters; otherwise include summary only with file path reference
- **FR-004**: System MUST send a Slack notification when an unrecoverable error occurs (voice service unavailable, critical persistence failure)
- **FR-005**: Error notifications MUST include: error type, session ID, timestamp, and brief description
- **FR-006**: Error notifications MUST be rate-limited to maximum 1 per error type per minute
- **FR-007**: Notification delivery MUST be asynchronous — never block the session or audio stream
- **FR-008**: System MUST support configuration via environment variables: webhook URL, channel name, enable/disable toggle
- **FR-009**: System MUST silently skip notifications when webhook URL is not configured (no errors, no warnings)
- **FR-010**: System MUST log delivery failures as warnings without affecting core functionality
- **FR-011**: Notification adapter MUST be independent of the core elicitation logic — adding/removing it does not modify existing modules' behaviour

### Key Entities

- **Notification**: A message to be delivered (type: intent_finalised | error, payload, timestamp)
- **NotificationConfig**: Webhook URL, channel, enabled flag, rate-limit settings
- **DeliveryResult**: Success/failure status, response code, retry count

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers receive notification of newly captured intent within 30 seconds of finalisation
- **SC-002**: Error alerts arrive within 10 seconds of the triggering event
- **SC-003**: Notification delivery adds zero latency to the user-facing session (fully async)
- **SC-004**: System operates normally with notifications disabled — no errors, no performance difference
- **SC-005**: Error notification flooding is prevented — maximum 1 alert per error type per minute regardless of error frequency

## Assumptions

- Slack Incoming Webhooks are used (not the full Slack API) — no OAuth, no bot tokens, just a webhook URL
- The webhook URL is provisioned by the operator and provided as an environment variable
- Notifications are best-effort — delivery failure does not constitute a system error
- The notification adapter is loaded at startup but does nothing if unconfigured
- Rate limiting is in-memory (per-process) — acceptable for single-task ECS deployment
- Message formatting uses Slack Block Kit for rich layout (project name bold, fields as bullet list)
