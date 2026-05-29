from unittest.mock import MagicMock, patch

from voice_server.ws.auth import extract_user_email


def test_extract_email_local_mode():
    ws = MagicMock()
    with patch("voice_server.ws.auth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(local_mode=True)
        result = extract_user_email(ws)
        assert result == "dev@localhost"


def test_extract_email_from_protocol_header():
    ws = MagicMock()
    ws.headers = {"sec-websocket-protocol": "v1.audio.intent, alice@example.com"}
    with patch("voice_server.ws.auth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(local_mode=False)
        result = extract_user_email(ws)
        assert result == "alice@example.com"


def test_extract_email_no_email_in_protocol():
    ws = MagicMock()
    ws.headers = {"sec-websocket-protocol": "v1.audio.intent"}
    with patch("voice_server.ws.auth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(local_mode=False)
        result = extract_user_email(ws)
        assert result == ""
