from __future__ import annotations

import re

from strands import tool

from voice_server.elicitation.intent_doc import IntentDocument
from voice_server.elicitation.storage import (
    list_intents,
    load_intent,
    next_intent_id,
    save_intent,
)
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)

VALID_SECTIONS = [
    "context",
    "intent",
    "motivation",
    "quality_attributes",
    "success_criteria",
    "assumptions",
    "clarifications",
]


@tool
def create_intent(project_name: str, context: str, intent: str, motivation: str) -> dict:
    """Create a new structured intent document with the mandatory fields populated.

    Args:
        project_name: Human-readable name for the project or idea.
        context: Problem space, constraints, and environment description.
        intent: Single declarative sentence capturing the big idea.
        motivation: Why this is being done now, cost of inaction.

    Returns:
        A dictionary with the intent ID and file path of the created document.
    """
    if not project_name or not intent:
        return {
            "status": "error",
            "content": [{"text": "project_name and intent are required"}],
        }

    intent_id = next_intent_id()
    doc = IntentDocument(
        intent_id=intent_id,
        project_name=project_name,
        context=context,
        intent=intent,
        motivation=motivation,
    )

    try:
        path = save_intent(doc)
    except OSError:
        try:
            path = save_intent(doc)
        except OSError as e:
            logger.error("create_intent_failed", intent_id=intent_id, error=str(e))
            return {
                "status": "error",
                "content": [{"text": f"Failed to save intent document: {e}"}],
            }

    logger.info("intent_created", intent_id=intent_id, project=project_name)

    import asyncio

    from voice_server.persistence.intent_session_adapter import IntentSessionAdapter
    from voice_server.sessions.intent_session import IntentSession

    try:
        loop = asyncio.get_running_loop()
        session = IntentSession(
            intent_id=intent_id,
            user_email=_get_current_user_email(),
            project_name=project_name,
            active_channels={_get_current_channel()},
        )
        session.record_section_update("context", _get_current_channel())
        session.record_section_update("intent", _get_current_channel())
        session.record_section_update("motivation", _get_current_channel())
        loop.create_task(IntentSessionAdapter().save(session))
    except RuntimeError:
        pass

    return {
        "status": "success",
        "content": [{"text": f"Created {intent_id} for '{project_name}'"}],
        "intent_id": intent_id,
        "path": str(path),
    }


@tool
def update_intent_section(intent_id: str, section: str, content: str, append: bool = False) -> dict:
    """Update a single section of an existing intent document.

    Args:
        intent_id: ID of the document to update (e.g., "INT-001").
        section: Section name to update. Valid: context, intent, motivation, quality_attributes, success_criteria, assumptions, clarifications.
        content: New content for the section.
        append: If true, append to existing content instead of replacing. Useful for list sections.

    Returns:
        A dictionary confirming the update.
    """
    if section not in VALID_SECTIONS:
        return {
            "status": "error",
            "content": [
                {"text": f"Invalid section '{section}'. Valid: {', '.join(VALID_SECTIONS)}"}
            ],
        }

    doc = load_intent(intent_id)
    if doc is None:
        available = list_intents()
        return {
            "status": "error",
            "content": [{"text": f"Document {intent_id} not found. Available: {available}"}],
        }

    if section in ("quality_attributes", "success_criteria", "assumptions", "clarifications"):
        _update_list_section(doc, section, content, append)
    else:
        setattr(doc, section, content)

    try:
        save_intent(doc)
    except OSError:
        try:
            save_intent(doc)
        except OSError as e:
            return {"status": "error", "content": [{"text": f"Failed to save: {e}"}]}

    logger.info("intent_section_updated", intent_id=intent_id, section=section)

    import asyncio

    from voice_server.persistence.intent_session_adapter import IntentSessionAdapter

    try:
        loop = asyncio.get_running_loop()

        async def _record_attribution():
            adapter = IntentSessionAdapter()
            session = await adapter.load(intent_id)
            if session:
                session.record_section_update(section, _get_current_channel())
                await adapter.save(session)

        loop.create_task(_record_attribution())
    except RuntimeError:
        pass

    return {
        "status": "success",
        "content": [{"text": f"Updated {section} section of {intent_id}"}],
    }


@tool
def read_intent(intent_id: str) -> dict:
    """Read the current state of an intent document for review or summarisation.

    Args:
        intent_id: ID of the document to read (e.g., "INT-001").

    Returns:
        The full document content and lists of populated vs empty sections.
    """
    doc = load_intent(intent_id)
    if doc is None:
        available = list_intents()
        if not available:
            return {
                "status": "error",
                "content": [{"text": "No intent documents exist yet. Use create_intent to start."}],
            }
        return {
            "status": "error",
            "content": [{"text": f"Document {intent_id} not found. Available: {available}"}],
        }

    return {
        "status": "success",
        "content": [{"text": doc.render()}],
        "populated_sections": doc.populated_sections(),
        "empty_sections": doc.empty_sections(),
    }


@tool
def finalise_intent(intent_id: str) -> dict:
    """Mark an intent document as confirmed after user approval.

    Args:
        intent_id: ID of the document to finalise (e.g., "INT-001").

    Returns:
        Confirmation that the document has been finalised.
    """
    doc = load_intent(intent_id)
    if doc is None:
        return {"status": "error", "content": [{"text": f"Document {intent_id} not found."}]}

    if doc.status == "confirmed":
        return {"status": "success", "content": [{"text": f"{intent_id} is already confirmed."}]}

    missing = []
    if not doc.context or doc.context == "[Not yet captured]":
        missing.append("context")
    if not doc.intent or doc.intent == "[Not yet captured]":
        missing.append("intent")
    if not doc.motivation or doc.motivation == "[Not yet captured]":
        missing.append("motivation")

    if missing:
        return {
            "status": "error",
            "content": [
                {"text": f"Cannot finalise — missing mandatory fields: {', '.join(missing)}"}
            ],
        }

    for empty_section in doc.empty_sections():
        if empty_section not in ("context", "intent", "motivation"):
            clr_id = f"CLR-{len(doc.clarifications) + 1:03d}"
            doc.clarifications.append(f"### {clr_id}")
            doc.clarifications.append(
                f"**Prompt:** What are the {empty_section.replace('_', ' ')} for this project?"
            )
            doc.clarifications.append("**Resolution:** OPEN")
            doc.clarifications.append("")

    doc.status = "confirmed"

    try:
        save_intent(doc)
    except OSError:
        try:
            save_intent(doc)
        except OSError as e:
            return {"status": "error", "content": [{"text": f"Failed to save: {e}"}]}

    logger.info("intent_finalised", intent_id=intent_id)

    import asyncio

    from voice_server.notifications import notify
    from voice_server.notifications.events import IntentFinalised

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            notify(
                IntentFinalised(
                    intent_id=intent_id,
                    project_name=doc.project_name,
                    intent_summary=doc.intent,
                    actor=doc.actor,
                    populated_fields=doc.populated_sections(),
                    open_clarifications=len(doc.clarifications),
                    full_content=doc.render(),
                )
            )
        )
    except RuntimeError:
        pass

    return {
        "status": "success",
        "content": [
            {"text": f"{intent_id} finalised and confirmed. Ready for downstream processing."}
        ],
    }


def _update_list_section(doc: IntentDocument, section: str, content: str, append: bool) -> None:
    current: list[str] = getattr(doc, section)
    if not append:
        setattr(doc, section, [content] if not content.startswith("- ") else [content])
        return

    if section == "quality_attributes":
        next_id = _next_list_id(current, "QA")
        new_item = f"- **{next_id}**: {content}"
    elif section == "success_criteria":
        next_id = _next_list_id(current, "SC")
        new_item = f"- **{next_id}**: {content}"
    elif section == "assumptions":
        next_id = _next_list_id(current, "ASM")
        new_item = f"- **{next_id}** [medium]: {content}"
    elif section == "clarifications":
        next_id = _next_clr_id(current)
        new_item = f"### {next_id}\n**Prompt:** {content}\n**Resolution:** OPEN\n"
    else:
        new_item = f"- {content}"

    current.append(new_item)


def _next_list_id(items: list[str], prefix: str) -> str:
    max_num = 0
    pattern = re.compile(rf"\*\*({prefix}-(\d+))\*\*")
    for item in items:
        m = pattern.search(item)
        if m:
            max_num = max(max_num, int(m.group(2)))
    return f"{prefix}-{max_num + 1:03d}"


def _next_clr_id(items: list[str]) -> str:
    max_num = 0
    pattern = re.compile(r"### CLR-(\d+)")
    for item in items:
        m = pattern.search(item)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"CLR-{max_num + 1:03d}"


import contextvars

_current_channel: contextvars.ContextVar[str] = contextvars.ContextVar(
    "_current_channel", default="voice"
)
_current_user_email: contextvars.ContextVar[str] = contextvars.ContextVar(
    "_current_user_email", default=""
)


def set_elicitation_context(channel: str, user_email: str) -> None:
    _current_channel.set(channel)
    _current_user_email.set(user_email)


def _get_current_channel() -> str:
    return _current_channel.get()


def _get_current_user_email() -> str:
    return _current_user_email.get()
