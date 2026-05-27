from __future__ import annotations

import time
from typing import Any

from voice_server.observability.logging import get_logger
from voice_server.persistence.client import get_item, put_item
from voice_server.persistence.serializers import (
    elicitation_to_item,
    item_to_elicitation_data,
)

logger = get_logger(__name__)


class ElicitationPersistenceAdapter:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    async def save(
        self,
        intent_id: str,
        populated_fields: list[str],
        outstanding_clarifications: list[str],
        status: str,
    ) -> None:
        item = elicitation_to_item(
            self._session_id, intent_id, populated_fields, outstanding_clarifications, status
        )
        success = await put_item(item)
        if not success:
            await put_item(item)

    async def load(self) -> dict[str, Any] | None:
        key = {"session_id": {"S": self._session_id}, "record_type": {"S": "ELICITATION"}}
        item = await get_item(key, consistent=True)
        if item is None:
            return None
        expires_at = int(item.get("expires_at", {}).get("N", "0"))
        if expires_at < int(time.time()):
            return None
        return item_to_elicitation_data(item)

    async def delete(self) -> None:
        from voice_server.persistence.client import delete_item

        key = {"session_id": {"S": self._session_id}, "record_type": {"S": "ELICITATION"}}
        await delete_item(key)
