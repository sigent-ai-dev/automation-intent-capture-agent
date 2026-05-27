from __future__ import annotations

import asyncio
from typing import Any, Protocol

from voice_server.observability.logging import get_logger

logger = get_logger(__name__)

NotificationEvent = Any

_adapters: list[NotificationAdapter] = []


class NotificationAdapter(Protocol):
    async def send(self, event: NotificationEvent) -> None: ...


def register_adapter(adapter: NotificationAdapter) -> None:
    _adapters.append(adapter)


async def notify(event: NotificationEvent) -> None:
    for adapter in _adapters:
        asyncio.create_task(_safe_send(adapter, event))


async def _safe_send(adapter: NotificationAdapter, event: NotificationEvent) -> None:
    try:
        await adapter.send(event)
    except Exception as e:
        logger.warning("notification_delivery_failed", error=str(e))
