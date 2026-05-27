from voice_server.notifications.events import ErrorOccurred, IntentFinalised
from voice_server.notifications.slack import (
    _format_error_notification,
    _format_intent_notification,
)


def test_intent_notification_short_content():
    event = IntentFinalised(
        intent_id="INT-001",
        project_name="Restaurant Booking",
        intent_summary="Enable online table booking for customers",
        actor="voice",
        populated_fields=["context", "intent", "motivation", "quality_attributes"],
        open_clarifications=1,
        full_content="Short content under 2000 chars",
    )
    payload = _format_intent_notification(event, "#test-channel")
    assert payload["channel"] == "#test-channel"
    assert "Restaurant Booking" in payload["text"]
    assert any("Intent:" in str(b) for b in payload["blocks"])
    content_blocks = [b for b in payload["blocks"] if "```" in str(b.get("text", {}))]
    assert len(content_blocks) == 1


def test_intent_notification_long_content():
    event = IntentFinalised(
        intent_id="INT-002",
        project_name="Big Project",
        intent_summary="Do big things",
        actor="voice",
        populated_fields=["context", "intent", "motivation"],
        open_clarifications=0,
        full_content="x" * 3000,
    )
    payload = _format_intent_notification(event, "")
    assert "channel" not in payload
    context_blocks = [b for b in payload["blocks"] if b.get("type") == "context"]
    has_too_long_msg = any("too long" in str(b) for b in context_blocks)
    assert has_too_long_msg


def test_intent_notification_no_channel():
    event = IntentFinalised(
        intent_id="INT-001",
        project_name="Test",
        intent_summary="Test intent",
        actor="voice",
    )
    payload = _format_intent_notification(event, "")
    assert "channel" not in payload


def test_error_notification_format():
    event = ErrorOccurred(
        error_type="VOICE_SERVICE_UNAVAILABLE",
        session_id="sess-123",
        description="All retry attempts exhausted.",
    )
    payload = _format_error_notification(event, "#alerts")
    assert payload["channel"] == "#alerts"
    assert "VOICE_SERVICE_UNAVAILABLE" in str(payload["blocks"])
    assert "sess-123" in str(payload["blocks"])


def test_error_notification_no_channel():
    event = ErrorOccurred(
        error_type="PERSISTENCE_FAILURE",
        session_id="sess-456",
        description="DynamoDB unreachable.",
    )
    payload = _format_error_notification(event, "")
    assert "channel" not in payload
