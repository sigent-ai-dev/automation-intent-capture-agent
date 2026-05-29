from voice_server.persistence.intent_history_adapter import IntentHistory, IntentTurn


def test_add_turn_increments_count():
    history = IntentHistory(intent_id="INT-001")
    history.add_turn("user", "Hello", "voice")
    history.add_turn("agent", "Hi there", "voice")
    assert history.turn_count == 2
    assert len(history.turns) == 2


def test_turn_has_channel_annotation():
    history = IntentHistory(intent_id="INT-001")
    history.add_turn("user", "Hello from slack", "slack")
    assert history.turns[0].channel == "slack"
    assert history.turns[0].role == "user"


def test_needs_summarisation_below_threshold():
    history = IntentHistory(intent_id="INT-001")
    for i in range(10):
        history.add_turn("user", f"turn {i}", "voice")
    assert not history.needs_summarisation()


def test_needs_summarisation_above_threshold():
    history = IntentHistory(intent_id="INT-001")
    for i in range(35):
        history.add_turn("user", f"turn {i}", "voice")
    assert history.needs_summarisation()


def test_get_overflow_turns():
    history = IntentHistory(intent_id="INT-001")
    for i in range(35):
        history.add_turn("user", f"turn {i}", "voice")
    overflow = history.get_overflow_turns()
    assert len(overflow) == 5


def test_apply_summarisation_trims_turns():
    history = IntentHistory(intent_id="INT-001")
    for i in range(35):
        history.add_turn("user", f"turn {i}", "voice")
    history.apply_summarisation("Summary of first 5 turns")
    assert len(history.turns) == 30
    assert "Summary of first 5 turns" in history.summary


def test_get_context_for_agent_includes_summary():
    history = IntentHistory(intent_id="INT-001", summary="Prior conversation about context")
    history.add_turn("user", "Adding quality attributes", "slack")
    context = history.get_context_for_agent()
    assert "Prior conversation about context" in context
    assert "[slack] user: Adding quality attributes" in context


def test_get_context_for_agent_no_summary():
    history = IntentHistory(intent_id="INT-001")
    history.add_turn("user", "Hello", "voice")
    history.add_turn("agent", "Hi", "voice")
    context = history.get_context_for_agent()
    assert "[voice] user: Hello" in context
    assert "[voice] agent: Hi" in context
    assert "Summary" not in context
