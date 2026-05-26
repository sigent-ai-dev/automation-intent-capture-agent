"""Unit tests for the capture session store."""

import pytest

from voice_server.capture.models import CaptureSession, CaptureStatus
from voice_server.capture.store import CaptureStore


@pytest.fixture
def store():
    return CaptureStore()


def test_create_session(store):
    session = CaptureSession(project_name="test-project")
    result = store.create(session)
    assert result.id == session.id
    assert result.project_name == "test-project"
    assert result.status == CaptureStatus.PENDING


def test_get_session(store):
    session = CaptureSession(project_name="test")
    store.create(session)
    retrieved = store.get(session.id)
    assert retrieved is not None
    assert retrieved.id == session.id


def test_get_nonexistent_returns_none(store):
    assert store.get("nonexistent") is None


def test_list_active(store):
    s1 = CaptureSession(project_name="active1")
    s2 = CaptureSession(project_name="active2", status=CaptureStatus.ACTIVE)
    s3 = CaptureSession(project_name="done", status=CaptureStatus.COMPLETE)
    store.create(s1)
    store.create(s2)
    store.create(s3)
    active = store.list_active()
    assert len(active) == 2
    assert all(s.status in (CaptureStatus.PENDING, CaptureStatus.ACTIVE) for s in active)


def test_delete_session(store):
    session = CaptureSession(project_name="to-delete")
    store.create(session)
    deleted = store.delete(session.id)
    assert deleted is not None
    assert deleted.status == CaptureStatus.CANCELLED
    assert store.get(session.id) is None


def test_delete_nonexistent_returns_none(store):
    assert store.delete("nonexistent") is None
