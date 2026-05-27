from voice_server.bidi.connection import VoiceConnection, VoiceConnectionState


def test_initial_state_is_connecting():
    conn = VoiceConnection(session_id="s1")
    assert conn.state == VoiceConnectionState.CONNECTING


def test_transition_to_active():
    conn = VoiceConnection(session_id="s1")
    conn.transition_to(VoiceConnectionState.ACTIVE)
    assert conn.state == VoiceConnectionState.ACTIVE


def test_transition_connecting_to_reconnecting():
    conn = VoiceConnection(session_id="s1")
    conn.transition_to(VoiceConnectionState.ACTIVE)
    conn.transition_to(VoiceConnectionState.RECONNECTING)
    assert conn.state == VoiceConnectionState.RECONNECTING


def test_transition_to_draining():
    conn = VoiceConnection(session_id="s1")
    conn.transition_to(VoiceConnectionState.ACTIVE)
    conn.transition_to(VoiceConnectionState.DRAINING)
    assert conn.state == VoiceConnectionState.DRAINING


def test_transition_to_closed():
    conn = VoiceConnection(session_id="s1")
    conn.transition_to(VoiceConnectionState.CLOSED)
    assert conn.state == VoiceConnectionState.CLOSED


def test_expires_at_is_8_minutes_after_start():
    conn = VoiceConnection(session_id="s1")
    delta = conn.expires_at - conn.started_at
    assert delta.total_seconds() == 480


def test_reconnect_at_is_7_minutes_after_start():
    conn = VoiceConnection(session_id="s1")
    delta = conn.reconnect_at - conn.started_at
    assert delta.total_seconds() == 420


def test_unique_id_generated():
    conn1 = VoiceConnection(session_id="s1")
    conn2 = VoiceConnection(session_id="s1")
    assert conn1.id != conn2.id
