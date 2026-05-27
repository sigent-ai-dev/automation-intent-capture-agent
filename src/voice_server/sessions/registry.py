from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from voice_server.models.session import Session, SessionState
from voice_server.observability.logging import get_logger

if TYPE_CHECKING:
    from voice_server.persistence.session_adapter import SessionPersistenceAdapter

logger = get_logger(__name__)


class SessionRegistry:
    def __init__(self, persistence: SessionPersistenceAdapter | None = None) -> None:
        self._sessions: dict[str, Session] = {}
        self._user_sessions: dict[str, str] = {}
        self._persistence = persistence

    def create(self, session: Session) -> Session | None:
        existing_session_id = self._user_sessions.get(session.user_id)
        if existing_session_id:
            logger.info(
                "replacing_existing_session",
                user_id=session.user_id,
                old_session_id=existing_session_id,
                new_session_id=session.id,
            )
            self.remove(existing_session_id)

        self._sessions[session.id] = session
        self._user_sessions[session.user_id] = session.id
        if self._persistence:
            asyncio.create_task(self._persistence.save(session))
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_by_user(self, user_id: str) -> Session | None:
        session_id = self._user_sessions.get(user_id)
        if session_id:
            return self._sessions.get(session_id)
        return None

    def remove(self, session_id: str) -> Session | None:
        session = self._sessions.pop(session_id, None)
        if session:
            self._user_sessions.pop(session.user_id, None)
            session.transition_to(SessionState.CLOSED)
            if self._persistence:
                asyncio.create_task(self._persistence.save(session))
        return session

    def list_active(self) -> list[Session]:
        return [
            s
            for s in self._sessions.values()
            if s.state in (SessionState.CONNECTING, SessionState.STREAMING)
        ]

    @property
    def active_count(self) -> int:
        return len(self.list_active())

    def all_sessions(self) -> list[Session]:
        return list(self._sessions.values())


registry = SessionRegistry()
