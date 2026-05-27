from datetime import datetime, timezone
from unittest.mock import MagicMock

from voice_server.persistence.serializers import (
    elicitation_to_item,
    history_to_item,
    item_to_elicitation_data,
    item_to_history_data,
    item_to_session_data,
    session_to_item,
)


def _make_mock_session():
    session = MagicMock()
    session.id = "sess-001"
    session.user_id = "user-123"
    session.state.value = "streaming"
    session.connected_at = datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc)
    session.last_activity = datetime(2026, 5, 27, 10, 5, 0, tzinfo=timezone.utc)
    session.codec.format = "pcm"
    session.codec.sample_rate = 16000
    session.codec.bit_depth = 16
    session.codec.channels = 1
    return session


def test_session_roundtrip():
    session = _make_mock_session()
    item = session_to_item(session)
    assert item["session_id"]["S"] == "sess-001"
    assert item["record_type"]["S"] == "SESSION"
    assert item["status"]["S"] == "active"
    assert "expires_at" in item

    data = item_to_session_data(item)
    assert data["id"] == "sess-001"
    assert data["user_id"] == "user-123"
    assert data["state"] == "streaming"


def test_session_closed_status():
    session = _make_mock_session()
    session.state.value = "closed"
    item = session_to_item(session)
    assert item["status"]["S"] == "closed"


def test_history_roundtrip():
    history = MagicMock()
    history.summary = "User wants a booking system"
    history.window_size = 10
    turn = MagicMock()
    turn.role = "user"
    turn.text = "I need a restaurant app"
    turn.timestamp = datetime(2026, 5, 27, 10, 1, 0, tzinfo=timezone.utc)
    history.turns = [turn]

    item = history_to_item("sess-001", history)
    assert item["session_id"]["S"] == "sess-001"
    assert item["record_type"]["S"] == "HISTORY"
    assert item["summary"]["S"] == "User wants a booking system"
    assert len(item["turns"]["L"]) == 1

    data = item_to_history_data(item)
    assert data["session_id"] == "sess-001"
    assert data["summary"] == "User wants a booking system"
    assert len(data["turns"]) == 1
    assert data["turns"][0]["role"] == "user"


def test_elicitation_roundtrip():
    item = elicitation_to_item(
        session_id="sess-001",
        intent_id="INT-001",
        populated=["context", "intent"],
        outstanding=["CLR-001"],
        status="in_progress",
    )
    assert item["session_id"]["S"] == "sess-001"
    assert item["record_type"]["S"] == "ELICITATION"
    assert item["intent_id"]["S"] == "INT-001"

    data = item_to_elicitation_data(item)
    assert data["intent_id"] == "INT-001"
    assert data["populated_fields"] == ["context", "intent"]
    assert data["outstanding_clarifications"] == ["CLR-001"]
    assert data["elicitation_status"] == "in_progress"


def test_history_empty_turns():
    history = MagicMock()
    history.summary = ""
    history.window_size = 10
    history.turns = []

    item = history_to_item("sess-001", history)
    data = item_to_history_data(item)
    assert data["turns"] == []
    assert data["summary"] == ""
