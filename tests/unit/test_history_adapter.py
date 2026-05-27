import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_server.persistence.history_adapter import HistoryPersistenceAdapter


@pytest.fixture
def adapter():
    return HistoryPersistenceAdapter(session_id="sess-001")


@pytest.fixture
def mock_history():
    from datetime import datetime, timezone

    history = MagicMock()
    history.session_id = "sess-001"
    history.summary = "User wants a booking system"
    history.window_size = 10
    turn = MagicMock()
    turn.role = "user"
    turn.text = "I need a restaurant app"
    turn.timestamp = datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc)
    history.turns = [turn]
    return history


async def test_save_calls_put_item(adapter, mock_history):
    with patch(
        "voice_server.persistence.history_adapter.put_item", new_callable=AsyncMock
    ) as mock_put:
        mock_put.return_value = True
        await adapter.save(mock_history)
        mock_put.assert_called_once()


async def test_save_retries_on_failure(adapter, mock_history):
    with patch(
        "voice_server.persistence.history_adapter.put_item", new_callable=AsyncMock
    ) as mock_put:
        mock_put.side_effect = [False, True]
        await adapter.save(mock_history)
        assert mock_put.call_count == 2


async def test_load_returns_data(adapter):
    now = int(time.time())
    item = {
        "session_id": {"S": "sess-001"},
        "record_type": {"S": "HISTORY"},
        "summary": {"S": "User wants booking"},
        "turns": {
            "L": [
                {
                    "M": {
                        "role": {"S": "user"},
                        "text": {"S": "hello"},
                        "timestamp": {"S": "2026-05-27T10:00:00+00:00"},
                    }
                }
            ]
        },
        "window_size": {"N": "10"},
        "updated_at": {"S": "2026-05-27T10:05:00+00:00"},
        "expires_at": {"N": str(now + 86400)},
    }
    with patch(
        "voice_server.persistence.history_adapter.get_item", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = item
        data = await adapter.load()
        assert data is not None
        assert data["summary"] == "User wants booking"
        assert len(data["turns"]) == 1


async def test_load_returns_none_when_expired(adapter):
    item = {
        "session_id": {"S": "sess-001"},
        "record_type": {"S": "HISTORY"},
        "summary": {"S": "old"},
        "turns": {"L": []},
        "window_size": {"N": "10"},
        "expires_at": {"N": "1000000"},
    }
    with patch(
        "voice_server.persistence.history_adapter.get_item", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = item
        data = await adapter.load()
        assert data is None


async def test_load_returns_none_when_not_found(adapter):
    with patch(
        "voice_server.persistence.history_adapter.get_item", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None
        data = await adapter.load()
        assert data is None
