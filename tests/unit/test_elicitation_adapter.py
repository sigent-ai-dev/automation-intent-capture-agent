import time
from unittest.mock import AsyncMock, patch

import pytest

from voice_server.persistence.elicitation_adapter import ElicitationPersistenceAdapter


@pytest.fixture
def adapter():
    return ElicitationPersistenceAdapter(session_id="sess-001")


async def test_save_calls_put_item(adapter):
    with patch("voice_server.persistence.elicitation_adapter.put_item", new_callable=AsyncMock) as mock_put:
        mock_put.return_value = True
        await adapter.save(
            intent_id="INT-001",
            populated_fields=["context", "intent"],
            outstanding_clarifications=["CLR-001"],
            status="in_progress",
        )
        mock_put.assert_called_once()


async def test_save_retries_on_failure(adapter):
    with patch("voice_server.persistence.elicitation_adapter.put_item", new_callable=AsyncMock) as mock_put:
        mock_put.side_effect = [False, True]
        await adapter.save(
            intent_id="INT-001",
            populated_fields=["context"],
            outstanding_clarifications=[],
            status="in_progress",
        )
        assert mock_put.call_count == 2


async def test_load_returns_data(adapter):
    now = int(time.time())
    item = {
        "session_id": {"S": "sess-001"},
        "record_type": {"S": "ELICITATION"},
        "intent_id": {"S": "INT-001"},
        "populated_fields": {"L": [{"S": "context"}, {"S": "intent"}]},
        "outstanding_clarifications": {"L": [{"S": "CLR-001"}]},
        "elicitation_status": {"S": "in_progress"},
        "updated_at": {"S": "2026-05-27T10:00:00+00:00"},
        "expires_at": {"N": str(now + 86400)},
    }
    with patch("voice_server.persistence.elicitation_adapter.get_item", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = item
        data = await adapter.load()
        assert data is not None
        assert data["intent_id"] == "INT-001"
        assert data["populated_fields"] == ["context", "intent"]
        assert data["outstanding_clarifications"] == ["CLR-001"]


async def test_load_returns_none_when_expired(adapter):
    item = {
        "session_id": {"S": "sess-001"},
        "record_type": {"S": "ELICITATION"},
        "intent_id": {"S": "INT-001"},
        "populated_fields": {"L": []},
        "outstanding_clarifications": {"L": []},
        "elicitation_status": {"S": "in_progress"},
        "expires_at": {"N": "1000000"},
    }
    with patch("voice_server.persistence.elicitation_adapter.get_item", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = item
        data = await adapter.load()
        assert data is None


async def test_load_returns_none_when_not_found(adapter):
    with patch("voice_server.persistence.elicitation_adapter.get_item", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        data = await adapter.load()
        assert data is None
