from voice_server.sessions.intent_session import ChannelContribution, IntentSession


def test_intent_session_creation():
    session = IntentSession(intent_id="INT-001", user_email="alice@example.com")
    assert session.intent_id == "INT-001"
    assert session.user_email == "alice@example.com"
    assert session.elicitation_status == "in_progress"
    assert session.is_active()
    assert session.version == 1


def test_touch_updates_activity_and_channel():
    session = IntentSession(intent_id="INT-001", user_email="alice@example.com")
    original_time = session.last_activity
    session.touch("slack")
    assert "slack" in session.active_channels
    assert session.last_activity >= original_time


def test_record_section_update():
    session = IntentSession(intent_id="INT-001", user_email="alice@example.com")
    session.record_section_update("context", "voice")
    session.record_section_update("intent", "slack")

    assert "context" in session.section_attributions
    assert session.section_attributions["context"].channel == "voice"
    assert session.section_attributions["intent"].channel == "slack"
    assert "voice" in session.active_channels
    assert "slack" in session.active_channels


def test_is_active_false_when_confirmed():
    session = IntentSession(
        intent_id="INT-001", user_email="alice@example.com", elicitation_status="confirmed"
    )
    assert not session.is_active()


def test_channel_contribution_has_timestamp():
    contrib = ChannelContribution(channel="voice")
    assert contrib.channel == "voice"
    assert contrib.timestamp is not None
