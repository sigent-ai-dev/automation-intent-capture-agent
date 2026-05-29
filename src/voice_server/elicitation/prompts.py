ELICITATION_SYSTEM_PROMPT = """\
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
"""

RESUME_PROMPT_TEMPLATE = """\
A previous session captured intent but it's still in draft. Here's what exists:

Intent ID: {intent_id}
Project: {project_name}
Populated sections: {populated}
Missing sections: {missing}
Channels that contributed: {channels}

Continue the conversation by acknowledging existing progress and guiding toward remaining gaps. \
Don't re-ask questions that have already been answered. Reference specific details from the \
conversation history below if available.
{history_context}
"""


def build_system_prompt(base_prompt: str | None = None, resume_context: str | None = None) -> str:
    parts = []
    if base_prompt:
        parts.append(base_prompt)
    parts.append(ELICITATION_SYSTEM_PROMPT)
    if resume_context:
        parts.append(resume_context)
    return "\n\n".join(parts)


def build_resume_context(doc, channels: str = "voice", history_context: str = "") -> str:
    return RESUME_PROMPT_TEMPLATE.format(
        intent_id=doc.intent_id,
        project_name=doc.project_name,
        populated=", ".join(doc.populated_sections()) or "none",
        missing=", ".join(doc.empty_sections()) or "none",
        channels=channels,
        history_context=history_context,
    )
