from unittest.mock import MagicMock


def test_extract_user_id_from_alb_header(monkeypatch):
    monkeypatch.setenv("LOCAL_MODE", "false")
    from importlib import reload

    import voice_server.config
    reload(voice_server.config)
    import voice_server.ws.auth
    reload(voice_server.ws.auth)

    ws = MagicMock()
    ws.headers = {"x-amzn-oidc-identity": "cognito-sub-123"}
    user_id = voice_server.ws.auth.extract_user_id(ws)
    assert user_id == "cognito-sub-123"


def test_extract_user_id_missing_header(monkeypatch):
    monkeypatch.setenv("LOCAL_MODE", "false")
    from importlib import reload

    import voice_server.config
    reload(voice_server.config)
    import voice_server.ws.auth
    reload(voice_server.ws.auth)

    ws = MagicMock()
    ws.headers = {}
    user_id = voice_server.ws.auth.extract_user_id(ws)
    assert user_id is None


def test_extract_user_id_local_mode(monkeypatch):
    monkeypatch.setenv("LOCAL_MODE", "true")
    from importlib import reload

    import voice_server.config
    reload(voice_server.config)
    import voice_server.ws.auth
    reload(voice_server.ws.auth)

    ws = MagicMock()
    ws.headers = {}
    user_id = voice_server.ws.auth.extract_user_id(ws)
    assert user_id == "local-dev-user"
