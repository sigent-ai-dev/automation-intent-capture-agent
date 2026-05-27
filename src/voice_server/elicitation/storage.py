from __future__ import annotations

import os
import re
from pathlib import Path

from voice_server.config import get_settings
from voice_server.elicitation.intent_doc import IntentDocument


def _intent_dir() -> Path:
    settings = get_settings()
    return Path(settings.intent_dir)


def ensure_intent_dir() -> Path:
    path = _intent_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def next_intent_id() -> str:
    path = _intent_dir()
    if not path.exists():
        return "INT-001"
    existing = [f.name for f in path.glob("INT-*.md") if f.is_file()]
    if not existing:
        return "INT-001"
    numbers = []
    for name in existing:
        m = re.match(r"INT-(\d+)\.md", name)
        if m:
            numbers.append(int(m.group(1)))
    next_num = max(numbers) + 1 if numbers else 1
    return f"INT-{next_num:03d}"


def save_intent(doc: IntentDocument) -> Path:
    dir_path = ensure_intent_dir()
    filename = f"{doc.intent_id}.md"
    final_path = dir_path / filename
    tmp_path = dir_path / f".{filename}.tmp"
    tmp_path.write_text(doc.render(), encoding="utf-8")
    os.replace(str(tmp_path), str(final_path))
    return final_path


def load_intent(intent_id: str) -> IntentDocument | None:
    path = _intent_dir() / f"{intent_id}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    return IntentDocument.parse(text)


def list_intents() -> list[str]:
    path = _intent_dir()
    if not path.exists():
        return []
    return sorted(
        re.match(r"(INT-\d+)\.md", f.name).group(1)
        for f in path.glob("INT-*.md")
        if f.is_file() and re.match(r"INT-\d+\.md", f.name)
    )


def find_draft_intents() -> list[str]:
    ids = list_intents()
    drafts = []
    for intent_id in ids:
        doc = load_intent(intent_id)
        if doc and doc.status == "draft":
            drafts.append(intent_id)
    return drafts
