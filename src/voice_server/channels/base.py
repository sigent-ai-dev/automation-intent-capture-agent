from __future__ import annotations

from typing import Any, Protocol

_channels: list[ChannelAdapter] = []


class ChannelAdapter(Protocol):
    @property
    def name(self) -> str: ...

    async def resolve_identity(self, context: dict[str, Any]) -> str | None:
        """Resolve channel-specific context to a canonical email address."""
        ...

    async def handle_message(self, user_email: str, intent_id: str, message: str) -> dict[str, Any]:
        """Process an inbound message and return the agent response."""
        ...


def register_channel(adapter: ChannelAdapter) -> None:
    _channels.append(adapter)


def get_channels() -> list[ChannelAdapter]:
    return list(_channels)
