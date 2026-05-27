from __future__ import annotations

import time
from typing import Any

from voice_server.config import get_settings
from voice_server.observability.logging import get_logger
from voice_server.persistence.client import (
    batch_write_sync,
    delete_item,
    get_item,
    put_item,
    query_gsi,
)
from voice_server.persistence.serializers import item_to_session_data, session_to_item

logger = get_logger(__name__)


class SessionPersistenceAdapter:
    def __init__(self) -> None:
        self._available = True

    async def save(self, session) -> None:
        if not self._available:
            return
        item = session_to_item(session)
        success = await put_item(item)
        if not success:
            success = await put_item(item)
        if not success:
            logger.warning("session_persist_failed", session_id=session.id)
            self._available = False

    async def load(self, session_id: str) -> dict[str, Any] | None:
        key = {"session_id": {"S": session_id}, "record_type": {"S": "SESSION"}}
        item = await get_item(key, consistent=True)
        if item is None:
            return None
        data = item_to_session_data(item)
        if data["expires_at"] < int(time.time()):
            return None
        return data

    async def delete(self, session_id: str) -> None:
        key = {"session_id": {"S": session_id}, "record_type": {"S": "SESSION"}}
        await delete_item(key)

    async def list_active_sessions(self) -> list[dict[str, Any]]:
        items = await query_gsi("status-index", "active")
        now = int(time.time())
        return [
            item_to_session_data(item)
            for item in items
            if int(item.get("expires_at", {}).get("N", "0")) > now
        ]

    def drain_all(self, sessions) -> list[str]:
        """Synchronous drain for shutdown. Returns list of session IDs that failed."""
        settings = get_settings()
        items = [session_to_item(s) for s in sessions]
        deadline = time.time() + settings.shutdown_drain_seconds
        failed_ids: list[str] = []

        while items and time.time() < deadline:
            unprocessed = batch_write_sync(items)
            if not unprocessed:
                return []
            items = unprocessed
            if time.time() < deadline:
                time.sleep(1)

        for item in items:
            failed_ids.append(item["session_id"]["S"])
            logger.error("drain_session_failed", session_id=item["session_id"]["S"])

        return failed_ids

    async def refresh_ttl(self, session_id: str) -> None:
        settings = get_settings()
        expires_at = int(time.time()) + settings.session_ttl_seconds
        key = {"session_id": {"S": session_id}, "record_type": {"S": "SESSION"}}
        try:
            from voice_server.persistence.client import get_dynamo_client

            async with await get_dynamo_client() as client:
                await client.update_item(
                    TableName=settings.dynamo_table_name,
                    Key=key,
                    UpdateExpression="SET expires_at = :ttl, last_activity = :la",
                    ExpressionAttributeValues={
                        ":ttl": {"N": str(expires_at)},
                        ":la": {"N": str(int(time.time()))},
                    },
                )
        except Exception as e:
            logger.warning("ttl_refresh_failed", session_id=session_id, error=str(e))
