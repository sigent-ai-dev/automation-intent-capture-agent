from __future__ import annotations

from dataclasses import dataclass

from voice_server.persistence.intent_session_adapter import IntentSessionAdapter
from voice_server.sessions.intent_session import IntentSession


@dataclass
class IntentSummary:
    intent_id: str
    project_name: str
    elicitation_status: str
    populated_fields: list[str]
    last_channel: str
    last_activity: str


async def find_active_intents(user_email: str) -> list[IntentSession]:
    adapter = IntentSessionAdapter()
    return await adapter.query_by_email(user_email)


async def get_intent_summaries(user_email: str) -> list[IntentSummary]:
    sessions = await find_active_intents(user_email)
    summaries = []
    for session in sessions:
        populated = list(session.section_attributions.keys())
        last_channel = ""
        if session.active_channels:
            last_channel = sorted(session.active_channels)[-1]
        summaries.append(
            IntentSummary(
                intent_id=session.intent_id,
                project_name=session.project_name,
                elicitation_status=session.elicitation_status,
                populated_fields=populated,
                last_channel=last_channel,
                last_activity=session.last_activity.isoformat(),
            )
        )
    return summaries
