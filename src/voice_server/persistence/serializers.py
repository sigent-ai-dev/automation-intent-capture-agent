from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from voice_server.config import get_settings


def session_to_item(session) -> dict[str, Any]:
    settings = get_settings()
    expires_at = int(time.time()) + settings.session_ttl_seconds
    return {
        "session_id": {"S": session.id},
        "record_type": {"S": "SESSION"},
        "user_id": {"S": session.user_id},
        "state": {"S": session.state.value},
        "connected_at": {"S": session.connected_at.isoformat()},
        "last_activity": {"N": str(int(session.last_activity.timestamp()))},
        "status": {"S": "active" if session.state.value != "closed" else "closed"},
        "codec": {
            "M": {
                "format": {"S": session.codec.format},
                "sample_rate": {"N": str(session.codec.sample_rate)},
                "bit_depth": {"N": str(session.codec.bit_depth)},
                "channels": {"N": str(session.codec.channels)},
            }
        },
        "expires_at": {"N": str(expires_at)},
    }


def item_to_session_data(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["session_id"]["S"],
        "user_id": item["user_id"]["S"],
        "state": item["state"]["S"],
        "connected_at": item["connected_at"]["S"],
        "last_activity": int(item["last_activity"]["N"]),
        "expires_at": int(item["expires_at"]["N"]),
    }


def history_to_item(session_id: str, history) -> dict[str, Any]:
    settings = get_settings()
    expires_at = int(time.time()) + settings.session_ttl_seconds
    turns = [
        {
            "M": {
                "role": {"S": t.role},
                "text": {"S": t.text},
                "timestamp": {"S": t.timestamp.isoformat()},
            }
        }
        for t in history.turns
    ]
    return {
        "session_id": {"S": session_id},
        "record_type": {"S": "HISTORY"},
        "summary": {"S": history.summary},
        "turns": {"L": turns},
        "window_size": {"N": str(history.window_size)},
        "updated_at": {"S": datetime.now(timezone.utc).isoformat()},
        "expires_at": {"N": str(expires_at)},
    }


def item_to_history_data(item: dict[str, Any]) -> dict[str, Any]:
    turns = []
    for t in item.get("turns", {}).get("L", []):
        m = t.get("M", {})
        turns.append(
            {
                "role": m["role"]["S"],
                "text": m["text"]["S"],
                "timestamp": m["timestamp"]["S"],
            }
        )
    return {
        "session_id": item["session_id"]["S"],
        "summary": item.get("summary", {}).get("S", ""),
        "turns": turns,
        "window_size": int(item.get("window_size", {}).get("N", "10")),
    }


def elicitation_to_item(session_id: str, intent_id: str, populated: list[str], outstanding: list[str], status: str) -> dict[str, Any]:
    settings = get_settings()
    expires_at = int(time.time()) + settings.session_ttl_seconds
    return {
        "session_id": {"S": session_id},
        "record_type": {"S": "ELICITATION"},
        "intent_id": {"S": intent_id},
        "populated_fields": {"L": [{"S": f} for f in populated]},
        "outstanding_clarifications": {"L": [{"S": c} for c in outstanding]},
        "elicitation_status": {"S": status},
        "updated_at": {"S": datetime.now(timezone.utc).isoformat()},
        "expires_at": {"N": str(expires_at)},
    }


def item_to_elicitation_data(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": item["session_id"]["S"],
        "intent_id": item.get("intent_id", {}).get("S", ""),
        "populated_fields": [f["S"] for f in item.get("populated_fields", {}).get("L", [])],
        "outstanding_clarifications": [c["S"] for c in item.get("outstanding_clarifications", {}).get("L", [])],
        "elicitation_status": item.get("elicitation_status", {}).get("S", "in_progress"),
    }
