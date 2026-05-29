# Contract: Slack Events Integration

## Purpose

Define how the Slack bot receives and responds to messages for intent elicitation.

## Slack App Configuration

**Required OAuth Scopes**:
- `app_mentions:read` — detect when bot is @mentioned
- `chat:write` — send messages in channels/threads
- `users:read.email` — resolve Slack user ID → email for identity mapping
- `im:history` — read DM messages
- `im:write` — send DM messages

**Event Subscriptions** (Events API):
- `app_mention` — bot mentioned in a channel
- `message.im` — direct message to bot

**Request URL**: `https://{host}/slack/events`

## Inbound Event: app_mention / message.im

Slack sends:

```json
{
  "type": "event_callback",
  "event": {
    "type": "app_mention",
    "user": "U1234ABCD",
    "text": "<@UBOTID> I want to continue my intent capture",
    "channel": "C9876XYZ",
    "ts": "1717012345.123456",
    "thread_ts": "1717012300.000000"
  }
}
```

## Bot Response Strategy

1. **Acknowledge** within 3 seconds (empty 200 response to Slack)
2. **Resolve identity**: Call `users.info` → extract `user.profile.email`
3. **Lookup active intents**: Query `GET /intents/active?user_email=...`
4. **Route**:
   - No active intents → "No active intent captures found. Want to start a new one?"
   - One active intent → Resume automatically, reply with progress summary
   - Multiple active intents → List them, ask user to pick one
5. **Respond in thread**: All elicitation happens in a Slack thread (not top-level channel messages)

## Response Format

Bot messages use Slack Block Kit:

```json
{
  "channel": "C9876XYZ",
  "thread_ts": "1717012300.000000",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Resuming *Restaurant Booking System* (INT-001).\n\nYou've captured: context, intent, motivation.\nRemaining: quality attributes, success criteria, assumptions.\n\nLet's continue — what quality attributes matter most for this system?"
      }
    }
  ]
}
```

## Thread Model

- Each intent capture session maps to one Slack thread
- Thread `ts` is stored in the INTENT_SESSION record as channel-specific metadata
- If the user @mentions the bot outside a thread, a new thread is started
- All subsequent messages within the thread are treated as elicitation turns

## Error Responses

| Condition | Bot Response |
|-----------|-------------|
| Email not resolvable | "I couldn't find your email in Slack. Please ensure your profile email is visible." |
| Intent not found | "That intent doesn't exist or has already been finalised." |
| Rate limited by Slack | Retry with exponential backoff (handled by slack-bolt) |
| Elicitation engine error | "Something went wrong on my end. Your progress is saved — try again in a moment." |
