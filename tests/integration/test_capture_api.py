"""Integration tests for the capture session REST API."""

import pytest
from httpx import ASGITransport, AsyncClient

from voice_server.capture.models import CaptureResult, CaptureStatus
from voice_server.capture.store import capture_store
from voice_server.main import app


@pytest.fixture(autouse=True)
def clean_capture_store():
    yield
    capture_store._sessions.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_create_session(client):
    resp = await client.post("/sessions", json={"project_name": "test-project"})
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert "join_url" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_sessions_empty(client):
    resp = await client.get("/sessions")
    assert resp.status_code == 200
    assert resp.json()["sessions"] == []


@pytest.mark.asyncio
async def test_list_sessions_with_active(client):
    await client.post("/sessions", json={"project_name": "proj1"})
    await client.post("/sessions", json={"project_name": "proj2"})
    resp = await client.get("/sessions")
    assert resp.status_code == 200
    assert len(resp.json()["sessions"]) == 2


@pytest.mark.asyncio
async def test_get_session(client):
    create_resp = await client.post("/sessions", json={"project_name": "test"})
    session_id = create_resp.json()["session_id"]

    resp = await client.get(f"/sessions/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["status"] == "pending"
    assert "progress" in data
    assert "participants" in data


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    resp = await client.get("/sessions/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_result_not_complete(client):
    create_resp = await client.post("/sessions", json={"project_name": "test"})
    session_id = create_resp.json()["session_id"]

    resp = await client.get(f"/sessions/{session_id}/result")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_result_when_complete(client):
    create_resp = await client.post("/sessions", json={"project_name": "test"})
    session_id = create_resp.json()["session_id"]

    # Simulate completion
    session = capture_store.get(session_id)
    session.status = CaptureStatus.COMPLETE
    session.result = CaptureResult(
        intent_md="# Intent\n\n## Context\nTest\n",
        state={"project_name": "test", "current_phase": "capture"},
        audit_md="# Audit\n\n## Entry\n",
    )

    resp = await client.get(f"/sessions/{session_id}/result")
    assert resp.status_code == 200
    data = resp.json()
    assert "intent_md" in data
    assert "state" in data
    assert "audit_md" in data


@pytest.mark.asyncio
async def test_cancel_session(client):
    create_resp = await client.post("/sessions", json={"project_name": "test"})
    session_id = create_resp.json()["session_id"]

    resp = await client.delete(f"/sessions/{session_id}")
    assert resp.status_code == 204

    # Verify it's gone from active list
    list_resp = await client.get("/sessions")
    assert len(list_resp.json()["sessions"]) == 0


@pytest.mark.asyncio
async def test_cancel_nonexistent(client):
    resp = await client.delete("/sessions/nonexistent")
    assert resp.status_code == 404
