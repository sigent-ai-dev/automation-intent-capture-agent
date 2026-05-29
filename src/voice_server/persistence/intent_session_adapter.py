from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from voice_server.config import get_settings
from voice_server.observability.logging import get_logger
from voice_server.persistence.client import get_item, put_item, query_gsi_by_email
from voice_server.sessions.intent_session import ChannelContribution, IntentSession

logger = get_logger(__name__)


def _session_to_item(session: IntentSession) -> dict[str, Any]:
    settings = get_settings()
    expires_at = int(time.time()) + settings.session_ttl_seconds

    attributions: dict[str, Any] = {}
    for section, contrib in session.section_attributions.items():
        attributions[section] = {
            "M": {
                "channel": {"S": contrib.channel},
                "timestamp": {"S": contrib.timestamp.isoformat()},
            }
        }

    return {
        "session_id": {"S": session.intent_id},
        "record_type": {"S": "INTENT_SESSION"},
        "user_email": {"S": session.user_email},
        "project_name": {"S": session.project_name},
        "elicitation_status": {"S": session.elicitation_status},
        "active_channels": {"SS": list(session.active_channels) or ["voice"]},
        "section_attributions": {"M": attributions},
        "last_activity": {"N": str(int(session.last_activity.timestamp()))},
        "created_at": {"S": session.created_at.isoformat()},
        "version": {"N": str(session.version)},
        "expires_at": {"N": str(expires_at)},
    }


def _item_to_session(item: dict[str, Any]) -> IntentSession:
    attributions: dict[str, ChannelContribution] = {}
    for section, val in item.get("section_attributions", {}).get("M", {}).items():
        m = val.get("M", {})
        attributions[section] = ChannelContribution(
            channel=m["channel"]["S"],
            timestamp=datetime.fromisoformat(m["timestamp"]["S"]),
        )

    channels_raw = item.get("active_channels", {}).get("SS", [])

    return IntentSession(
        intent_id=item["session_id"]["S"],
        user_email=item["user_email"]["S"],
        project_name=item.get("project_name", {}).get("S", ""),
        elicitation_status=item.get("elicitation_status", {}).get("S", "in_progress"),
        active_channels=set(channels_raw),
        section_attributions=attributions,
        last_activity=datetime.fromtimestamp(
            int(item.get("last_activity", {}).get("N", "0")), tz=timezone.utc
        ),
        created_at=datetime.fromisoformat(
            item.get("created_at", {}).get("S", datetime.now(timezone.utc).isoformat())
        ),
        version=int(item.get("version", {}).get("N", "1")),
    )


class IntentSessionAdapter:
    async def save(self, session: IntentSession) -> bool:
        item = _session_to_item(session)
        return await put_item(item)

    async def load(self, intent_id: str) -> IntentSession | None:
        key = {"session_id": {"S": intent_id}, "record_type": {"S": "INTENT_SESSION"}}
        item = await get_item(key, consistent=True)
        if item is None:
            return None
        expires_at = int(item.get("expires_at", {}).get("N", "0"))
        if expires_at < int(time.time()):
            return None
        return _item_to_session(item)

    async def query_by_email(self, user_email: str) -> list[IntentSession]:
        items = await query_gsi_by_email(user_email)
        sessions = []
        now = int(time.time())
        for item in items:
            if item.get("record_type", {}).get("S") != "INTENT_SESSION":
                continue
            expires_at = int(item.get("expires_at", {}).get("N", "0"))
            if expires_at < now:
                continue
            session = _item_to_session(item)
            if session.is_active():
                sessions.append(session)
        sessions.sort(key=lambda s: s.last_activity, reverse=True)
        return sessions
