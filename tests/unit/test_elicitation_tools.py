from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from voice_server.elicitation.intent_doc import IntentDocument
from voice_server.elicitation.storage import save_intent
from voice_server.elicitation.tools import (
    create_intent,
    finalise_intent,
    read_intent,
    update_intent_section,
)


@pytest.fixture
def intent_dir(tmp_path):
    with patch("voice_server.elicitation.storage._intent_dir", return_value=tmp_path / ".intent"):
        yield tmp_path / ".intent"


def test_create_intent_success(intent_dir):
    result = create_intent(
        project_name="My App",
        context="Need an app",
        intent="Build a mobile app for customers",
        motivation="Competitors have apps",
    )
    assert result["status"] == "success"
    assert result["intent_id"] == "INT-001"
    assert (intent_dir / "INT-001.md").exists()


def test_create_intent_validation_error(intent_dir):
    result = create_intent(project_name="", context="x", intent="", motivation="x")
    assert result["status"] == "error"


def test_update_intent_section_replace(intent_dir):
    doc = IntentDocument(intent_id="INT-001", project_name="Test", context="old")
    save_intent(doc)
    result = update_intent_section(intent_id="INT-001", section="context", content="new context")
    assert result["status"] == "success"
    from voice_server.elicitation.storage import load_intent

    updated = load_intent("INT-001")
    assert updated.context == "new context"


def test_update_intent_section_append(intent_dir):
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Test",
        quality_attributes=["- **QA-001**: Fast"],
    )
    save_intent(doc)
    result = update_intent_section(
        intent_id="INT-001",
        section="quality_attributes",
        content="Secure",
        append=True,
    )
    assert result["status"] == "success"
    from voice_server.elicitation.storage import load_intent

    updated = load_intent("INT-001")
    assert len(updated.quality_attributes) == 2
    assert "QA-002" in updated.quality_attributes[1]


def test_update_intent_section_invalid_section(intent_dir):
    doc = IntentDocument(intent_id="INT-001", project_name="Test")
    save_intent(doc)
    result = update_intent_section(intent_id="INT-001", section="bogus", content="x")
    assert result["status"] == "error"
    assert "Invalid section" in result["content"][0]["text"]


def test_update_intent_section_not_found(intent_dir):
    result = update_intent_section(intent_id="INT-999", section="context", content="x")
    assert result["status"] == "error"


def test_read_intent_success(intent_dir):
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Read Test",
        context="Has context",
        intent="Has intent",
    )
    save_intent(doc)
    result = read_intent(intent_id="INT-001")
    assert result["status"] == "success"
    assert "context" in result["populated_sections"]
    assert "motivation" in result["empty_sections"]


def test_read_intent_not_found(intent_dir):
    result = read_intent(intent_id="INT-999")
    assert result["status"] == "error"


def test_finalise_intent_success(intent_dir):
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Final",
        context="Has context",
        intent="Do the thing",
        motivation="Because",
    )
    save_intent(doc)
    result = finalise_intent(intent_id="INT-001")
    assert result["status"] == "success"
    from voice_server.elicitation.storage import load_intent

    updated = load_intent("INT-001")
    assert updated.status == "confirmed"


def test_finalise_intent_missing_mandatory(intent_dir):
    doc = IntentDocument(intent_id="INT-001", project_name="Incomplete", context="Has context")
    save_intent(doc)
    result = finalise_intent(intent_id="INT-001")
    assert result["status"] == "error"
    assert "missing mandatory" in result["content"][0]["text"].lower()


def test_finalise_intent_idempotent(intent_dir):
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Already Done",
        context="c",
        intent="i",
        motivation="m",
        status="confirmed",
    )
    save_intent(doc)
    result = finalise_intent(intent_id="INT-001")
    assert result["status"] == "success"
    assert "already confirmed" in result["content"][0]["text"].lower()
