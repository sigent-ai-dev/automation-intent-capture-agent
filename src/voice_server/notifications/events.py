from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class IntentFinalised:
    intent_id: str
    project_name: str
    intent_summary: str
    actor: str
    populated_fields: list[str] = field(default_factory=list)
    open_clarifications: int = 0
    full_content: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ErrorOccurred:
    error_type: str
    session_id: str
    description: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
