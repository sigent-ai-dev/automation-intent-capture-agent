import time
from unittest.mock import AsyncMock, patch

import pytest

from voice_server.persistence.session_adapter import SessionPersistenceAdapter


@pytest.fixture
def adapter():
    return SessionPersistenceAdapter()


@pytest.fixture
def mock_session():
    from voice_server.models.session import Session, SessionState

    s = Session(user_id="user-123")
    s.state = SessionState.STREAMING
    return s


async def test_save_calls_put_item(adapter, mock_session):
    with patch("voice_server.persistence.session_adapter.put_item", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = True
        await adapter.save(mock_session)
        mock_put.assert_called_once()


async def test_save_retries_on_failure(adapter, mock_session):
    with patch("voice_server.persistence.session_adapter.put_item", new_callable=AsyncMock) as mock_put:
        mock_put.side_effect = [False, True]
        await adapter.save(mock_session)
        assert mock_put.call_count == 2


async def test_load_returns_data(adapter):
    item = {
        "session_id": {"S": "sess-001"},
        "record_type": {"S": "SESSION"},
        "user_id": {"S": "user-123"},
        "state": {"S": "streaming"},
        "connected_at": {"S": "2026-05-27T10:00:00+00:00"},
        "last_activity": {"N": str(int(time.time()))},
        "expires_at": {"N": str(int(time.time()) + 86400)},
    }
    with patch("voice_server.persistence.session_adapter.get_item", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = item
        data = await adapter.load("sess-001")
        assert data is not None
        assert data["id"] == "sess-001"
        assert data["user_id"] == "user-123"


async def test_load_returns_none_when_expired(adapter):
    item = {
        "session_id": {"S": "sess-001"},
        "record_type": {"S": "SESSION"},
        "user_id": {"S": "user-123"},
        "state": {"S": "streaming"},
        "connected_at": {"S": "2026-05-27T10:00:00+00:00"},
        "last_activity": {"N": "1000000"},
        "expires_at": {"N": "1000000"},
    }
    with patch("voice_server.persistence.session_adapter.get_item", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = item
        data = await adapter.load("sess-001")
        assert data is None


async def test_load_returns_none_when_not_found(adapter):
    with patch("voice_server.persistence.session_adapter.get_item", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        data = await adapter.load("sess-999")
        assert data is None


async def test_delete_calls_delete_item(adapter):
    with patch("voice_server.persistence.session_adapter.delete_item", new_callable=AsyncMock) as mock_del:
        mock_del.return_value = True
        await adapter.delete("sess-001")
        mock_del.assert_called_once()


async def test_list_active_sessions(adapter):
    now = int(time.time())
    items = [
        {
            "session_id": {"S": "sess-001"},
            "user_id": {"S": "user-1"},
            "state": {"S": "streaming"},
            "connected_at": {"S": "2026-05-27T10:00:00+00:00"},
            "last_activity": {"N": str(now)},
            "expires_at": {"N": str(now + 86400)},
        }
    ]
    with patch("voice_server.persistence.session_adapter.query_gsi", new_callable=AsyncMock) as mock_gsi:
        mock_gsi.return_value = items
        result = await adapter.list_active_sessions()
        assert len(result) == 1
        assert result[0]["id"] == "sess-001"
