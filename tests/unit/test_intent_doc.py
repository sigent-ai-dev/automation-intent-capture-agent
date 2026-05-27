from datetime import date

from voice_server.elicitation.intent_doc import IntentDocument


def test_render_minimal():
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Test Project",
        captured_date=date(2026, 5, 27),
    )
    rendered = doc.render()
    assert "# Intent: Test Project" in rendered
    assert "**Intent ID**: INT-001" in rendered
    assert "**Status**: draft" in rendered
    assert "## Context" in rendered


def test_render_with_content():
    doc = IntentDocument(
        intent_id="INT-002",
        project_name="Booking System",
        context="Restaurant needs online reservations",
        intent="Enable online table booking for customers",
        motivation="Losing walk-in customers to competitors with apps",
        quality_attributes=["- **QA-001**: Response time under 2 seconds"],
        success_criteria=["- **SC-001**: 50% of bookings made online within 3 months"],
    )
    rendered = doc.render()
    assert "Restaurant needs online reservations" in rendered
    assert "Enable online table booking" in rendered
    assert "QA-001" in rendered
    assert "SC-001" in rendered


def test_parse_roundtrip():
    doc = IntentDocument(
        intent_id="INT-003",
        project_name="Roundtrip Test",
        captured_date=date(2026, 1, 15),
        actor="voice",
        status="confirmed",
        context="Some context here",
        intent="Do the thing",
        motivation="Because reasons",
        quality_attributes=["- **QA-001**: Fast"],
        success_criteria=["- **SC-001**: Works"],
        assumptions=["- **ASM-001** [high]: Stuff exists"],
    )
    rendered = doc.render()
    parsed = IntentDocument.parse(rendered)
    assert parsed.intent_id == "INT-003"
    assert parsed.project_name == "Roundtrip Test"
    assert parsed.status == "confirmed"
    assert parsed.context == "Some context here"
    assert parsed.intent == "Do the thing"
    assert parsed.motivation == "Because reasons"
    assert len(parsed.quality_attributes) == 1
    assert len(parsed.success_criteria) == 1
    assert len(parsed.assumptions) == 1


def test_parse_missing_sections():
    text = "# Intent: Minimal\n\n**Intent ID**: INT-001\n**Captured**: 2026-05-27\n**Actor**: voice\n**Status**: draft\n"
    doc = IntentDocument.parse(text)
    assert doc.intent_id == "INT-001"
    assert doc.context == ""
    assert doc.intent == ""


def test_populated_sections():
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Test",
        context="Has context",
        intent="Has intent",
    )
    populated = doc.populated_sections()
    assert "context" in populated
    assert "intent" in populated
    assert "motivation" not in populated


def test_empty_sections():
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Test",
        context="Has context",
        intent="Has intent",
        motivation="Has motivation",
    )
    empty = doc.empty_sections()
    assert "context" not in empty
    assert "quality_attributes" in empty
    assert "success_criteria" in empty
