from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from voice_server.channels.text_agent import invoke_text_agent
from voice_server.elicitation.intent_doc import IntentDocument
from voice_server.elicitation.storage import load_intent
from voice_server.observability.logging import get_logger
from voice_server.persistence.intent_history_adapter import IntentHistoryAdapter
from voice_server.persistence.intent_session_adapter import IntentSessionAdapter
from voice_server.sessions.user_lookup import get_intent_summaries

logger = get_logger(__name__)
router = APIRouter(prefix="/intents", tags=["intents"])


class ResumeRequest(BaseModel):
    channel: str
    user_email: str
    message: str = ""


class MessageRequest(BaseModel):
    channel: str
    user_email: str
    message: str


@router.get("/active")
async def get_active_intents(user_email: str):
    if not user_email:
        raise HTTPException(status_code=400, detail="user_email parameter required")
    summaries = await get_intent_summaries(user_email)
    return {"intents": [s.__dict__ for s in summaries]}


@router.post("/{intent_id}/resume")
async def resume_intent(intent_id: str, request: ResumeRequest):
    session_adapter = IntentSessionAdapter()
    session = await session_adapter.load(intent_id)

    if session is None:
        raise HTTPException(
            status_code=404, detail=f"Intent {intent_id} not found or not in progress"
        )

    if session.user_email != request.user_email:
        raise HTTPException(status_code=403, detail="Intent does not belong to this user")

    if not session.is_active():
        raise HTTPException(
            status_code=404, detail=f"Intent {intent_id} not found or not in progress"
        )

    session.touch(request.channel)
    await session_adapter.save(session)

    doc = load_intent(intent_id)
    if doc is None:
        raise HTTPException(
            status_code=404, detail=f"Intent document {intent_id} not found on filesystem"
        )

    history_adapter = IntentHistoryAdapter()
    history = await history_adapter.load(intent_id)
    history_context = history.get_context_for_agent() if history else ""

    progress = {
        "populated": doc.populated_sections(),
        "remaining": doc.empty_sections(),
    }

    agent_response = _build_resume_response(doc, progress, request.channel, history_context)

    return {
        "intent_id": intent_id,
        "agent_response": agent_response,
        "progress": progress,
    }


@router.post("/{intent_id}/message")
async def send_message(intent_id: str, request: MessageRequest):
    session_adapter = IntentSessionAdapter()
    session = await session_adapter.load(intent_id)

    if session is None or not session.is_active():
        raise HTTPException(
            status_code=404, detail=f"Intent {intent_id} not found or not in progress"
        )

    if session.user_email != request.user_email:
        raise HTTPException(status_code=403, detail="Intent does not belong to this user")

    session.touch(request.channel)
    await session_adapter.save(session)

    history_adapter = IntentHistoryAdapter()
    history = await history_adapter.load(intent_id)
    if history is None:
        from voice_server.persistence.intent_history_adapter import IntentHistory

        history = IntentHistory(intent_id=intent_id)

    history.add_turn("user", request.message, request.channel)
    await history_adapter.save(history)

    doc = load_intent(intent_id)
    agent_response = await invoke_text_agent(
        message=request.message,
        channel=request.channel,
        user_email=request.user_email,
        history=history,
        doc=doc,
    )

    history.add_turn("agent", agent_response, request.channel)
    await history_adapter.save(history)

    return {
        "agent_response": agent_response,
        "updated_fields": [],
    }


def _build_resume_response(
    doc: IntentDocument,
    progress: dict,
    channel: str,
    history_context: str,
) -> str:
    populated = ", ".join(progress["populated"]) or "none"
    remaining = ", ".join(progress["remaining"]) or "none"

    response = (
        f"Resuming '{doc.project_name}' ({doc.intent_id}) via {channel}. "
        f"Populated: {populated}. Remaining: {remaining}. "
    )

    if progress["remaining"]:
        next_section = progress["remaining"][0]
        response += f"Let's work on {next_section} next."

    return response
