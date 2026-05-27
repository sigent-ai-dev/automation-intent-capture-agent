from voice_server.bidi.history import ConversationHistory


def test_add_turn_and_get_recent():
    h = ConversationHistory(session_id="s1", window_size=3)
    h.add_turn("user", "Hello")
    h.add_turn("assistant", "Hi there")
    recent = h.get_recent()
    assert len(recent) == 2
    assert recent[0].role == "user"
    assert recent[1].role == "assistant"


def test_sliding_window_limits_turns():
    h = ConversationHistory(session_id="s1", window_size=3)
    for i in range(5):
        h.add_turn("user", f"message {i}")
    assert len(h.turns) == 3
    assert h.turns[0].text == "message 2"


def test_summary_generated_on_overflow():
    h = ConversationHistory(session_id="s1", window_size=3)
    for i in range(5):
        h.add_turn("user", f"msg{i}")
    assert h.summary != ""
    assert "msg0" in h.summary
    assert "msg1" in h.summary


def test_get_summary_and_recent():
    h = ConversationHistory(session_id="s1", window_size=2)
    h.add_turn("user", "first")
    h.add_turn("assistant", "second")
    h.add_turn("user", "third")
    result = h.get_summary_and_recent()
    assert "[Summary of earlier conversation]" in result
    assert "third" in result


def test_overflow_beyond_window_accumulates_summary():
    h = ConversationHistory(session_id="s1", window_size=2)
    for i in range(10):
        h.add_turn("user", f"turn{i}")
    assert len(h.turns) == 2
    assert "turn0" in h.summary
    assert "turn7" in h.summary
    assert h.turns[-1].text == "turn9"
