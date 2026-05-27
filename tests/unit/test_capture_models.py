"""Unit tests for capture session models."""

import os

os.environ.setdefault("LOCAL_MODE", "true")

from voice_server.capture.models import (
    CaptureProgress,
    CaptureResult,
    CaptureSession,
    CaptureStatus,
)


def test_session_defaults():
    session = CaptureSession(project_name="test")
    assert session.status == CaptureStatus.PENDING
    assert session.project_name == "test"
    assert session.id  # non-empty UUID
    assert session.participants == []
    assert session.result is None
    assert session.error is None


def test_session_join_url():
    session = CaptureSession(project_name="test")
    assert f"/join/{session.id}" in session.join_url


def test_session_to_summary_dict():
    session = CaptureSession(project_name="my-project")
    d = session.to_summary_dict()
    assert d["session_id"] == session.id
    assert d["project_name"] == "my-project"
    assert d["status"] == "pending"
    assert "join_url" in d
    assert "created_at" in d


def test_session_to_detail_dict():
    session = CaptureSession(project_name="my-project", participants=["alice"])
    d = session.to_detail_dict()
    assert d["participants"] == ["alice"]
    assert "progress" in d
    assert d["progress"]["sections_covered"] == []


def test_progress_to_dict():
    progress = CaptureProgress(sections_covered=["Context", "Intent"], proposal_rounds=2)
    d = progress.to_dict()
    assert d["sections_covered"] == ["Context", "Intent"]
    assert d["proposal_rounds"] == 2
    assert d["alignment_reached"] is False


def test_result_to_dict():
    result = CaptureResult(
        intent_md="# Intent\n\n## Context\n",
        state={"project_name": "test"},
        audit_md="# Audit\n",
    )
    d = result.to_dict()
    assert "# Intent" in d["intent_md"]
    assert d["state"]["project_name"] == "test"


def test_session_touch():
    session = CaptureSession(project_name="test")
    original = session.updated_at
    session.touch()
    assert session.updated_at >= original
