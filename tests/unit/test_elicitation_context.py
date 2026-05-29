from voice_server.elicitation.tools import (
    _get_current_channel,
    _get_current_user_email,
    set_elicitation_context,
)


def test_set_and_get_channel():
    set_elicitation_context("slack", "alice@example.com")
    assert _get_current_channel() == "slack"
    assert _get_current_user_email() == "alice@example.com"


def test_defaults():
    set_elicitation_context("voice", "")
    assert _get_current_channel() == "voice"
    assert _get_current_user_email() == ""


def test_channel_override():
    set_elicitation_context("voice", "user@test.com")
    assert _get_current_channel() == "voice"
    set_elicitation_context("claude", "user@test.com")
    assert _get_current_channel() == "claude"
