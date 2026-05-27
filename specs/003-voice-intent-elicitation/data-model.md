# Data Model: Voice Intent Elicitation

## Entities

### IntentDocument

The structured output written to `.intent/INT-NNN.md`.

| Field | Type | Description |
|-------|------|-------------|
| intent_id | str | Unique identifier (INT-001, INT-002, ...) |
| project_name | str | Human-readable project name |
| captured_date | date | When the intent was first created |
| actor | str | Who captured it (default: "voice") |
| status | str | "draft" or "confirmed" |
| context | str | Problem space, constraints, prior art |
| intent | str | Single declarative sentence — the big idea |
| motivation | str | Why now, cost of inaction |
| quality_attributes | list[QualityAttribute] | Non-functional requirements (QA-NNN) |
| success_criteria | list[SuccessCriterion] | Observable outcomes (SC-NNN) |
| assumptions | list[Assumption] | Explicit beliefs with confidence levels (ASM-NNN) |
| clarifications | list[Clarification] | Open questions (CLR-NNN) |

### QualityAttribute

| Field | Type | Description |
|-------|------|-------------|
| id | str | QA-NNN format |
| description | str | Specific non-functional requirement |

### SuccessCriterion

| Field | Type | Description |
|-------|------|-------------|
| id | str | SC-NNN format |
| description | str | Measurable, observable outcome |

### Assumption

| Field | Type | Description |
|-------|------|-------------|
| id | str | ASM-NNN format |
| confidence | str | "high", "medium", or "low" |
| description | str | What is assumed to be true |

### Clarification

| Field | Type | Description |
|-------|------|-------------|
| id | str | CLR-NNN format |
| prompt | str | The question |
| resolution | str | Answer text, or "OPEN" if unresolved |

## Relationships

```
IntentDocument 1 ──── * QualityAttribute
IntentDocument 1 ──── * SuccessCriterion
IntentDocument 1 ──── * Assumption
IntentDocument 1 ──── * Clarification
```

## State Transitions

```
                 create_intent()
                       │
                       ▼
              ┌─────────────────┐
              │  Status: draft  │ ←── update_intent_section()
              └────────┬────────┘       (loops back)
                       │
              finalise_intent()
                       │
                       ▼
            ┌───────────────────────┐
            │  Status: confirmed    │
            └───────────────────────┘
```

## Validation Rules

- `intent_id` must be unique within the `.intent/` directory
- `intent` field must be a single sentence (no line breaks)
- `status` must be one of: "draft", "confirmed"
- Finalisation requires: context, intent, and motivation to be non-empty
- Quality Attributes, Success Criteria, Assumptions are optional for finalisation but prompted
- Clarifications with resolution "OPEN" block nothing (informational for downstream)
- `captured_date` is set once at creation, never modified

## Filesystem Layout

```
.intent/
├── INT-001.md          # First captured intent
├── INT-002.md          # Second captured intent
├── .INT-003.md.tmp     # Temporary file during atomic write (cleaned up)
└── ...
```
