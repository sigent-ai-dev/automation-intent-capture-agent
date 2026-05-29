from unittest.mock import MagicMock, patch

from voice_server.channels.text_agent import invoke_text_agent
from voice_server.persistence.intent_history_adapter import IntentHistory


async def test_invoke_text_agent_returns_response():
    mock_agent_instance = MagicMock()
    mock_agent_instance.return_value = "Here's what I captured for quality attributes."

    with patch("voice_server.channels.text_agent.Agent", return_value=mock_agent_instance):
        result = await invoke_text_agent(
            message="Performance should be under 200ms",
            channel="slack",
            user_email="alice@example.com",
        )
        assert "quality attributes" in result


async def test_invoke_text_agent_handles_exception():
    mock_agent_instance = MagicMock()
    mock_agent_instance.side_effect = RuntimeError("Bedrock unavailable")

    with patch("voice_server.channels.text_agent.Agent", return_value=mock_agent_instance):
        result = await invoke_text_agent(
            message="test",
            channel="claude",
            user_email="alice@example.com",
        )
        assert "issue" in result or "try again" in result


async def test_invoke_text_agent_with_history_and_doc():
    history = IntentHistory(intent_id="INT-001")
    history.add_turn("user", "The problem is slow onboarding", "voice")
    history.add_turn("agent", "I've captured that as context", "voice")

    mock_doc = MagicMock()
    mock_doc.populated_sections.return_value = ["context"]
    mock_doc.empty_sections.return_value = ["intent", "motivation"]
    mock_doc.intent_id = "INT-001"
    mock_doc.project_name = "Test"

    mock_agent_instance = MagicMock()
    mock_agent_instance.return_value = "Let's discuss the intent next."

    with patch("voice_server.channels.text_agent.Agent", return_value=mock_agent_instance):
        result = await invoke_text_agent(
            message="The intent is to reduce onboarding time",
            channel="slack",
            user_email="bob@example.com",
            history=history,
            doc=mock_doc,
        )
        assert "intent" in result.lower() or "onboarding" in result.lower()
