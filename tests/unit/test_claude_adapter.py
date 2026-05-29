from unittest.mock import AsyncMock, patch

from voice_server.channels.claude.skill import intent_capture, _resolve_claude_identity


async def test_list_returns_empty_when_no_intents():
    with patch("voice_server.channels.claude.skill.get_intent_summaries", new_callable=AsyncMock) as mock:
        mock.return_value = []
        result = await intent_capture(action="list", user_email="alice@example.com")
        assert result["intents"] == []


async def test_list_returns_intents():
    from voice_server.sessions.user_lookup import IntentSummary

    summary = IntentSummary(
        intent_id="INT-001",
        project_name="Test",
        elicitation_status="in_progress",
        populated_fields=["context"],
        last_channel="voice",
        last_activity="2026-05-29T12:00:00",
    )
    with patch("voice_server.channels.claude.skill.get_intent_summaries", new_callable=AsyncMock) as mock:
        mock.return_value = [summary]
        result = await intent_capture(action="list", user_email="alice@example.com")
        assert len(result["intents"]) == 1
        assert result["intents"][0]["intent_id"] == "INT-001"


async def test_start_warns_about_existing_drafts():
    from voice_server.sessions.intent_session import IntentSession

    session = IntentSession(intent_id="INT-001", user_email="alice@example.com")
    with patch("voice_server.channels.claude.skill.find_active_intents", new_callable=AsyncMock) as mock:
        mock.return_value = [session]
        result = await intent_capture(
            action="start", project_name="New Project", user_email="alice@example.com"
        )
        assert "1 active draft" in result["agent_response"]


async def test_unknown_action_returns_error():
    result = await intent_capture(action="invalid", user_email="alice@example.com")
    assert "error" in result
    assert "Unknown action" in result["error"]


async def test_no_identity_returns_error():
    with patch("voice_server.channels.claude.skill._resolve_claude_identity", return_value=""):
        result = await intent_capture(action="list")
        assert "error" in result
        assert "Cannot determine user identity" in result["error"]


def test_resolve_claude_identity_from_git():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = type("Result", (), {"returncode": 0, "stdout": "dev@test.com\n"})()
        email = _resolve_claude_identity()
        assert email == "dev@test.com"
