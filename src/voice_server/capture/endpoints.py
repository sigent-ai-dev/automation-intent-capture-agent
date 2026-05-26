"""REST API endpoints for capture session management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from voice_server.capture.models import CaptureSession, CaptureStatus
from voice_server.capture.store import capture_store

router = APIRouter(prefix="/sessions", tags=["capture"])


class CreateSessionRequest(BaseModel):
    project_name: str = "unnamed"


class CreateSessionResponse(BaseModel):
    session_id: str
    join_url: str
    status: str
    created_at: str


@router.post("", response_model=CreateSessionResponse, status_code=201)
async def create_session(body: CreateSessionRequest) -> dict:
    session = CaptureSession(project_name=body.project_name)
    capture_store.create(session)
    return session.to_summary_dict()


@router.get("")
async def list_sessions() -> dict:
    sessions = capture_store.list_active()
    return {"sessions": [s.to_summary_dict() for s in sessions]}


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict:
    session = capture_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_detail_dict()


@router.get("/{session_id}/result")
async def get_session_result(session_id: str) -> dict:
    session = capture_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != CaptureStatus.COMPLETE:
        raise HTTPException(status_code=404, detail="Session not yet complete")
    if not session.result:
        raise HTTPException(status_code=404, detail="No result available")
    return session.result.to_dict()


@router.delete("/{session_id}", status_code=204)
async def cancel_session(session_id: str) -> None:
    session = capture_store.delete(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
