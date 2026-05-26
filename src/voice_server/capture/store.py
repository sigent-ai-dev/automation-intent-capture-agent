"""In-memory capture session store. Will be replaced with DynamoDB in issue #9."""

from voice_server.capture.models import CaptureSession, CaptureStatus
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)


class CaptureStore:
    def __init__(self) -> None:
        self._sessions: dict[str, CaptureSession] = {}

    def create(self, session: CaptureSession) -> CaptureSession:
        self._sessions[session.id] = session
        logger.info("capture_session_created", session_id=session.id, project=session.project_name)
        return session

    def get(self, session_id: str) -> CaptureSession | None:
        return self._sessions.get(session_id)

    def list_active(self) -> list[CaptureSession]:
        return [
            s
            for s in self._sessions.values()
            if s.status in (CaptureStatus.PENDING, CaptureStatus.ACTIVE)
        ]

    def delete(self, session_id: str) -> CaptureSession | None:
        session = self._sessions.pop(session_id, None)
        if session:
            session.status = CaptureStatus.CANCELLED
            session.touch()
            logger.info("capture_session_cancelled", session_id=session_id)
        return session


capture_store = CaptureStore()
