from unittest.mock import AsyncMock, patch

import pytest

from voice_server.sessions.intent_session import IntentSession
from voice_server.sessions.user_lookup import find_active_intents, get_intent_summaries


@pytest.fixture
def mock_session_adapter():
    with patch("voice_server.sessions.user_lookup.IntentSessionAdapter") as mock:
        adapter_instance = AsyncMock()
        mock.return_value = adapter_instance
        yield adapter_instance


async def test_find_active_intents_returns_sessions(mock_session_adapter):
    session = IntentSession(intent_id="INT-001", user_email="alice@example.com")
    mock_session_adapter.query_by_email.return_value = [session]

    result = await find_active_intents("alice@example.com")
    assert len(result) == 1
    assert result[0].intent_id == "INT-001"


async def test_find_active_intents_empty(mock_session_adapter):
    mock_session_adapter.query_by_email.return_value = []

    result = await find_active_intents("nobody@example.com")
    assert result == []


async def test_get_intent_summaries_maps_fields(mock_session_adapter):
    session = IntentSession(
        intent_id="INT-002",
        user_email="bob@example.com",
        project_name="Test Project",
        active_channels={"voice", "slack"},
    )
    session.record_section_update("context", "voice")
    session.record_section_update("intent", "slack")
    mock_session_adapter.query_by_email.return_value = [session]

    summaries = await get_intent_summaries("bob@example.com")
    assert len(summaries) == 1
    s = summaries[0]
    assert s.intent_id == "INT-002"
    assert s.project_name == "Test Project"
    assert "context" in s.populated_fields
    assert "intent" in s.populated_fields
