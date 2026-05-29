# Contract: Intent Lookup API

## Purpose

Internal API for channel adapters to discover a user's active intent captures.

## Endpoint: GET /intents/active

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_email | string | yes | Canonical email address of the user |

**Response 200** (active intents found):

```json
{
  "intents": [
    {
      "intent_id": "INT-001",
      "project_name": "Restaurant Booking System",
      "elicitation_status": "in_progress",
      "populated_fields": ["context", "intent", "motivation"],
      "empty_fields": ["quality_attributes", "success_criteria", "assumptions"],
      "open_clarifications": 2,
      "last_activity": "2026-05-29T14:30:00Z",
      "last_channel": "voice"
    }
  ]
}
```

**Response 200** (no active intents):

```json
{
  "intents": []
}
```

**Response 400** (missing parameter):

```json
{
  "error": "user_email parameter required"
}
```

## Endpoint: POST /intents/{intent_id}/resume

**Purpose**: Resume an existing intent capture from a new channel.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| intent_id | string | The intent to resume (e.g., "INT-001") |

**Request Body**:

```json
{
  "channel": "slack",
  "user_email": "alice@example.com",
  "message": "I'd like to continue where we left off"
}
```

**Response 200** (resumed):

```json
{
  "intent_id": "INT-001",
  "agent_response": "Welcome back! I see you started capturing intent for 'Restaurant Booking System' via voice. You've covered context, intent, and motivation. Let's work on the remaining sections — shall we start with quality attributes?",
  "progress": {
    "populated": ["context", "intent", "motivation"],
    "remaining": ["quality_attributes", "success_criteria", "assumptions"]
  }
}
```

**Response 404** (intent not found):

```json
{
  "error": "Intent INT-999 not found or not in progress"
}
```

**Response 403** (wrong user):

```json
{
  "error": "Intent does not belong to this user"
}
```

## Endpoint: POST /intents/{intent_id}/message

**Purpose**: Send a message within an active cross-channel elicitation session.

**Request Body**:

```json
{
  "channel": "slack",
  "user_email": "alice@example.com",
  "message": "The main quality attribute is low latency for search results"
}
```

**Response 200**:

```json
{
  "agent_response": "Got it — I've noted low-latency search as a key quality attribute. So what I'm hearing is the system should return results in under a second. Does that sound right?",
  "updated_fields": ["quality_attributes"]
}
```
