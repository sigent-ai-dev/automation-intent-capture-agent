# Contract: Claude Skill Adapter

## Purpose

Expose intent capture as an MCP tool that Claude Code (or other Claude interfaces) can invoke for text-based elicitation.

## MCP Tool: `intent_capture`

**Description**: Start or resume an intent capture session. The agent conducts propose-and-steer elicitation to produce a structured intent document.

### Tool Input Schema

```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["start", "resume", "message", "status", "list"],
      "description": "Action to perform"
    },
    "intent_id": {
      "type": "string",
      "description": "Intent ID to resume or message (required for resume/message)"
    },
    "message": {
      "type": "string",
      "description": "User message for the elicitation agent (required for message action)"
    },
    "project_name": {
      "type": "string",
      "description": "Project name (required for start action)"
    }
  },
  "required": ["action"]
}
```

### Actions

#### `list` — List active intent captures

**Input**: `{"action": "list"}`

**Output**:
```json
{
  "intents": [
    {
      "intent_id": "INT-001",
      "project_name": "Restaurant Booking",
      "progress": "3/6 sections",
      "last_activity": "2026-05-29T14:30:00Z",
      "last_channel": "voice"
    }
  ]
}
```

#### `start` — Begin a new intent capture

**Input**: `{"action": "start", "project_name": "New Feature X"}`

**Output**:
```json
{
  "intent_id": "INT-003",
  "agent_response": "Let's capture intent for 'New Feature X'. Tell me about the context — what problem are you trying to solve and who are the stakeholders?"
}
```

#### `resume` — Resume an existing intent

**Input**: `{"action": "resume", "intent_id": "INT-001"}`

**Output**:
```json
{
  "intent_id": "INT-001",
  "agent_response": "Picking up where you left off on 'Restaurant Booking'. You've covered context, intent, and motivation. What quality attributes matter most?",
  "progress": {
    "populated": ["context", "intent", "motivation"],
    "remaining": ["quality_attributes", "success_criteria", "assumptions"]
  }
}
```

#### `message` — Send a message within active session

**Input**: `{"action": "message", "intent_id": "INT-001", "message": "Performance is critical — searches under 200ms"}`

**Output**:
```json
{
  "agent_response": "Got it — I've noted sub-200ms search latency as a quality attribute. What about reliability? Any uptime targets?",
  "updated_fields": ["quality_attributes"]
}
```

#### `status` — Check progress of an intent

**Input**: `{"action": "status", "intent_id": "INT-001"}`

**Output**:
```json
{
  "intent_id": "INT-001",
  "project_name": "Restaurant Booking",
  "status": "in_progress",
  "populated": ["context", "intent", "motivation", "quality_attributes"],
  "remaining": ["success_criteria", "assumptions"],
  "open_clarifications": 1,
  "channels_contributed": ["voice", "claude"],
  "turn_count": 18
}
```

## Identity Resolution

The Claude skill resolves user identity from:
1. The active Cognito session (if running in the browser-based Claude interface)
2. Git config email (if running in Claude Code CLI): `git config user.email`
3. Explicit `--user-email` flag passed to the skill

## Error Handling

| Condition | Response |
|-----------|----------|
| No user identity resolvable | `{"error": "Cannot determine user identity. Set git config user.email or pass --user-email."}` |
| intent_id not found | `{"error": "Intent INT-999 not found or already finalised."}` |
| intent_id belongs to different user | `{"error": "This intent belongs to a different user."}` |
| message without active session | `{"error": "No active session. Use 'resume' first."}` |
