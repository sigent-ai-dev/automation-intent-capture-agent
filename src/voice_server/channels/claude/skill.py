from __future__ import annotations

import subprocess
from typing import Any

from voice_server.elicitation.storage import load_intent
from voice_server.observability.logging import get_logger
from voice_server.persistence.intent_history_adapter import IntentHistory, IntentHistoryAdapter
from voice_server.persistence.intent_session_adapter import IntentSessionAdapter
from voice_server.sessions.user_lookup import find_active_intents, get_intent_summaries

logger = get_logger(__name__)


async def intent_capture(
    action: str,
    intent_id: str = "",
    message: str = "",
    project_name: str = "",
    user_email: str = "",
) -> dict[str, Any]:
    email = user_email or _resolve_claude_identity()
    if not email:
        return {
            "error": "Cannot determine user identity. Set git config user.email or pass --user-email."
        }

    if action == "list":
        return await _handle_list(email)
    elif action == "start":
        return await _handle_start(email, project_name)
    elif action == "resume":
        return await _handle_resume(email, intent_id)
    elif action == "message":
        return await _handle_message(email, intent_id, message)
    elif action == "status":
        return await _handle_status(email, intent_id)
    else:
        return {"error": f"Unknown action: {action}. Valid: list, start, resume, message, status"}


async def _handle_list(email: str) -> dict[str, Any]:
    summaries = await get_intent_summaries(email)
    return {
        "intents": [
            {
                "intent_id": s.intent_id,
                "project_name": s.project_name,
                "progress": f"{len(s.populated_fields)}/6 sections",
                "last_activity": s.last_activity,
                "last_channel": s.last_channel,
            }
            for s in summaries
        ]
    }


async def _handle_start(email: str, project_name: str) -> dict[str, Any]:
    if not project_name:
        return {"error": "project_name is required for start action"}

    intents = await find_active_intents(email)
    warning = ""
    if intents:
        warning = f"Note: you have {len(intents)} active draft(s). "

    return {
        "intent_id": "(will be assigned on first tool call)",
        "agent_response": f"{warning}Let's capture intent for '{project_name}'. "
        "Tell me about the context — what problem are you trying to solve and who are the stakeholders?",
    }


async def _handle_resume(email: str, intent_id: str) -> dict[str, Any]:
    if not intent_id:
        return {"error": "intent_id is required for resume action"}

    adapter = IntentSessionAdapter()
    session = await adapter.load(intent_id)

    if session is None or not session.is_active():
        return {"error": f"Intent {intent_id} not found or already finalised."}

    if session.user_email != email:
        return {"error": "This intent belongs to a different user."}

    session.touch("claude")
    await adapter.save(session)

    doc = load_intent(intent_id)
    if doc is None:
        return {"error": f"Intent document {intent_id} not found on filesystem."}

    populated = doc.populated_sections()
    remaining = doc.empty_sections()

    history_adapter = IntentHistoryAdapter()
    history = await history_adapter.load(intent_id)
    history_hint = ""
    if history and history.turns:
        last_turn = history.turns[-1]
        history_hint = f" Last discussed: '{last_turn.text[:80]}' via {last_turn.channel}."

    return {
        "intent_id": intent_id,
        "agent_response": (
            f"Picking up where you left off on '{doc.project_name}'. "
            f"Populated: {', '.join(populated) or 'none'}. "
            f"Remaining: {', '.join(remaining) or 'none'}.{history_hint}"
        ),
        "progress": {"populated": populated, "remaining": remaining},
    }


async def _handle_message(email: str, intent_id: str, message: str) -> dict[str, Any]:
    if not intent_id:
        return {"error": "intent_id is required for message action"}
    if not message:
        return {"error": "message is required for message action"}

    adapter = IntentSessionAdapter()
    session = await adapter.load(intent_id)

    if session is None or not session.is_active():
        return {"error": f"No active session for {intent_id}. Use 'resume' first."}

    if session.user_email != email:
        return {"error": "This intent belongs to a different user."}

    session.touch("claude")
    await adapter.save(session)

    history_adapter = IntentHistoryAdapter()
    history = await history_adapter.load(intent_id)
    if history is None:
        history = IntentHistory(intent_id=intent_id)

    history.add_turn("user", message, "claude")
    await history_adapter.save(history)

    from voice_server.channels.text_agent import invoke_text_agent

    doc = load_intent(intent_id)
    agent_response = await invoke_text_agent(
        message=message,
        channel="claude",
        user_email=email,
        history=history,
        doc=doc,
    )

    history.add_turn("agent", agent_response, "claude")
    await history_adapter.save(history)

    return {"agent_response": agent_response, "updated_fields": []}


async def _handle_status(email: str, intent_id: str) -> dict[str, Any]:
    if not intent_id:
        return {"error": "intent_id is required for status action"}

    adapter = IntentSessionAdapter()
    session = await adapter.load(intent_id)

    if session is None:
        return {"error": f"Intent {intent_id} not found."}

    if session.user_email != email:
        return {"error": "This intent belongs to a different user."}

    doc = load_intent(intent_id)
    populated = doc.populated_sections() if doc else []
    remaining = doc.empty_sections() if doc else []

    history_adapter = IntentHistoryAdapter()
    history = await history_adapter.load(intent_id)

    return {
        "intent_id": intent_id,
        "project_name": session.project_name,
        "status": session.elicitation_status,
        "populated": populated,
        "remaining": remaining,
        "open_clarifications": len(doc.clarifications) if doc else 0,
        "channels_contributed": sorted(session.active_channels),
        "turn_count": history.turn_count if history else 0,
    }


def _resolve_claude_identity() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return ""
