from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from voice_server.config import get_settings
from voice_server.observability.logging import get_logger
from voice_server.persistence.client import get_item, put_item

logger = get_logger(__name__)


@dataclass
class IntentTurn:
    role: str
    text: str
    channel: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class IntentHistory:
    intent_id: str
    turns: list[IntentTurn] = field(default_factory=list)
    summary: str = ""
    turn_count: int = 0

    def add_turn(self, role: str, text: str, channel: str) -> None:
        self.turns.append(IntentTurn(role=role, text=text, channel=channel))
        self.turn_count += 1

    def needs_summarisation(self) -> bool:
        settings = get_settings()
        return len(self.turns) > settings.history_summarise_threshold

    def get_overflow_turns(self) -> list[IntentTurn]:
        settings = get_settings()
        if len(self.turns) <= settings.history_summarise_threshold:
            return []
        return self.turns[: -settings.history_summarise_threshold]

    def apply_summarisation(self, summary_text: str) -> None:
        settings = get_settings()
        overflow = self.get_overflow_turns()
        if not overflow:
            return
        if self.summary:
            self.summary = f"{self.summary}\n\n{summary_text}"
        else:
            self.summary = summary_text
        self.turns = self.turns[-settings.history_summarise_threshold :]

    def get_context_for_agent(self) -> str:
        parts: list[str] = []
        if self.summary:
            parts.append(f"[Summary of earlier conversation across channels]:\n{self.summary}")
        for turn in self.turns:
            parts.append(f"[{turn.channel}] {turn.role}: {turn.text}")
        return "\n".join(parts)


def _history_to_item(history: IntentHistory) -> dict[str, Any]:
    settings = get_settings()
    expires_at = int(time.time()) + settings.session_ttl_seconds
    turns = [
        {
            "M": {
                "role": {"S": t.role},
                "text": {"S": t.text},
                "channel": {"S": t.channel},
                "timestamp": {"S": t.timestamp.isoformat()},
            }
        }
        for t in history.turns
    ]
    return {
        "session_id": {"S": history.intent_id},
        "record_type": {"S": "INTENT_HISTORY"},
        "turns": {"L": turns},
        "summary": {"S": history.summary},
        "turn_count": {"N": str(history.turn_count)},
        "updated_at": {"S": datetime.now(timezone.utc).isoformat()},
        "expires_at": {"N": str(expires_at)},
    }


def _item_to_history(item: dict[str, Any]) -> IntentHistory:
    turns = []
    for t in item.get("turns", {}).get("L", []):
        m = t.get("M", {})
        turns.append(
            IntentTurn(
                role=m["role"]["S"],
                text=m["text"]["S"],
                channel=m.get("channel", {}).get("S", "voice"),
                timestamp=datetime.fromisoformat(m["timestamp"]["S"]),
            )
        )
    return IntentHistory(
        intent_id=item["session_id"]["S"],
        turns=turns,
        summary=item.get("summary", {}).get("S", ""),
        turn_count=int(item.get("turn_count", {}).get("N", str(len(turns)))),
    )


class IntentHistoryAdapter:
    async def save(self, history: IntentHistory) -> bool:
        item = _history_to_item(history)
        return await put_item(item)

    async def load(self, intent_id: str) -> IntentHistory | None:
        key = {"session_id": {"S": intent_id}, "record_type": {"S": "INTENT_HISTORY"}}
        item = await get_item(key, consistent=True)
        if item is None:
            return None
        expires_at = int(item.get("expires_at", {}).get("N", "0"))
        if expires_at < int(time.time()):
            return None
        return _item_to_history(item)
