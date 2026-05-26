from datetime import datetime, timedelta, timezone

from voice_server.models.session import Session, SessionState
from voice_server.sessions.registry import SessionRegistry


def test_stale_session_detected():
    reg = SessionRegistry()
    session = Session(user_id="user-1", state=SessionState.STREAMING)
    session.last_activity = datetime.now(timezone.utc) - timedelta(seconds=35)
    reg.create(session)

    now = datetime.now(timezone.utc)
    timeout = 30
    stale = []
    for s in reg.all_sessions():
        if s.state in (SessionState.CONNECTING, SessionState.STREAMING):
            elapsed = (now - s.last_activity).total_seconds()
            if elapsed > timeout:
                stale.append(s.id)

    assert session.id in stale


def test_active_session_not_stale():
    reg = SessionRegistry()
    session = Session(user_id="user-1", state=SessionState.STREAMING)
    reg.create(session)

    now = datetime.now(timezone.utc)
    timeout = 30
    stale = []
    for s in reg.all_sessions():
        if s.state in (SessionState.CONNECTING, SessionState.STREAMING):
            elapsed = (now - s.last_activity).total_seconds()
            if elapsed > timeout:
                stale.append(s.id)

    assert len(stale) == 0


def test_closed_session_not_checked():
    reg = SessionRegistry()
    session = Session(user_id="user-1", state=SessionState.CLOSED)
    session.last_activity = datetime.now(timezone.utc) - timedelta(seconds=60)
    reg.create(session)

    now = datetime.now(timezone.utc)
    timeout = 30
    stale = []
    for s in reg.all_sessions():
        if s.state in (SessionState.CONNECTING, SessionState.STREAMING):
            elapsed = (now - s.last_activity).total_seconds()
            if elapsed > timeout:
                stale.append(s.id)

    assert len(stale) == 0
