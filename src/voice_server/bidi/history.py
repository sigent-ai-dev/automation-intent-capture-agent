from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Turn:
    role: str
    text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationHistory:
    def __init__(self, session_id: str, window_size: int = 10) -> None:
        self.session_id = session_id
        self.window_size = window_size
        self.turns: list[Turn] = []
        self.summary: str = ""

    def add_turn(self, role: str, text: str) -> None:
        self.turns.append(Turn(role=role, text=text))
        if len(self.turns) > self.window_size:
            self._summarise_overflow()

    def get_recent(self) -> list[Turn]:
        return self.turns[-self.window_size :]

    def get_summary_and_recent(self) -> str:
        parts: list[str] = []
        if self.summary:
            parts.append(f"[Summary of earlier conversation]: {self.summary}")
        for turn in self.get_recent():
            parts.append(f"{turn.role}: {turn.text}")
        return "\n".join(parts)

    def _summarise_overflow(self) -> None:
        overflow = self.turns[: -self.window_size]
        overflow_text = " ".join(f"{t.role}: {t.text}" for t in overflow)
        if self.summary:
            self.summary = f"{self.summary} {overflow_text}"
        else:
            self.summary = overflow_text
        self.turns = self.turns[-self.window_size :]
