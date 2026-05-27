from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date


@dataclass
class IntentDocument:
    intent_id: str = ""
    project_name: str = ""
    captured_date: date = field(default_factory=date.today)
    actor: str = "voice"
    status: str = "draft"
    context: str = ""
    intent: str = ""
    motivation: str = ""
    quality_attributes: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    clarifications: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"# Intent: {self.project_name}",
            "",
            f"**Intent ID**: {self.intent_id}",
            f"**Captured**: {self.captured_date.isoformat()}",
            f"**Actor**: {self.actor}",
            f"**Status**: {self.status}",
            "",
            "## Context",
            "",
            self.context or "[Not yet captured]",
            "",
            "## Intent",
            "",
            self.intent or "[Not yet captured]",
            "",
            "## Motivation",
            "",
            self.motivation or "[Not yet captured]",
            "",
            "## Quality Attributes",
            "",
        ]
        if self.quality_attributes:
            lines.extend(self.quality_attributes)
        else:
            lines.append("[Not yet captured]")
        lines.extend(["", "## Success Criteria", ""])
        if self.success_criteria:
            lines.extend(self.success_criteria)
        else:
            lines.append("[Not yet captured]")
        lines.extend(["", "## Assumptions", ""])
        if self.assumptions:
            lines.extend(self.assumptions)
        else:
            lines.append("[Not yet captured]")
        lines.extend(["", "## Clarifications", ""])
        if self.clarifications:
            lines.extend(self.clarifications)
        else:
            lines.append("[None]")
        lines.append("")
        return "\n".join(lines)

    @classmethod
    def parse(cls, text: str) -> IntentDocument:
        doc = cls()

        title_match = re.search(r"^# Intent:\s*(.+)$", text, re.MULTILINE)
        if title_match:
            doc.project_name = title_match.group(1).strip()

        for pattern, attr in [
            (r"\*\*Intent ID\*\*:\s*(.+)", "intent_id"),
            (r"\*\*Actor\*\*:\s*(.+)", "actor"),
            (r"\*\*Status\*\*:\s*(.+)", "status"),
        ]:
            m = re.search(pattern, text)
            if m:
                setattr(doc, attr, m.group(1).strip())

        date_match = re.search(r"\*\*Captured\*\*:\s*(\d{4}-\d{2}-\d{2})", text)
        if date_match:
            doc.captured_date = date.fromisoformat(date_match.group(1))

        sections = _split_sections(text)
        doc.context = sections.get("context", "")
        doc.intent = sections.get("intent", "")
        doc.motivation = sections.get("motivation", "")
        doc.quality_attributes = _extract_list(sections.get("quality attributes", ""))
        doc.success_criteria = _extract_list(sections.get("success criteria", ""))
        doc.assumptions = _extract_list(sections.get("assumptions", ""))
        doc.clarifications = _extract_block(sections.get("clarifications", ""))

        return doc

    def populated_sections(self) -> list[str]:
        result = []
        if self.context and self.context != "[Not yet captured]":
            result.append("context")
        if self.intent and self.intent != "[Not yet captured]":
            result.append("intent")
        if self.motivation and self.motivation != "[Not yet captured]":
            result.append("motivation")
        if self.quality_attributes:
            result.append("quality_attributes")
        if self.success_criteria:
            result.append("success_criteria")
        if self.assumptions:
            result.append("assumptions")
        return result

    def empty_sections(self) -> list[str]:
        all_sections = [
            "context", "intent", "motivation",
            "quality_attributes", "success_criteria", "assumptions",
        ]
        return [s for s in all_sections if s not in self.populated_sections()]


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_heading = ""
    current_lines: list[str] = []

    for line in text.split("\n"):
        heading_match = re.match(r"^## (.+)$", line)
        if heading_match:
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = heading_match.group(1).strip().lower()
            current_lines = []
        elif current_heading:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _extract_list(text: str) -> list[str]:
    if not text or text == "[Not yet captured]":
        return []
    return [line for line in text.split("\n") if line.startswith("- ")]


def _extract_block(text: str) -> list[str]:
    if not text or text in ("[None]", "[Not yet captured]"):
        return []
    lines = [line for line in text.split("\n") if line.strip()]
    return lines
