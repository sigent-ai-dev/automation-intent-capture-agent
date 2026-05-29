from __future__ import annotations

from strands import Agent

from voice_server.elicitation.prompts import build_resume_context, build_system_prompt
from voice_server.elicitation.tools import (
    create_intent,
    finalise_intent,
    read_intent,
    set_elicitation_context,
    update_intent_section,
)
from voice_server.observability.logging import get_logger
from voice_server.persistence.intent_history_adapter import IntentHistory

logger = get_logger(__name__)

_TOOLS = [create_intent, update_intent_section, read_intent, finalise_intent]


async def invoke_text_agent(
    message: str,
    channel: str,
    user_email: str,
    history: IntentHistory | None = None,
    doc=None,
) -> str:
    set_elicitation_context(channel, user_email)

    system_parts = [build_system_prompt()]
    if doc:
        channels = ", ".join(
            set(t.channel for t in history.turns) if history and history.turns else [channel]
        )
        history_context = history.get_context_for_agent() if history else ""
        resume_ctx = build_resume_context(doc, channels=channels, history_context=history_context)
        system_parts.append(resume_ctx)

    system_prompt = "\n\n".join(system_parts)

    messages = []
    if history and history.turns:
        for turn in history.turns[-10:]:
            role = "user" if turn.role == "user" else "assistant"
            messages.append({"role": role, "content": [{"text": turn.text}]})

    agent = Agent(
        system_prompt=system_prompt,
        tools=_TOOLS,
        messages=messages,
    )

    try:
        result = agent(message)
        response_text = str(result)
        if not response_text or response_text == "None":
            response_text = "I've processed your input. What would you like to discuss next?"
        return response_text
    except Exception as e:
        logger.warning("text_agent_invocation_failed", error=str(e), channel=channel)
        return "I encountered an issue processing your message. Your progress is saved — please try again."
