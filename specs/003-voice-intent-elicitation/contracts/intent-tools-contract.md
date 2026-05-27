# Intent Elicitation Tools Contract

## Overview

Four Strands tools registered on the BidiAgent that enable structured intent capture during voice conversation. The agent invokes these tools autonomously based on conversation context.

---

## Tool: create_intent

Creates a new intent document with mandatory fields populated.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| project_name | str | yes | Human-readable name for the project/idea |
| context | str | yes | Problem space and constraints |
| intent | str | yes | Single declarative sentence — the big idea |
| motivation | str | yes | Why now, cost of inaction |

### Returns

```json
{
  "status": "success",
  "content": [{"text": "Created INT-001 for 'Restaurant Booking System'"}],
  "intent_id": "INT-001",
  "path": ".intent/INT-001.md"
}
```

### Behaviour

- Scans `.intent/` for existing `INT-*.md` files to determine next sequential ID
- Creates `.intent/` directory if it doesn't exist
- Writes document with Status: draft
- Sets `captured_date` to today, `actor` to "voice"
- Atomic write (temp file + rename)

### Error Cases

- Filesystem permission denied → retry once, then return error status
- Invalid intent (empty string) → return validation error

---

## Tool: update_intent_section

Updates a single section of an existing intent document.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| intent_id | str | yes | ID of document to update (e.g., "INT-001") |
| section | str | yes | Section name: "context", "intent", "motivation", "quality_attributes", "success_criteria", "assumptions", "clarifications" |
| content | str | yes | New content for the section (replaces existing) |
| append | bool | no | If true, append to existing content instead of replacing (default: false) |

### Returns

```json
{
  "status": "success",
  "content": [{"text": "Updated motivation section of INT-001"}]
}
```

### Behaviour

- Reads existing document, parses into sections
- Replaces (or appends to) the specified section
- Preserves all other sections unchanged
- Atomic write
- For list sections (quality_attributes, success_criteria, assumptions, clarifications), `append=true` adds new items with auto-incremented IDs

### Error Cases

- Document not found → return error with available intent IDs
- Invalid section name → return error listing valid sections
- Filesystem write failure → retry once, return error if persistent

---

## Tool: read_intent

Reads the current state of an intent document for summarisation.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| intent_id | str | yes | ID of document to read (e.g., "INT-001") |

### Returns

```json
{
  "status": "success",
  "content": [{"text": "# Intent: Restaurant Booking System\n\n**Intent ID**: INT-001\n..."}],
  "populated_sections": ["context", "intent", "motivation"],
  "empty_sections": ["quality_attributes", "success_criteria", "assumptions"]
}
```

### Behaviour

- Reads and returns the full document content
- Reports which sections are populated vs empty (for agent to guide conversation)
- Does not modify the document

### Error Cases

- Document not found → return error listing available documents
- No documents exist → return message suggesting create_intent

---

## Tool: finalise_intent

Marks an intent document as confirmed after user approval.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| intent_id | str | yes | ID of document to finalise (e.g., "INT-001") |

### Returns

```json
{
  "status": "success",
  "content": [{"text": "INT-001 finalised and confirmed. Ready for downstream processing."}]
}
```

### Behaviour

- Validates mandatory fields are populated (context, intent, motivation)
- Changes Status from "draft" to "confirmed"
- Records any empty optional sections as OPEN clarifications
- Atomic write

### Error Cases

- Mandatory fields missing → return error listing which fields need content
- Document already confirmed → return info (idempotent, no error)
- Document not found → return error

---

## Agent System Prompt Extension

The following guidance is prepended to the BidiAgent system prompt when elicitation tools are registered:

```
You are capturing structured business intent through conversation. Your goal is to produce a valid intent document.

APPROACH:
- Listen to what the user describes, then form an interpretation
- Present your understanding back: "So what I'm hearing is..." 
- Use create_intent once you have Context + Intent + Motivation
- Use update_intent_section as you learn more details
- Ask at most 3 clarification questions, targeting scope-critical gaps
- Record anything you can't resolve as an OPEN clarification

COMPLETION:
- When Context, Intent, and Motivation are populated, summarise what you captured
- Ask: "Does this capture your intent accurately?"  
- On confirmation, call finalise_intent
- If the user wants changes, use update_intent_section then re-confirm

STYLE:
- Narrate your actions naturally: "I've noted that as your main motivation"
- Never mention tool names, JSON, or technical internals
- Keep the conversation flowing — don't pause for each field
```

---

## Integration Point

Tools are registered in `src/voice_server/bidi/agent.py` at agent creation:

```python
from voice_server.elicitation.tools import create_intent, update_intent_section, read_intent, finalise_intent

ELICITATION_TOOLS = [create_intent, update_intent_section, read_intent, finalise_intent]

def create_bidi_agent(system_prompt: str | None = None, tools: list | None = None) -> BidiAgent:
    settings = get_settings()
    model = BidiNovaSonicModel(model_id=settings.nova_sonic_model_id)
    all_tools = list(tools or []) + ELICITATION_TOOLS
    return BidiAgent(model=model, system_prompt=system_prompt, tools=all_tools)
```
