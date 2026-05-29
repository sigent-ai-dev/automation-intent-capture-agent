"""Unit tests for Sec-WebSocket-Protocol token extraction."""

from unittest.mock import MagicMock, patch

import pytest

from voice_server.ws.auth import extract_user_id


@pytest.fixture
def mock_websocket():
    ws = MagicMock()
    ws.headers = {}
    return ws


class TestExtractUserIdFromProtocol:
    def test_extracts_token_from_sec_websocket_protocol(self, mock_websocket):
        mock_websocket.headers = {
            "sec-websocket-protocol": "v1.audio.intent, eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test"
        }
        with patch("voice_server.ws.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(local_mode=False)
            with patch("voice_server.ws.auth.validate_token_sync") as mock_validate:
                mock_validate.return_value = "user-123"
                result = extract_user_id(mock_websocket)
                assert result == "user-123"
                mock_validate.assert_called_once_with(
                    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test"
                )

    def test_returns_none_when_no_protocol_header(self, mock_websocket):
        mock_websocket.headers = {}
        with patch("voice_server.ws.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(local_mode=False)
            result = extract_user_id(mock_websocket)
            assert result is None

    def test_returns_none_when_single_protocol_value(self, mock_websocket):
        mock_websocket.headers = {"sec-websocket-protocol": "v1.audio.intent"}
        with patch("voice_server.ws.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(local_mode=False)
            result = extract_user_id(mock_websocket)
            assert result is None

    def test_returns_none_when_first_value_not_expected_protocol(self, mock_websocket):
        mock_websocket.headers = {"sec-websocket-protocol": "unknown, some-token"}
        with patch("voice_server.ws.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(local_mode=False)
            result = extract_user_id(mock_websocket)
            assert result is None

    def test_returns_local_user_in_local_mode(self, mock_websocket):
        with patch("voice_server.ws.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(local_mode=True)
            result = extract_user_id(mock_websocket)
            assert result == "local-dev-user"

    def test_returns_none_when_token_validation_fails(self, mock_websocket):
        mock_websocket.headers = {
            "sec-websocket-protocol": "v1.audio.intent, invalid-token"
        }
        with patch("voice_server.ws.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(local_mode=False)
            with patch("voice_server.ws.auth.validate_token_sync") as mock_validate:
                mock_validate.return_value = None
                result = extract_user_id(mock_websocket)
                assert result is None
