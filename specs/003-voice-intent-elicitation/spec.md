# Feature Specification: Voice Intent Elicitation

**Feature Branch**: `003-voice-intent-elicitation`

**Created**: 2026-05-27

**Status**: Draft

**Input**: User description: "Wire Strands tools into the BidiAgent for structured intent elicitation. During voice conversation, the agent should use tools to: (1) create/update a structured intent document (.intent/intent.md) capturing who, what, why, constraints, and success criteria; (2) ask targeted clarification questions when intent fields are underspecified; (3) confirm captured intent with the user before finalising. The elicitation flow should work conversationally — the agent guides the user through intent capture naturally, not as a rigid form-fill. Tools must integrate with the existing AudioBridge and BidiAgent from issue #2. Output format must be compatible with intent-kit CLI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversational Intent Capture (Priority: P1)

A user starts a voice session and describes a business idea or project need. The agent listens, extracts key intent fields (who, what, why, constraints, success criteria), and progressively builds a structured intent document through natural conversation — asking follow-up questions only when critical information is missing.

**Why this priority**: This is the core value proposition — transforming unstructured voice into structured, actionable intent documents that downstream tools (intent-kit, Spec Kit) can consume.

**Independent Test**: Start a voice session, describe a project idea (e.g., "I want to build a booking system for my restaurant"), verify that the agent produces a valid `.intent/INT-001.md` file with populated Context, Intent, and Motivation sections.

**Acceptance Scenarios**:

1. **Given** an active voice session with the BidiAgent, **When** the user describes their idea in natural speech, **Then** the agent extracts intent fields and begins building a structured intent document without requiring the user to follow a rigid template.
2. **Given** the user has provided a high-level description, **When** the agent identifies missing critical fields (e.g., no success criteria mentioned), **Then** it asks a targeted follow-up question conversationally (e.g., "How would you know this is working well?") rather than listing all missing fields at once.
3. **Given** the agent has captured sufficient intent, **When** the intent document has all mandatory fields populated, **Then** the agent summarises what it captured and asks the user to confirm before finalising.
4. **Given** the user confirms the captured intent, **When** finalisation occurs, **Then** the system writes a valid `.intent/INT-NNN.md` file in intent-kit format with proper frontmatter (Intent ID, Captured date, Actor, Status: confirmed).

---

### User Story 2 - Iterative Refinement (Priority: P1)

The user reviews the captured intent (via the agent reading it back) and provides corrections or additions. The agent updates the document incrementally without losing previously captured information.

**Why this priority**: Real conversations are non-linear — users clarify, correct, and add context as they think through their idea. The system must handle iterative refinement to be useful.

**Independent Test**: Capture initial intent, then say "Actually, I also need it to handle group bookings" — verify the document is updated to include the new requirement without losing existing content.

**Acceptance Scenarios**:

1. **Given** an intent document has been partially captured, **When** the user provides additional context or corrections, **Then** the agent updates the relevant section(s) without overwriting unrelated content.
2. **Given** the user says something that contradicts previously captured intent, **When** the agent detects the contradiction, **Then** it acknowledges the change and updates the document, noting the revision.
3. **Given** the user wants to hear what's been captured so far, **When** they ask for a summary, **Then** the agent reads back the current state of the intent document in natural language.

---

### User Story 3 - Clarification Elicitation (Priority: P2)

When the user's description is ambiguous or underspecified in ways that would meaningfully impact downstream work, the agent asks targeted clarification questions — prioritised by impact on scope, then feasibility, then quality.

**Why this priority**: Clarifications prevent expensive misunderstandings later. However, over-questioning frustrates users, so the agent must be selective.

**Independent Test**: Describe a vague idea ("I want an app for my business"), verify the agent asks 2-3 high-impact questions (what does the business do? who are the users?) rather than interrogating with 10+ questions.

**Acceptance Scenarios**:

1. **Given** the user provides a vague or ambiguous description, **When** multiple reasonable interpretations exist with different scope implications, **Then** the agent asks a focused clarification question targeting the most impactful ambiguity.
2. **Given** the agent has asked a clarification question, **When** the user responds, **Then** the agent incorporates the answer into the intent document and only asks another question if a remaining gap is critical.
3. **Given** the user indicates they want to move on (e.g., "that's enough for now"), **When** mandatory fields are still empty, **Then** the agent records the gaps as open clarifications in the document rather than blocking progress.

---

### User Story 4 - Multi-Session Continuity (Priority: P3)

A user returns to a previously started intent capture session. The agent loads the existing intent document and continues where the conversation left off, without re-asking questions that have already been answered.

**Why this priority**: Complex intents may span multiple conversations. Users shouldn't have to repeat themselves.

**Independent Test**: Start an intent capture session, partially complete it, disconnect, reconnect, verify the agent acknowledges existing progress and picks up from where it left off.

**Acceptance Scenarios**:

1. **Given** an intent document exists from a previous session, **When** the user starts a new voice session for the same project, **Then** the agent acknowledges existing progress and asks what they'd like to add or change.
2. **Given** a partially complete intent document, **When** the agent resumes, **Then** it identifies the most critical remaining gaps and gently guides the user toward filling them.

---

### Edge Cases

- What happens if the user provides contradictory requirements in a single utterance?
- How does the system handle very short/terse responses to clarification questions (e.g., "yes", "no", "dunno")?
- What happens if the user switches topics mid-conversation (e.g., starts describing a different project)?
- How does the agent handle domain-specific jargon it doesn't understand?
- What happens if the voice connection drops during finalisation (intent partially written)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide Strands tools that the BidiAgent can invoke during voice conversation to create and update intent documents
- **FR-002**: System MUST produce intent documents in the intent-kit format (frontmatter: Intent ID, Captured date, Actor; sections: Context, Intent, Motivation, Quality Attributes, Success Criteria, Assumptions, Clarifications)
- **FR-003**: System MUST store intent documents at `.intent/INT-NNN.md` (e.g., `.intent/INT-001.md`) within the project directory, accumulating multiple intents over time
- **FR-004**: Agent MUST extract intent fields conversationally from natural speech without requiring users to follow a rigid template or answer fields in order
- **FR-005**: Agent MUST ask targeted clarification questions when critical intent fields cannot be reasonably inferred — maximum 3 questions before offering to proceed with documented gaps
- **FR-006**: Agent MUST summarise captured intent and request user confirmation before finalising the document
- **FR-007**: System MUST support incremental updates — adding or modifying individual sections without overwriting the entire document
- **FR-008**: System MUST preserve previously captured content when the user provides corrections or additions
- **FR-009**: Agent MUST integrate with the existing AudioBridge and BidiAgent lifecycle from issue #2 — tools are registered at agent creation time
- **FR-010**: System MUST generate unique Intent IDs (format: INT-NNN, incrementing from existing documents)
- **FR-011**: Agent MUST be able to read back the current state of captured intent when the user asks for a summary
- **FR-012**: Agent MUST narrate its actions naturally (e.g., "I've captured that as your main motivation") without exposing tool names or mechanics to the user
- **FR-013**: On tool failure, system MUST retry silently once; if still failing, agent MUST inform user conversationally and buffer the content in memory
- **FR-014**: Agent MUST only offer finalisation when Context, Intent, and Motivation sections are populated; other sections are prompted but deferrable
- **FR-015**: Session state (draft vs confirmed, open clarifications) MUST be stored within the intent document itself via a `Status` frontmatter field and the Clarifications section — no separate state file

### Key Entities

- **IntentDocument**: The structured output — maps to `.intent/INT-NNN.md` with frontmatter (Intent ID, Captured, Actor, Status) + sections
- **IntentField**: Individual sections within the document (Context, Intent, Motivation, Quality Attributes, Success Criteria, Assumptions, Clarifications)
- **Clarification**: An open question recorded when the user cannot or chooses not to resolve an ambiguity
- **ElicitationSession**: The conversational state tracked within the intent document's frontmatter (`Status: draft|confirmed`) and Clarifications section (open questions from previous sessions)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can describe a project idea in natural speech and receive a valid, structured intent document within a single voice session (under 10 minutes for a typical idea)
- **SC-002**: Generated intent documents are parseable by intent-kit CLI without modification (100% format compliance)
- **SC-003**: The agent asks no more than 5 clarification questions per session — the rest is inferred or recorded as open clarifications
- **SC-004**: Users can iteratively refine captured intent without the agent losing or overwriting previously captured content
- **SC-005**: The agent correctly populates at least 4 of the 6 intent sections (Context, Intent, Motivation, Quality Attributes, Success Criteria, Assumptions) from a single 3-minute description

## Clarifications

### Session 2026-05-27

- Q: How are multiple intents stored — one file overwritten or accumulating? → A: Multiple intents accumulate as `.intent/INT-001.md`, `.intent/INT-002.md`, etc.
- Q: Should tool invocations be visible to the user during conversation? → A: Agent narrates actions naturally ("I've noted that...") without exposing tool names or mechanics.
- Q: How should the agent handle tool failures during voice conversation? → A: Silent retry once, then conversational notification if persistent failure.
- Q: What minimum fields must be populated before offering finalisation? → A: Context + Intent + Motivation mandatory; Quality Attributes, Success Criteria, Assumptions prompted but deferrable.
- Q: Where is in-progress elicitation state persisted between sessions? → A: In the intent document itself via `Status` frontmatter field + Clarifications section.

## Assumptions

- The BidiAgent and AudioBridge from issue #2 are fully functional and available for tool registration
- intent-kit CLI format is stable and follows the structure seen in intent-kit's example documents (frontmatter + markdown sections)
- Users will describe their intent in English
- A single voice session typically lasts 5-15 minutes for intent capture
- The system runs locally with filesystem access to write `.intent/INT-NNN.md` files
- Intent IDs are scoped per project directory (no cross-project deduplication needed)
- Multiple intent documents accumulate in `.intent/` over time (one per captured intent)
- The agent's system prompt can be extended to include elicitation guidance without exceeding Nova Sonic's context limits
