from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ChannelContribution:
    channel: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class IntentSession:
    intent_id: str
    user_email: str
    project_name: str = ""
    elicitation_status: str = "in_progress"
    active_channels: set[str] = field(default_factory=set)
    section_attributions: dict[str, ChannelContribution] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

    def touch(self, channel: str | None = None) -> None:
        self.last_activity = datetime.now(timezone.utc)
        if channel:
            self.active_channels.add(channel)

    def record_section_update(self, section: str, channel: str) -> None:
        self.section_attributions[section] = ChannelContribution(channel=channel)
        self.touch(channel)

    def is_active(self) -> bool:
        return self.elicitation_status == "in_progress"
