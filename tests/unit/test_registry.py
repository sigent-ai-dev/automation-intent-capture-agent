from voice_server.models.session import Session, SessionState
from voice_server.sessions.registry import SessionRegistry


def test_create_and_get():
    reg = SessionRegistry()
    session = Session(user_id="user-1")
    reg.create(session)
    assert reg.get(session.id) is session


def test_get_by_user():
    reg = SessionRegistry()
    session = Session(user_id="user-1")
    reg.create(session)
    assert reg.get_by_user("user-1") is session
    assert reg.get_by_user("user-2") is None


def test_remove():
    reg = SessionRegistry()
    session = Session(user_id="user-1")
    reg.create(session)
    removed = reg.remove(session.id)
    assert removed is session
    assert removed.state == SessionState.CLOSED
    assert reg.get(session.id) is None


def test_remove_nonexistent():
    reg = SessionRegistry()
    assert reg.remove("nonexistent") is None


def test_list_active():
    reg = SessionRegistry()
    s1 = Session(user_id="user-1", state=SessionState.STREAMING)
    s2 = Session(user_id="user-2", state=SessionState.CONNECTING)
    s3 = Session(user_id="user-3", state=SessionState.CLOSED)
    reg.create(s1)
    reg.create(s2)
    reg.create(s3)
    active = reg.list_active()
    assert len(active) == 2
    assert s3 not in active


def test_single_session_per_user():
    reg = SessionRegistry()
    s1 = Session(user_id="user-1")
    s2 = Session(user_id="user-1")
    reg.create(s1)
    reg.create(s2)
    assert reg.get(s1.id) is None
    assert reg.get(s2.id) is s2
    assert s1.state == SessionState.CLOSED


def test_active_count():
    reg = SessionRegistry()
    reg.create(Session(user_id="u1", state=SessionState.STREAMING))
    reg.create(Session(user_id="u2", state=SessionState.STREAMING))
    assert reg.active_count == 2
