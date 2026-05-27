from __future__ import annotations

import time
from typing import Any

from voice_server.observability.logging import get_logger
from voice_server.persistence.client import get_item, put_item
from voice_server.persistence.serializers import history_to_item, item_to_history_data

logger = get_logger(__name__)


class HistoryPersistenceAdapter:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    async def save(self, history) -> None:
        item = history_to_item(self._session_id, history)
        success = await put_item(item)
        if not success:
            await put_item(item)

    async def load(self) -> dict[str, Any] | None:
        key = {"session_id": {"S": self._session_id}, "record_type": {"S": "HISTORY"}}
        item = await get_item(key, consistent=True)
        if item is None:
            return None
        data = item_to_history_data(item)
        expires_at = int(item.get("expires_at", {}).get("N", "0"))
        if expires_at < int(time.time()):
            return None
        return data

    async def delete(self) -> None:
        from voice_server.persistence.client import delete_item

        key = {"session_id": {"S": self._session_id}, "record_type": {"S": "HISTORY"}}
        await delete_item(key)
