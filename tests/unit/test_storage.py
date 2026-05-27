from datetime import date
from unittest.mock import patch

import pytest

from voice_server.elicitation.intent_doc import IntentDocument
from voice_server.elicitation.storage import (
    ensure_intent_dir,
    find_draft_intents,
    list_intents,
    load_intent,
    next_intent_id,
    save_intent,
)


@pytest.fixture
def intent_dir(tmp_path):
    with patch("voice_server.elicitation.storage._intent_dir", return_value=tmp_path / ".intent"):
        yield tmp_path / ".intent"


def test_ensure_intent_dir_creates(intent_dir):
    assert not intent_dir.exists()
    result = ensure_intent_dir()
    assert result.exists()
    assert result == intent_dir


def test_next_intent_id_empty(intent_dir):
    assert next_intent_id() == "INT-001"


def test_next_intent_id_increments(intent_dir):
    intent_dir.mkdir(parents=True)
    (intent_dir / "INT-001.md").write_text("test")
    (intent_dir / "INT-002.md").write_text("test")
    assert next_intent_id() == "INT-003"


def test_save_intent_atomic(intent_dir):
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Test",
        captured_date=date(2026, 5, 27),
    )
    path = save_intent(doc)
    assert path.exists()
    assert path.name == "INT-001.md"
    assert not (intent_dir / ".INT-001.md.tmp").exists()


def test_load_intent_roundtrip(intent_dir):
    doc = IntentDocument(
        intent_id="INT-001",
        project_name="Load Test",
        context="some context",
        intent="do the thing",
        motivation="because",
    )
    save_intent(doc)
    loaded = load_intent("INT-001")
    assert loaded is not None
    assert loaded.project_name == "Load Test"
    assert loaded.context == "some context"


def test_load_intent_not_found(intent_dir):
    assert load_intent("INT-999") is None


def test_list_intents(intent_dir):
    intent_dir.mkdir(parents=True)
    (intent_dir / "INT-001.md").write_text("test")
    (intent_dir / "INT-003.md").write_text("test")
    (intent_dir / "other.md").write_text("ignored")
    result = list_intents()
    assert result == ["INT-001", "INT-003"]


def test_find_draft_intents(intent_dir):
    doc1 = IntentDocument(intent_id="INT-001", project_name="Draft", status="draft")
    doc2 = IntentDocument(intent_id="INT-002", project_name="Done", status="confirmed")
    save_intent(doc1)
    save_intent(doc2)
    drafts = find_draft_intents()
    assert drafts == ["INT-001"]
