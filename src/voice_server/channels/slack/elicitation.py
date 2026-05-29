from __future__ import annotations

from voice_server.channels.slack.identity import resolve_email_from_slack
from voice_server.observability.logging import get_logger
from voice_server.persistence.intent_history_adapter import IntentHistory, IntentHistoryAdapter
from voice_server.persistence.intent_session_adapter import IntentSessionAdapter
from voice_server.sessions.user_lookup import find_active_intents

logger = get_logger(__name__)


async def handle_slack_message(client, event: dict, say) -> None:
    user_id = event.get("user", "")
    text = event.get("text", "").strip()
    thread_ts = event.get("thread_ts") or event.get("ts")

    text = _strip_bot_mention(text)

    email = await resolve_email_from_slack(client, user_id)
    if not email:
        await say(
            text="I couldn't find your email in Slack. Please ensure your profile email is visible.",
            thread_ts=thread_ts,
        )
        return

    intents = await find_active_intents(email)

    if not intents:
        await say(
            text="No active intent captures found. Want to start a new one? Just describe your project.",
            thread_ts=thread_ts,
        )
        return

    if len(intents) == 1:
        session = intents[0]
    else:
        options = "\n".join(
            f"• `{s.intent_id}` — {s.project_name}" for s in intents
        )
        await say(
            text=f"You have multiple active intents:\n{options}\n\nWhich one would you like to continue? Reply with the ID.",
            thread_ts=thread_ts,
        )
        return

    session.touch("slack")
    session_adapter = IntentSessionAdapter()
    await session_adapter.save(session)

    history_adapter = IntentHistoryAdapter()
    history = await history_adapter.load(session.intent_id)
    if history is None:
        history = IntentHistory(intent_id=session.intent_id)

    history.add_turn("user", text, "slack")
    await history_adapter.save(history)

    populated = ", ".join(session.section_attributions.keys()) or "none yet"
    response = (
        f"Resuming *{session.project_name}* ({session.intent_id}).\n\n"
        f"Populated: {populated}.\n"
        f"What would you like to add or discuss?"
    )

    history.add_turn("agent", response, "slack")
    await history_adapter.save(history)

    await say(text=response, thread_ts=thread_ts)


def _strip_bot_mention(text: str) -> str:
    import re

    return re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()
